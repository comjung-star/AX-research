"""Frozen C0/C1 multiview adapter. infer never reads relevance judgments."""
import argparse
from collections import defaultdict
from fractions import Fraction
import json
from pathlib import Path
import socket
import sys
from ax_research.heldout import read, write, sha, jsonl
from ax_research.functional_mapping import extract, compare
from ax_research.action_aggregation import purpose_filter, compose
from scripts.validation123_api import OUT, OLD, ROOT, validate


def hybrid(dr, br):
    return (Fraction(1, 60+dr)+Fraction(1, 60+br))/2


def mean_tie(paths):
    if not paths: raise ValueError('Empty paths')
    return sum(paths, Fraction())/len(paths)


def load_views():
    qs=jsonl(OLD/'input/questions.jsonl'); paths=[]; sources={}
    for rep in (1,2,3):
        for q in qs:
            qid=q['query_id']; name=f'views_{qid}_r{rep}'
            # The one invalid received response is retained, never edited/reused.
            if qid=='NV20261102_08' and rep==2:name+='_quote_retry'
            p=OUT/'api/results'/(name+'.json');r=read(p);validate('views',qid,r['data']);sources[p.relative_to(ROOT).as_posix()]=sha(p)
            for i,v in enumerate(r['data']['perspectives'],1):
                paths.append({'query_id':f'p_{qid}_r{rep}_{i}','text':v['title']+'\n'+v['description'],'parent_query_id':qid,'repeat':rep,'perspective':v,'source_result':p.relative_to(ROOT).as_posix()})
    return paths,sources


