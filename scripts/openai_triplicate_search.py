"""Frozen DEV retrieval: existing BGE-M3 CLS, mean view fusion and round robin."""
import argparse
import hashlib
import os
import statistics
from collections import Counter
from itertools import combinations
import numpy as np
from scripts import openai_triplicate as run
from ax_research.retrieval.bm25 import BM25Retriever
from ax_research.selection import branch_balanced_unique

K_VALUES=(5,10,20)
def frozen_labels():
    f=run.OUT/'stage1_silver.json';freeze=run.read(run.OUT/'silver_freeze.json')
    assert hashlib.sha256(f.read_bytes()).hexdigest()==freeze['sha256']
    d=run.read(f);assert d['pairs']==1120 and d['received_scores']>=3192
    return {q:{r['cid']:r['silver_score'] for r in d['records'] if r['qid']==q} for q in run.inputs()[1]}

def metrics(ranking,grades,k,threshold=3):
    ids=ranking[:k];assert len(ids)==k and len(set(ids))==k
    positive={c for c,s in grades.items() if s is not None and s>=threshold};unknown={c for c,s in grades.items() if s is None}
    tp=len(set(ids)&positive);u=len(set(ids)&unknown);outside=len(unknown)-u;r=len(positive)
    # A conditional point value is deliberately NOT a full-corpus P/R/F1 when
    # unknown labels exist. Bounds vary unknowns consistently, never label0.
    complete=not unknown
    p=tp/k if complete else tp/(k-u) if k>u else None
    recall=tp/r if r else None
    f1=2*tp/(k+r) if complete and r else (2*p*recall/(p+recall) if p is not None and recall is not None and p+recall else 0 if p==0 and recall==0 else None)
    lower_r=tp/(r+outside) if r+outside else None
    upper_r=(tp+u)/(r+u) if r+u else None
    return {'k':k,'tp':tp,'precision':p,'recall':recall,'f1':f1,'point_scope':'complete_corpus' if complete else 'conditional_on_judged_items','precision_denominator':k if complete else k-u,'recall_denominator':r,'unknown_in_top_k':u,'unknown_total':len(unknown),'precision_lower':tp/k,'precision_upper':(tp+u)/k,'recall_lower':lower_r,'recall_upper':upper_r,'f1_lower':2*tp/(k+r+outside) if r+outside else None,'f1_upper':2*(tp+u)/(k+r+u) if r+u else None,'related_ids':sorted(set(ids)&positive)}

def aggregate(rows):
    out={}
    for k in K_VALUES:
        cells=[r['metrics'][str(k)] for r in rows];d={'query_count':len(cells),'tp_sum':sum(c['tp'] for c in cells),'precision_denominator_sum':sum(c['precision_denominator'] for c in cells),'recall_denominator_sum':sum(c['recall_denominator'] for c in cells),'unknown_in_top_k_sum':sum(c['unknown_in_top_k'] for c in cells)}
        for name in ('precision','recall','f1','precision_lower','precision_upper','recall_lower','recall_upper','f1_lower','f1_upper'):
            values=[c[name] for c in cells if c[name] is not None];d['macro_'+name]=statistics.mean(values) if values else None;d[name+'_query_denominator']=len(values)
        out[str(k)]=d
    return out

def encoder():
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(4);path=run.ROOT.parent/'AX-prototype/.local/models/bge-m3'
    pooling=run.read(path/'1_Pooling/config.json');assert pooling['pooling_mode_cls_token'] and not pooling['pooling_mode_mean_tokens']
    model=SentenceTransformer(str(path),device='cpu',local_files_only=True);model.max_seq_length=4096;assert model.get_sentence_embedding_dimension()==1024
    return model,path
def encode(model,texts):
    lengths=[len(model.tokenizer.encode(t)) for t in texts];assert max(lengths)<=4096
    vectors=model.encode(texts,batch_size=8,normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False).astype(np.float32)
    assert vectors.shape==(len(texts),1024) and np.isfinite(vectors).all()
    return vectors,lengths
def rank(ids,scores):return sorted(ids,key=lambda c:(-float(scores[ids.index(c)]),c))
def row(q,ranking,grades,**extra):return {'qid':q,'ranking':ranking,**extra,'metrics':{str(k):metrics(ranking,grades,k) for k in K_VALUES}}

def stage2():
    labels=frozen_labels();cs,qs=run.inputs();ids=sorted(cs);qids=sorted(qs)
    texts={'single':['\n'.join(f'[{f.upper()}] {cs[c][f]}' for f in ('problem','task','context')) for c in ids]}
    for f in ('problem','task','context'):texts[f]=[f'[{f.upper()}] {cs[c][f]}' for c in ids]
    model,path=encoder();mat={};lengths={}
    for name,txt in texts.items():mat[name],lengths[name]=encode(model,txt)
    qv,lengths['queries']=encode(model,[qs[q] for q in qids])
    bm=BM25Retriever(dict(zip(ids,texts['single'])))
    systems={'A_single_dense':[],'B_three_view_dense':[],'BM25_auxiliary':[]};sources=[]
    for q,vec in zip(qids,qv):
        scores={'A_single_dense':mat['single']@vec,'B_three_view_dense':sum(mat[f]@vec for f in ('problem','task','context'))/3}
        for name,s in scores.items():
            ranking=rank(ids,s);systems[name].append(row(q,ranking,labels[q]));sources.append({'qid':q,'system':name,'scores':dict(zip(ids,map(float,s)))})
        systems['BM25_auxiliary'].append(row(q,[v.case_id for v in bm.search(qs[q],top_k=None)],labels[q]))
        sources.append({'qid':q,'system':'B_view_details','views':{f:{'ranking':rank(ids,mat[f]@vec),'scores':dict(zip(ids,map(float,mat[f]@vec)))} for f in ('problem','task','context')}})
    np.savez_compressed(run.OUT/'embeddings.npz',case_ids=np.array(ids),query_ids=np.array(qids),queries=qv,**mat)
    out={'status':'STAGE2_COMPLETE_DEV_AI_SILVER','systems':systems,'aggregate':{k:aggregate(v) for k,v in systems.items()},'score_details':sources,'settings':run.read(run.OUT/'plan.json')['retrieval'],'token_lengths':lengths,'pooling':'CLS confirmed from existing config','local_model_config_sha256':hashlib.sha256((path/'config.json').read_bytes()).hexdigest(),'silver_sha256':run.read(run.OUT/'silver_freeze.json')['sha256'],'human_gold':False}
    run.save(run.OUT/'stage2_results.json',out);print(out['aggregate']);return out

