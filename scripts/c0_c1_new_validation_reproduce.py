"""Recompute new-query embeddings and frozen C0/C1 without reading any qrels."""
import argparse
from pathlib import Path
import socket
from ax_research.heldout import read,write,sha,jsonl
from ax_research.functional_mapping import extract,compare
from ax_research.action_aggregation import purpose_filter
from ax_research.semantic_mapping import combined_score,ranking_key
from scripts.c0_c1_new_validation import ROOT,OUT,INPUT,verify


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();dest=a.output.resolve();dest.mkdir(parents=True,exist_ok=False)
    verify()
    def blocked(*args,**kwargs):raise RuntimeError('No network/API in replay')
    socket.socket.connect=blocked;socket.create_connection=blocked
    from scripts.heldout_run import predict
    cfg=read(ROOT/'configs/semantic_mapping_20261028.json');model=(ROOT/cfg['model_path']).resolve();qs=jsonl(INPUT)
    base=predict(qs,model,dest)
    details=read(dest/'evidence.json')['records'];by={(r['query_id'],r['case_id']):r for r in details}
    rules=read(ROOT/'configs/functional_mapping_20261028.json');policy=read(ROOT/'configs/action_aggregation_20261102.json');cp=read(ROOT/'docs/query-case-functional-mapping-2026-10-28/stage2/case_profiles.json')
    filtered={c:{role:purpose_filter(v,policy) for role,v in fields.items()} for c,fields in cp.items()};systems={'C0':base['systems']['C'],'C1':[],'C1_NO_EMBEDDING':[]}
    for q in qs:
        qid=q['query_id'];profile=purpose_filter(extract(q['text'],rules),policy)
        for name in ('C1','C1_NO_EMBEDDING'):
            values={}
            for c in base['case_ids']:
                strength=compare(profile,filtered[c])['mapping_grade'];s=by[qid,c]['semantic']['score']
                values[c]=combined_score(strength,s) if name=='C1' else strength/8+.25
            ranking=sorted(values,key=lambda c:(-values[c],-by[qid,c]['retrieval_tie'],c))
            systems[name].append({'query_id':qid,'ranking':ranking,**{f'top{k}':ranking[:k] for k in (5,10,20)},'scores':values})
    actual={'query_ids':base['query_ids'],'case_ids':base['case_ids'],'systems':systems,'scope':'NEW_VALIDATION_ORIGINAL_ONLY'}
    write(dest/'rankings.json',actual)
    expected=read(OUT/'predictions/rankings.json');assert actual==expected,'Reproduction score/ranking drift'
    verify()
    write(dest/'replay_receipt.json',{'all30_rankings_and3360_scores_equal':True,'rankings_sha256':sha(dest/'rankings.json'),'original_rankings_sha256':sha(OUT/'predictions/rankings.json'),'qrels_read':False,'fresh_query_embedding_encoding':True,'paid_API_calls':0,'question_sha256':sha(INPUT),'model_freeze_sha256':sha(OUT/'model_freeze.json')})
    print('Replay complete: fresh local embeddings, all30rankings/3360scores equal; no labels')


if __name__=='__main__':main()
