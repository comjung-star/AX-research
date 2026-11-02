"""Independent arithmetic, literal-source, aggregation and replay checks."""
from collections import defaultdict,Counter
import argparse
from decimal import Decimal,localcontext
from fractions import Fraction
from pathlib import Path
import subprocess
from ax_research.heldout import read,sha,write

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/action-disambiguation-aggregation-2026-11-02';EX=OUT/'experiment'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-receipt',type=Path,default=OUT/'verification.json');args=parser.parse_args()
    receipt=read(EX/'prediction_receipt.json');replay=ROOT.parent/'AX-action-aggregation-replay-20261102'
    same={n:sha(EX/n)==h and sha(replay/n)==h for n,h in receipt['files'].items()};assert all(same.values())
    complete=read(EX/'evaluation/complete.json')
    for n,h in complete['files'].items():assert sha(EX/'evaluation'/n)==h
    profiles=read(EX/'profiles.json');quotes=0;held=Counter()
    groups=[(profiles['queries_before'],profiles['queries_after'])]
    for role in ('task','problem','context'):groups.append(({c:p[role] for c,p in profiles['cases_before'].items()},{c:p[role] for c,p in profiles['cases_after'].items()}))
    for old,new in groups:
        for p,x in new.items():
            assert x['text']==old[p]['text'] and set(x['function_ids'])<=set(old[p]['function_ids'])
            for f in x['functions']:
                for role in ('action','object','clause'):
                    s=f[role];assert x['text'][s['start']:s['end']]==s['quote'];quotes+=1
                assert f['actual_output_status']=='UNKNOWN_UNLESS_SEPARATELY_LITERAL'
            for s in x['purpose_audit']['validation_cues']+x['purpose_audit']['purpose_spans']+x['purpose_audit']['input_spans']:
                assert x['text'][s['start']:s['end']]==s['quote'];quotes+=1
            held.update(h['reason'] for h in x['purpose_audit']['held'])
    # Independently reconstruct all component arithmetic, including three-way set gate.
    checked=0;gatechecks=0;score=read(EX/'scores.json')['records']
    for r in score:
        q0=r['original_path'];c=r['case_id']
        for mode in ('C0','C1','C2','C3','C1_NO_EMBEDDING','C3_NO_EMBEDDING'):
            filtered=mode in ('C1','C3','C1_NO_EMBEDDING','C3_NO_EMBEDDING');gated=mode in ('C2','C3','C3_NO_EMBEDDING')
            qp=profiles['queries_after' if filtered else 'queries_before'];cp=profiles['cases_after' if filtered else 'cases_before'];bg=r['branch_rule_after' if filtered else 'branch_rule_before'];g0=r['original_rule_after' if filtered else 'original_rule_before']
            allowed={p:sorted(set(qp[q0]['function_ids'])&set(qp[p]['function_ids'])&set(cp[c]['task']['function_ids'])) for p in bg}
            selected=[p for p in bg if not gated or allowed[p]]
            v=r['variants'][mode];assert v['allowed_paths']==selected
            if gated:assert (r['allowed_after'] if filtered else r['allowed_before'])=={p:allowed[p] for p in bg if allowed[p]};gatechecks+=1
            rr=max([g0]+[bg[p] for p in selected]);bb=(r['original_semantic']+max(r['branch_semantic'][p] for p in selected))/2 if selected else r['original_semantic']
            value=rr/8+(.25 if mode.endswith('NO_EMBEDDING') else (bb+1)/4)
            assert abs(v['score']-value)<1e-15;checked+=1
    label=read(ROOT/'docs/stage123-openai-triplicate-2026-10-27/stage1_silver.json')['records'];grades=defaultdict(dict)
    for r in label:grades[r['qid']][r['cid']]=r['silver_score']
    systems=read(EX/'rankings.json')['systems'];expect={};ndexpect={};rankchecks=0;Ochecks=0
    scoreindex={(x['condition'],x['qid'],x['repeat'],x['case_id']):x for x in score}
    for name,runs in systems.items():
        buckets=defaultdict(list);nb=defaultdict(list)
        for r in runs:
            q=r['qid'];g=grades[q];pos={c for c,v in g.items() if v>=3};n=len(pos);rank=r['ranking'];assert len(rank)==len(set(rank))==112 and set(rank)==set(g);rankchecks+=1
            scope=next(s for s in ('O_SINGLE','D_SINGLE','O_THREE','D_THREE') if name.endswith('_'+s));method=name[:-(len(scope)+1)]
            def rankkey(c):
                item=scoreindex[scope,q,r['repeat'],c]
                assert r['scores'][c]==item['variants'][method]['score']
                return -item['variants'][method]['score'],-item['retrieval_tie'],c
            assert rank==sorted(g,key=rankkey)
            for k in (5,10,20):
                h=sum(c in pos for c in rank[:k]);buckets[q,k,'precision'].append(Fraction(h,k))
                if n:buckets[q,k,'recall'].append(Fraction(h,n));buckets[q,k,'f1'].append(Fraction(2*h,k+n))
                if k in (5,10):
                    with localcontext() as ctx:
                        ctx.prec=45
                        dcg=lambda seq:sum((Decimal(2)**v-1)/(Decimal(i+2).ln()/Decimal(2).ln()) for i,v in enumerate(seq))
                        den=dcg(sorted(g.values(),reverse=True)[:k]);value=dcg([g[c] for c in rank[:k]])/den if den else None
                        if value is not None:nb[q,k].append(float(value))
        for k in (5,10,20):
            for m in ('precision','recall','f1'):
                vals=[sum(v,Fraction())/len(v) for (q,kk,mm),v in buckets.items() if kk==k and mm==m];expect[name,k,m]=sum(vals,Fraction())/len(vals)
            if k in (5,10):
                vals=[sum(v)/len(v) for (q,kk),v in nb.items() if kk==k];ndexpect[name,k]=sum(vals)/len(vals) if vals else None
    for suf in ('O_SINGLE','O_THREE'):
        for left,right in [('C0','C2'),('C1','C3')]:
            for a,b in zip(systems[left+'_'+suf],systems[right+'_'+suf]):assert a['ranking']==b['ranking'] and a['scores']==b['scores'];Ochecks+=1
    num=0;ndnum=0
    for r in read(EX/'evaluation/results.json')['macro']:
        for m in ('precision','recall','f1'):assert abs(r[m]-float(expect[r['system'],r['k'],m]))<1e-12;num+=1
        if r['k'] in (5,10):assert abs(r['ndcg']-ndexpect[r['system'],r['k']])<1e-12;ndnum+=1
    oldsource=read(OUT/'audit/type_analysis.json')['records'];cohort=[r for r in oldsource if r['condition']=='D_SINGLE' and 'READING_VS_VALIDATION_RULE_CONFLATION' in r['types']]
    before=after=0
    for r in cohort:
        cid=r['case_id'];oldcase=set(profiles['cases_before'][cid]['task']['function_ids']);newcase=set(profiles['cases_after'][cid]['task']['function_ids'])
        before+=any('validate_record' in (set(profiles['queries_before'][p['path_id']]['function_ids'])&oldcase) for p in r['branches'])
        after+=any('validate_record' in (set(profiles['queries_after'][p['path_id']]['function_ids'])&newcase) for p in r['branches'])
    modified=subprocess.check_output(['git','diff','024d73e87795a1b615e8b1d9f37f64ba2386b3bd','--diff-filter=MDR','--name-only'],cwd=ROOT,text=True).splitlines();assert set(modified)<={'scripts/.gitattributes','configs/.gitattributes','tests/.gitattributes','src/ax_research/.gitattributes'}
    write(args.output_receipt,{'replay_hash_matches':same,'final_rankings_checked':rankchecks,'independent_full_score_join_and_rank_orders':rankchecks,'component_scores_checked':checked,'gate_set_checks':gatechecks,'fraction_macro_checks':num,'decimal_ndcg_macro_checks':ndnum,'literal_source_quote_checks':quotes,'O_score_and_rank_invariants':Ochecks,'profile_held_counts_all_roles':dict(held),'source_supported_reading_validation_cohort_D_SINGLE':{'before_shared_validate':before,'after_shared_validate':after,'unit':'query-repeat-case, user-mentioned type plus all matching cases; not humanGold counts'},'existing_changes_only_metadata':modified,'old_models_data_labels_demo_modified':False,'test_access':False,'new_embeddings':0,'api_calls':0,'cost_usd':'0.00','post_result_tuning':False})
    print('Verified',rankchecks,'rankings',checked,'scores',num,'Fraction metrics',ndnum,'Decimal nDCG; quote checks',quotes,'cohort',before,'->',after)


if __name__=='__main__':main()