def stage3():
    labels=frozen_labels();base=run.read(run.OUT/'stage2_results.json');cs,qs=run.inputs();cache=np.load(run.OUT/'embeddings.npz');ids=cache['case_ids'].tolist();model,_=encoder()
    methods={'C_dynamic_single_dense':[],'D_dynamic_three_view_dense':[]};views_log=[];diversity=[]
    baseline={name:{r['qid']:r['ranking'] for r in rows} for name,rows in base['systems'].items()}
    for q in sorted(qs):
        for rep in (1,2,3):
            result=run.read(run.OUT/'results'/f'stage3_{q}_r{rep}.json');assert result['validation']['valid']
            ps=result['validation']['data']['perspectives'];texts=[p['title']+'\n'+p['description'] for p in ps]
            vectors,lengths=encode(model,texts);branch={name:{} for name in methods}
            for p,vec,txt,n in zip(ps,vectors,texts,lengths):
                scores={'C_dynamic_single_dense':cache['single']@vec,'D_dynamic_three_view_dense':sum(cache[f]@vec for f in ('problem','task','context'))/3}
                for name,s in scores.items():
                    ranking=rank(ids,s);branch[name][p['id']]=ranking
                    views_log.append({'qid':q,'repeat':rep,'system':name,'perspective':p,'branch_query':txt,'input_tokens':n,'full_ranking':ranking,'full_scores':dict(zip(ids,map(float,s)))})
            sims=[float(vectors[a]@vectors[b]) for a,b in combinations(range(len(ps)),2)]
            diversity.append({'qid':q,'repeat':rep,'perspectives':len(ps),'mean_pair_cosine':statistics.mean(sims),'keywords':[p['keywords'] for p in ps],'interpretation':'Perspective semantic variety, not retrieval effectiveness.'})
            for name,branches in branch.items():
                selected=branch_balanced_unique(branches,20);ranking=[c for _,c in selected];assert len(set(ranking))==20
                parent='A_single_dense' if name.startswith('C_') else 'B_three_view_dense';original=baseline[parent][q];positive={c for c,s in labels[q].items() if s is not None and s>=3}
                changes={str(k):{'new_related':sorted((set(ranking[:k])-set(original[:k]))&positive),'lost_related':sorted((set(original[:k])-set(ranking[:k]))&positive),'retained_related':sorted(set(original[:k])&set(ranking[:k])&positive),'recommendation_jaccard':len(set(original[:k])&set(ranking[:k]))/len(set(original[:k])|set(ranking[:k]))} for k in K_VALUES}
                methods[name].append(row(q,ranking,labels[q],repeat=rep,selected_with_branch=selected,related_changes=changes))
    # Average repeats inside each original query, then macro over10 queries.
    per_query={};macro={}
    for name,rows in methods.items():
        per_query[name]=[]
        for q in sorted(qs):
            rs=[r for r in rows if r['qid']==q];cell={}
            for k in K_VALUES:
                cell[str(k)]={}
                for field in ('precision','recall','f1'):
                    values=[r['metrics'][str(k)][field] for r in rs if r['metrics'][str(k)][field] is not None]
                    cell[str(k)][field+'_mean']=statistics.mean(values) if values else None
                    cell[str(k)][field+'_stdev']=statistics.stdev(values) if len(values)>1 else None
            per_query[name].append({'qid':q,'repeats':3,'metrics':cell})
        # Equal3 repetitions per query: raw average equals nested average; save
        # both the30-row aggregate and explicit10-query denominator.
        macro[name]=aggregate(rows)
        for d in macro[name].values():
            d['generation_runs']=30;d['original_queries']=10;d['aggregation']='3 repeats within each query, then10-query macro';d['query_count']=10
            for key in list(d):
                if key.endswith('_query_denominator'):
                    d[key.replace('_query_denominator','_generation_run_denominator')]=d[key];d[key]=d[key]//3
    out={'status':'STAGE3_COMPLETE_DEV_OPENAI_ONLY','baseline_once':{n:base['aggregate'][n] for n in ('A_single_dense','B_three_view_dense')},'systems':methods,'aggregate':macro,'query_repeat_means':per_query,'branches':views_log,'perspective_diversity':diversity,'generation_requests':30,'deterministic_baseline_repetitions':1,'silver_sha256':base['silver_sha256'],'human_gold':False,'reference_coverage':'Not reported; references unvalidated'}
    run.save(run.OUT/'stage3_results.json',out);print(macro);return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['stage2','stage3']);a=p.parse_args();stage2() if a.phase=='stage2' else stage3()
