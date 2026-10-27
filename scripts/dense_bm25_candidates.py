"""Controlled local BM25 addition to frozen Dense paths; no LLM or encoder."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import socket
import subprocess
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from scripts import candidate_fusion_ablation as old
from ax_research.retrieval.bm25 import BM25Retriever

ROOT=Path(__file__).resolve().parents[1];CONFIG=ROOT/'configs/dense_bm25_candidates_20261027.json'
CFG=json.loads(CONFIG.read_text(encoding='utf-8-sig'));SOURCE=ROOT/CFG['source'];FUSION=ROOT/CFG['fusion_source'];OUT=ROOT/CFG['output']
CONDITIONS={
 'A':{'scope':'original','backbone':'single','channel':'dense'},
 'B':{'scope':'original','backbone':'three','channel':'dense'},
 'C':{'scope':'original','backbone':'single','channel':'hybrid','reference':'A'},
 'D':{'scope':'dynamic','backbone':'single','channel':'dense'},
 'E':{'scope':'dynamic','backbone':'three','channel':'dense'},
 'F':{'scope':'dynamic','backbone':'single','channel':'hybrid','reference':'D'},
 'S_C3':{'scope':'original','backbone':'three','channel':'hybrid','reference':'B'},
 'S_F3':{'scope':'dynamic','backbone':'three','channel':'hybrid','reference':'E'},
 'S_BM25_O':{'scope':'original','backbone':'single','channel':'bm25','reference':'A'},
 'S_BM25_M':{'scope':'dynamic','backbone':'single','channel':'bm25','reference':'D'}}
INPUTS=[SOURCE/n for n in ('stage1_silver.json','silver_freeze.json','stage2_results.json','stage3_results.json','embeddings.npz','environment.json','plan.json')]+[FUSION/n for n in ('results.json','preregistration.json')]+[ROOT/'data/v2_5/research'/n for n in ('dev_problem_views.csv','dev_queries.json','split_groups.csv')]+[ROOT/'src/ax_research/retrieval/bm25.py']

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprint(p):
    raw=p.read_bytes()
    if p==ROOT/'src/ax_research/retrieval/bm25.py':raw=raw.replace(b'\r\n',b'\n')
    return hashlib.sha256(raw).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(name,d):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jsonl(name,rows):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8') as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
def csv_save(name,rows):
    if rows:
        with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def prepare():
    inputs=[]
    for p in INPUTS:
        rel=p.relative_to(ROOT).as_posix();original=subprocess.check_output(['git','show',CFG['base_commit']+':'+rel],cwd=ROOT)
        current=p.read_bytes();source_code=p==ROOT/'src/ax_research/retrieval/bm25.py'
        if source_code:
            expected=subprocess.check_output(['git','rev-parse',CFG['base_commit']+':'+rel],cwd=ROOT,text=True).strip()
            filtered=subprocess.check_output(['git','hash-object','--path='+rel,str(p)],cwd=ROOT,text=True).strip()
            assert expected==filtered and original.replace(b'\r\n',b'\n')==current.replace(b'\r\n',b'\n'),'BM25 code changed'
        else:assert original==current,'Original changed: '+rel
        inputs.append({'path':rel,'sha256':fingerprint(p),'comparison':'Git-canonical source LF; original Windows CRLF is not a code change' if source_code else 'exact raw bytes'})
    d={'config':CFG,'config_sha256':digest(CFG),'conditions':CONDITIONS,'config_preregistration_commit':subprocess.check_output(['git','log','-1','--format=%H','--',str(CONFIG.relative_to(ROOT))],cwd=ROOT,text=True).strip(),'inputs':inputs,'api_calls':0,'key_reads':0,'embedding_inference':0,'stage4_access':False}
    p=OUT/'preregistration.json'
    if p.exists():assert read(p)==d,'Frozen inputs/config changed'
    save('preregistration.json',d);return d

def reciprocal(rank):return Fraction(1,60+rank)
def channel_fuse(dense_rank,bm25_rank):
    assert set(dense_rank)==set(bm25_rank) and len(set(dense_rank))==len(dense_rank)
    dr={c:i for i,c in enumerate(dense_rank,1)};br={c:i for i,c in enumerate(bm25_rank,1)}
    scores={c:(reciprocal(dr[c])+reciprocal(br[c]))/2 for c in dr}
    return sorted(scores,key=lambda c:(-scores[c],c)),scores
def mean_path_scores(paths):
    assert paths and all(set(p)==set(paths[0]) for p in paths)
    result={cid:sum((p[cid] for p in paths),Fraction(0))/len(paths) for cid in paths[0]}
    return sorted(result,key=lambda c:(-result[c],c)),result

def run():
    manifest=prepare();cases,labels,s2,s3,groups,details=old.load()
    assert old.CFG['relevance_threshold']==CFG['threshold'] and old.CFG['K']==CFG['K']
    with (ROOT/'data/v2_5/research/dev_queries.json').open(encoding='utf-8-sig') as f:queries={x['query_id']:x['query'] for x in json.load(f)['queries']}
    ids=sorted(cases);docs={cid:'\n'.join(f'[{k.upper()}] {cases[cid][k]}' for k in ('problem','task','context')) for cid in ids}
    bm=BM25Retriever(docs);assert bm._case_ids==ids
    bm_model=bm._bm25
    save('bm25_corpus_statistics.json',{'case_order':ids,'document_frequencies_by_case':dict(zip(ids,bm_model.doc_freqs)),'document_lengths_by_case':dict(zip(ids,bm_model.doc_len)),'idf':bm_model.idf,'average_document_length':bm_model.avgdl,'k1':bm_model.k1,'b':bm_model.b,'epsilon':bm_model.epsilon,'purpose':'Scalar independent BM25 score verification and token evidence, not query expansion or changed tokenizer.'})
    save('bm25_settings.json',{'implementation':'existing BM25Retriever/KiwiTokenizer/BM25Okapi','source_sha256':sha(ROOT/'src/ax_research/retrieval/bm25.py'),'versions':{n:importlib.metadata.version(n) for n in ('kiwipiepy','rank-bm25')},'k1':bm_model.k1,'b':bm_model.b,'epsilon':bm_model.epsilon,'average_document_length':bm_model.avgdl,'documents':112,'query_expansion':False,'case_prefixes':['[PROBLEM]','[TASK]','[CONTEXT]'],'tied_scores':'case_id_ascending, unchanged from old implementation'})
    path_registry={};dense_paths={};path_groups=defaultdict(list)
    originals={name:{r['qid']:r for r in rows} for name,rows in s2['systems'].items()}
    oscores={(x['system'],x['qid']):x['scores'] for x in s2['score_details'] if 'scores' in x}
    for q in sorted(queries):
        pid='o_'+q;path_registry[pid]={'path_id':pid,'scope':'original','qid':q,'repeat':0,'perspective_id':None,'original_query':queries[q],'query_text':queries[q]};path_groups[('original',q,0)].append(pid)
        for backbone,oname in [('single','A_single_dense'),('three','B_three_view_dense')]:dense_paths[(pid,backbone)]={'ranking':originals[oname][q]['ranking'],'scores':oscores[(oname,q)]}
        for rep in (1,2,3):
            key=('C_dynamic_single_dense',q,rep)
            for viewid,b in details[key].items():
                pid=f'p_{q}_r{rep}_{viewid}';path_registry[pid]={'path_id':pid,'scope':'dynamic','qid':q,'repeat':rep,'perspective_id':viewid,'original_query':queries[q],'query_text':b['branch_query'],'perspective':b['perspective']};path_groups[('dynamic',q,rep)].append(pid)
                for backbone,sname in [('single','C_dynamic_single_dense'),('three','D_dynamic_three_view_dense')]:
                    source=details[(sname,q,rep)][viewid];assert source['branch_query']==b['branch_query']
                    dense_paths[(pid,backbone)]={'ranking':source['full_ranking'],'scores':source['full_scores']}
    assert len(path_registry)==118 and len(dense_paths)==236
    sparse={};hybrid={};tie_stats=[];features=[];complement=[]
    for pid,meta in path_registry.items():
        found=bm.search(meta['query_text'],top_k=None);ranking=[x.case_id for x in found];scores={x.case_id:x.score for x in found};tokens=bm._tokenizer.tokenize(meta['query_text'])
        assert len(ranking)==112 and set(ranking)==set(ids)
        if meta['scope']=='original':assert ranking==originals['BM25_auxiliary'][meta['qid']]['ranking'],'Original BM25 replay mismatch'
        cnt=Counter(scores.values());sparse[pid]={'ranking':ranking,'scores':scores,'query_tokens':tokens}
        tie_stats.append({'path_id':pid,'qid':meta['qid'],'scope':meta['scope'],'distinct_score_count':len(cnt),'zero_score_cases':sum(s==0 for s in scores.values()),'positive_score_cases':sum(s>0 for s in scores.values()),'top20_zero_score_cases':sum(scores[c]==0 for c in ranking[:20]),'largest_tie_group':max(cnt.values()),'top_score':scores[ranking[0]],'token_count':len(tokens)})
        br={c:i for i,c in enumerate(ranking,1)}
        for backbone in ('single','three'):
            d=dense_paths[(pid,backbone)];hr,hs=channel_fuse(d['ranking'],ranking);hybrid[(pid,backbone)]={'ranking':hr,'scores':hs};dr={c:i for i,c in enumerate(d['ranking'],1)};hri={c:i for i,c in enumerate(hr,1)};m=len(path_groups[(meta['scope'],meta['qid'],meta['repeat'])])
            for cid in ids:
                doc_index=ids.index(cid);matched=sorted(set(tokens)&set(bm_model.doc_freqs[doc_index]))
                features.append({'path_id':pid,'qid':meta['qid'],'repeat':meta['repeat'],'scope':meta['scope'],'perspective_id':meta['perspective_id'],'backbone':backbone,'case_id':cid,'dense_rank':dr[cid],'dense_score':d['scores'][cid],'bm25_rank':br[cid],'bm25_score':scores[cid],'bm25_matched_tokens':matched,'hybrid_rank_within_path':hri[cid],'dense_weight':.5,'bm25_weight':.5,'dense_weighted_rrf_exact':str(reciprocal(dr[cid])/2),'bm25_weighted_rrf_exact':str(reciprocal(br[cid])/2),'hybrid_rrf_score':float(hs[cid]),'hybrid_rrf_exact':str(hs[cid]),'perspective_count':m,'normalized_final_hybrid_contribution':float(hs[cid]/m),'normalized_final_hybrid_contribution_exact':str(hs[cid]/m),'effective_dense_path_weight':float(Fraction(1,2*m)),'effective_bm25_path_weight':float(Fraction(1,2*m))})
            positive={c for c,g in labels[meta['qid']].items() if g>=3}
            for k in CFG['K']:
                dt=set(d['ranking'][:k])&positive;bt=set(ranking[:k])&positive
                complement.append({'scope':'per_search_path','path_id':pid,'qid':meta['qid'],'repeat':meta['repeat'],'backbone':backbone,'k':k,'dense_only_related':sorted(dt-bt),'bm25_only_related':sorted(bt-dt),'common_related':sorted(dt&bt),'dense_related_total':len(dt),'bm25_related_total':len(bt)})
    save('query_registry.json',{'paths':path_registry,'input_source':'original dev query and frozen108 generated perspectives only'})
    save('case_registry.json',{'cases':{cid:{k:cases[cid][k] for k in ('case_id','problem','task','context','evidence_ids','leakage_group_id')} for cid in ids},'labels_included':False})
    save('bm25_paths.json',{'paths':sparse,'all_original_rankings_reproduced':True})
    save('dense_paths.json',{'paths':[{'path_id':p,'backbone':b,**x} for (p,b),x in dense_paths.items()],'scores_copied_from_existing_artifacts':True,'new_embeddings':False})
    save('hybrid_paths.json',{'paths':[{'path_id':p,'backbone':b,'ranking':x['ranking'],'scores':{c:float(v) for c,v in x['scores'].items()},'scores_exact':{c:str(v) for c,v in x['scores'].items()}} for (p,b),x in hybrid.items()]})
    save('bm25_tie_diagnostics.json',{'paths':tie_stats,'note':'Full112 candidates used. Zero-score ranks are deterministic ID order, not positive lexical evidence; no tie correction was tuned.'})
    jsonl('candidate_features.jsonl',features)
    systems={};pools=[]
    prior=read(FUSION/'results.json')['systems']
    for condition,setting in CONDITIONS.items():
        rows=[]
        for q in sorted(queries):
            for rep in ((0,) if setting['scope']=='original' else (1,2,3)):
                paths=path_groups[(setting['scope'],q,rep)];parts=[]
                for pid in paths:
                    if setting['channel']=='hybrid':part=hybrid[(pid,setting['backbone'])]['scores']
                    else:
                        ranking=sparse[pid]['ranking'] if setting['channel']=='bm25' else dense_paths[(pid,setting['backbone'])]['ranking'];part={cid:reciprocal(i) for i,cid in enumerate(ranking,1)}
                    parts.append(part)
                ranking,score=mean_path_scores(parts)
                if condition in ('D','E'):
                    pn=('single_dense' if condition=='D' else 'three_view_dense')+'__mean_rrf';oldrow=next(x for x in prior[pn] if x['qid']==q and x['repeat']==rep);assert ranking==oldrow['ranking'],'Matched outer fusion changed'
                if condition in ('A','B'):assert ranking==originals['A_single_dense' if condition=='A' else 'B_three_view_dense'][q]['ranking']
                row={'qid':q,'repeat':rep,'path_ids':paths,'ranking':ranking,'scores':{cid:float(v) for cid,v in score.items()},'scores_exact':{cid:str(v) for cid,v in score.items()},'top_k':{str(k):ranking[:k] for k in CFG['K']},'metrics':{str(k):old.metrics(ranking,labels[q],k) for k in CFG['K']}}
                if 'reference' in setting:
                    base=next(r for r in systems[setting['reference']] if r['qid']==q and r['repeat']==rep);positive={cid for cid,g in labels[q].items() if g>=3};changes={}
                    for k in CFG['K']:
                        before=set(base['ranking'][:k])&positive;after=set(ranking[:k])&positive
                        changes[str(k)]={'new_related':sorted(after-before),'retained_related':sorted(before&after),'lost_related':sorted(before-after)}
                    row['reference']=setting['reference'];row['changes']=changes
                rows.append(row)
                if setting['channel']=='hybrid':pools.append({'condition':condition,'qid':q,'repeat':rep,'scope':setting['scope'],'backbone':setting['backbone'],'path_ids':paths,'candidate_ids_ranked_all112':ranking,'final_retrieval_score':row['scores'],'final_retrieval_score_exact':row['scores_exact'],'mapping_input_must_not_truncate_to_top20':True})
        systems[condition]=rows
    agg={n:old.aggregate(rs) for n,rs in systems.items()}
    for n in ('A','B','S_BM25_O'):
        oldname={'A':'A_single_dense','B':'B_three_view_dense','S_BM25_O':'BM25_auxiliary'}[n]
        for k in CFG['K']:
            for field in ('precision','recall','f1'):assert abs(agg[n][str(k)]['macro_'+field]-s2['aggregate'][oldname][str(k)]['macro_'+field])<1e-12
    save('results.json',{'config_sha256':digest(CFG),'conditions':CONDITIONS,'systems':systems,'aggregate':agg,'silver_sha256':sha(SOURCE/'stage1_silver.json'),'outer_fusion_control':'same mean across perspective rank-contribution scores; no original anchor or RR in treatment comparisons','api_calls':0,'new_dense_embeddings':0,'human_gold':False})
    jsonl('mapping_candidate_pools.jsonl',pools)
    save('channel_complementarity.json',{'records':complement,'labels_used_for_evaluation_only':True})
    macro=[];query_metrics=[];rank_changes=[]
    for n,rows in systems.items():
        for k,d in agg[n].items():macro.append({'condition':n,'k':k,**d})
        for row in rows:
            for k in CFG['K']:
                m=row['metrics'][str(k)];ch=row.get('changes',{}).get(str(k),{})
                query_metrics.append({'condition':n,'qid':row['qid'],'repeat':row['repeat'],'k':k,'precision':m['precision'],'recall':m['recall'],'f1':m['f1'],'true_positives':m['true_positives'],'precision_denominator':k,'recall_denominator':m['recall_denominator'],'matched_reference':row.get('reference',''),'new_related':len(ch['new_related']) if ch else '', 'retained_related':len(ch['retained_related']) if ch else '', 'lost_related':len(ch['lost_related']) if ch else ''})
            if row.get('reference'):
                base=next(x for x in systems[row['reference']] if x['qid']==row['qid'] and x['repeat']==row['repeat'])
                for cid in ids:rank_changes.append({'condition':n,'reference':row['reference'],'qid':row['qid'],'repeat':row['repeat'],'cid':cid,'silver_score':labels[row['qid']][cid],'old_rank':base['ranking'].index(cid)+1,'new_rank':row['ranking'].index(cid)+1,'rank_gain_positive_is_up':base['ranking'].index(cid)-row['ranking'].index(cid)})
    csv_save('macro_metrics.csv',macro);csv_save('query_run_metrics.csv',query_metrics);csv_save('case_rank_changes.csv',rank_changes)
    assert all(fingerprint(ROOT/x['path'])==x['sha256'] for x in manifest['inputs'])
    save('preservation.json',{'passed':True,'unchanged_inputs':manifest['inputs'],'api_calls':0,'api_key_reads':0,'embedding_inference':0,'stage4_access':False})
    print(json.dumps({'macro20':{n:z['20'] for n,z in agg.items()},'bm25_paths':len(sparse),'candidate_feature_rows':len(features),'handover_pools':len(pools)},ensure_ascii=False))

def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','run']);a=p.parse_args();connect=socket.socket.connect;create=socket.create_connection
    socket.socket.connect=old.no_network;socket.create_connection=old.no_network
    try:prepare() if a.phase=='prepare' else run()
    finally:socket.socket.connect=connect;socket.create_connection=create
if __name__=='__main__':main()