def infer(scratch,model,dest=None):
    dest=dest or OUT/'stage3/predictions';dest.mkdir(parents=True,exist_ok=False);scratch.mkdir(exist_ok=False)
    paths,sources=load_views();write(dest/'paths.json',{'paths':paths,'api_results_sha256':sources})
    from scripts.heldout_run import freeze,predict
    state=freeze(model);state['adapter_sha256']=sha(Path(__file__));state['views']=sources
    state['C1_policy_sha256']=sha(ROOT/'configs/action_aggregation_20261102.json')
    state['C1_core_sha256']=sha(ROOT/'src/ax_research/action_aggregation.py')
    write(dest/'freeze.json',state)
    # Both socket and file-open guards are installed before inference. No qrels.
    accesses=set()
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes)):
            p=str(args[0]).replace('\\','/').lower()
            if any(s in p for s in ('qrels','stage1_silver','human_review','work-b','work_b','heldout-data')):
                raise RuntimeError('Label/sealed-data read denied during inference')
            if p.endswith(('.json','.jsonl','.npz','.py','.safetensors')):accesses.add(str(args[0]))
    sys.addaudithook(audit)
    def blocked(*a,**k):raise RuntimeError('No network in inference')
    socket.socket.connect=blocked;socket.create_connection=blocked
    raw=predict(paths,model,scratch)
    evidence=read(scratch/'evidence.json');by={(r['query_id'],r['case_id']):r for r in evidence['records']}
    originals=read(OLD/'predictions/rankings.json');oe=read(OLD/'predictions/evidence.json');ob={(r['query_id'],r['case_id']):r for r in oe['records']}
    c1old=read(OLD/'predictions/C1_details.json');c1by={(r['query_id'],r['case_id']):r for r in c1old['records']}
    rules=read(ROOT/'configs/functional_mapping_20261028.json');cfg=read(ROOT/'configs/action_aggregation_20261102.json')
    cps=read(ROOT/'docs/query-case-functional-mapping-2026-10-28/stage2/case_profiles.json')
    filtered={c:{role:purpose_filter(p,cfg) for role,p in roles.items()} for c,roles in cps.items()}
    profiles={p['query_id']:purpose_filter(extract(p['text'],rules),cfg) for p in paths}
    c1maps={(p['query_id'],c):compare(profiles[p['query_id']],filtered[c]) for p in paths for c in raw['case_ids']}
    write(dest/'query_profiles.json',{'semantic':evidence['query_profiles'],'C0_rule':evidence['rule_profiles'],'C1_rule':profiles,'C1_cases':filtered})
    rawr={r['query_id']:r for r in raw['systems']['C']};ties={};branch_systems={'C0':raw['systems']['C'],'C1':[]}
    with (dest/'branch_scores.jsonl').open('x',encoding='utf-8',newline='\n') as f:
        for p in paths:
            pid=p['query_id'];rs=[by[pid,c] for c in raw['case_ids']]
            dr=sorted(rs,key=lambda r:(-r['dense'],r['case_id']));br=sorted(rs,key=lambda r:(-r['bm25'],r['case_id']))
            dn={r['case_id']:i for i,r in enumerate(dr,1)};bn={r['case_id']:i for i,r in enumerate(br,1)}
            scores={}
            for c in raw['case_ids']:
                e=by[pid,c];t=hybrid(dn[c],bn[c]);assert float(t)==e['retrieval_tie'];ties[pid,c]=t
                m=c1maps[pid,c];s=.5*m['mapping_grade']/4+.5*(e['semantic']['score']+1)/2;scores[c]=s
                rec={'path_id':pid,'case_id':c,'dense':e['dense'],'dense_rank':dn[c],'bm25':e['bm25'],'bm25_rank':bn[c],'hybrid_exact':str(t),'C0_rule':e['rule'],'C1_rule':m,'semantic':e['semantic'],'C0_score':e['combined'],'C1_score':s,'case_source':'docs/dense-bm25-candidates-2026-10-27/case_registry.json'}
                f.write(json.dumps(rec,ensure_ascii=False,separators=(',',':'))+'\n')
            rank=sorted(scores,key=lambda c:(-scores[c],-ties[pid,c],c))
            branch_systems['C1'].append({'query_id':pid,'ranking':rank,'scores':scores,**{f'top{k}':rank[:k] for k in (5,10,20)}})
    write(dest/'branch_rankings.json',{'systems':branch_systems,'case_ids':raw['case_ids'],'path_count':len(paths)})
    grouped=defaultdict(list)
    for p in paths:grouped[p['parent_query_id'],p['repeat']].append(p['query_id'])
    systems={'E1':originals['systems']['C0'],'E3':originals['systems']['C1'],'E3_NEUTRAL':originals['systems']['C1_NO_EMBEDDING'],'E2':[],'E4':[],'E4_NEUTRAL':[]}
    with (dest/'combined_scores.jsonl').open('x',encoding='utf-8',newline='\n') as f:
        for (qid,rep),pids in grouped.items():
            vals={name:{} for name in ('E2','E4','E4_NEUTRAL')};ts={}
            for c in raw['case_ids']:
                whole=ob[qid,c];bs={p:by[p,c]['semantic']['score'] for p in pids};ts[c]=mean_tie([ties[p,c] for p in pids]);records={}
                for name in vals:
                    old=name=='E2';wg=whole['rule']['mapping_grade'] if old else c1by[qid,c]['new_rule']['mapping_grade']
                    grades={p:(by[p,c]['rule']['mapping_grade'] if old else c1maps[p,c]['mapping_grade']) for p in pids}
                    r=compose(wg,grades,whole['semantic']['score'],bs,no_embedding=name=='E4_NEUTRAL')
                    vals[name][c]=r['score'];records[name]=r
                f.write(json.dumps({'query_id':qid,'repeat':rep,'case_id':c,'tie_exact':str(ts[c]),'conditions':records},ensure_ascii=False,separators=(',',':'))+'\n')
            for name,values in vals.items():
                rank=sorted(values,key=lambda c:(-values[c],-ts[c],c));systems[name].append({'query_id':qid,'repeat':rep,'ranking':rank,'scores':values,**{f'top{k}':rank[:k] for k in (5,10,20)}})
    write(dest/'rankings.json',{'systems':systems,'case_ids':raw['case_ids'],'query_ids':originals['query_ids'],'repeats':[1,2,3]})
    import shutil
    shutil.copyfile(scratch/'new_query_vectors.npz',dest/'branch_vectors.npz')
    after=freeze(model);before={k:v for k,v in state.items() if k not in ('adapter_sha256','views','C1_policy_sha256','C1_core_sha256')}
    # Git metadata may advance while another local reporting unit is committed.
    # File/model/config/package hashes must still be exactly identical.
    assert {k:v for k,v in after.items() if k!='commit'}=={k:v for k,v in before.items() if k!='commit'}
    assert sha(ROOT/'configs/action_aggregation_20261102.json')==state['C1_policy_sha256']
    assert sha(ROOT/'src/ax_research/action_aggregation.py')==state['C1_core_sha256']
    write(dest/'post_freeze.json',after)
    write(dest/'access_audit.json',{'qrels_read':False,'sealed_test_read':False,'blocked_label_substrings':['qrels','stage1_silver','human_review','work-b','work_b','heldout-data'],'files_opened':sorted(accesses),'network_disabled':True})
    write(dest/'complete.json',{'complete':True,'path_count':len(paths),'all_case_count':112,'all_rounds':3,'files':{p.name:sha(p) for p in dest.iterdir()},'labels_read':False,'scratch':str(scratch)})
    print('Multiview prediction complete',len(paths),'paths',flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--scratch',type=Path,required=True);a.add_argument('--model',type=Path,required=True);a.add_argument('--output',type=Path);p=a.parse_args();infer(p.scratch.resolve(),p.model.resolve(),p.output.resolve() if p.output else None)
