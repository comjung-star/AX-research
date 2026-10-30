"""Independent scalar metric checks, source quote checks and replay hashes."""
import csv
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
import subprocess
from ax_research.heldout import read,sha,write

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/mapping-improvement-2026-10-30'


def main():
    ex=OUT/'experiment'; ev=ex/'evaluation';receipt=read(ex/'prediction_receipt.json')
    for name,h in receipt['artifact_sha256'].items():assert sha(ex/name)==h
    replay=ROOT.parent/'AX-mapping-replay-20261030'
    replay_equal={name:sha(replay/name)==h for name,h in receipt['artifact_sha256'].items()}
    assert all(replay_equal.values()),replay_equal
    profiles=read(ex/'profiles.json');quotes=0
    for group in (profiles['queries'],{c:p['task'] for c,p in profiles['cases'].items()}, {c:p['problem'] for c,p in profiles['cases'].items()}, {c:p['context'] for c,p in profiles['cases'].items()}):
        for p in group.values():
            for f in p['functions']:
                for key in ('action','object','clause'):
                    s=f[key];assert p['text'][s['start']:s['end']]==s['quote'];quotes+=1
                assert f['output_status']=='OPERATION_CATEGORY_ONLY_ACTUAL_OUTPUT_UNKNOWN'
    raw=read(ROOT/'docs/stage123-openai-triplicate-2026-10-27/stage1_silver.json')['records'];pos=defaultdict(set);grades={}
    for r in raw:
        grades[r['qid'],r['cid']]=r['silver_score']
        if r['silver_score']>=3:pos[r['qid']].add(r['cid'])
    systems=read(ex/'rankings.json')['systems'];systems['SingleDense_original']=read(ROOT/'docs/query-case-functional-mapping-2026-10-28/stage4_dev/results.json')['systems']['single_dense__original']
    expected={};runs=0
    for name,rs in systems.items():
        values=defaultdict(list)
        for r in rs:
            assert len(r['ranking'])==len(set(r['ranking']))==112;rset=set(r['ranking'])
            assert rset=={c for q,c in grades if q==r['qid']}
            for k in (5,10,20):
                h=sum(c in pos[r['qid']] for c in r['ranking'][:k]);n=len(pos[r['qid']]);q=r['qid']
                values[q,k,'precision'].append(Fraction(h,k))
                if n:
                    values[q,k,'recall'].append(Fraction(h,n));values[q,k,'f1'].append(Fraction(2*h,k+n))
            runs+=1
        for k in (5,10,20):
            for m in ('precision','recall','f1'):
                means=[sum(v,Fraction())/len(v) for (q,kk,mm),v in values.items() if kk==k and mm==m]
                expected[name,k,m]=sum(means,Fraction())/len(means)
    summary=read(ev/'results.json');checked=0
    for row in summary['macro']:
        for m in ('precision','recall','f1'):
            assert abs(row[m]-float(expected[row['system'],row['k'],m]))<1e-12;checked+=1
    changes=list(csv.DictReader((ev/'rank_changes.csv').open(encoding='utf-8')))
    counts=defaultdict(Counter)
    for r in changes:
        if not r['system'].endswith('D_SINGLE'):continue
        delta=int(r['rank_gain']);tag='up' if delta>0 else 'down' if delta<0 else 'same';grade=int(r['silver_grade'])
        category='related_ge3' if grade>=3 else 'grade0' if grade==0 else 'grade1_2'
        counts[r['system']][category+'_'+tag]+=1
    old_errors=read(ev/'old_error_analysis.json')['records'];flagcounts=Counter(f for r in old_errors if r['condition']=='D_SINGLE' for f in r['flags'])
    baseline_errors=[r for r in old_errors if r['condition']=='D_SINGLE' and r['silver_grade']==0 and r['A_rank']<=5]
    newids=read(ex/'recognition.json')['newly_recognized_unknown33']
    recognition_grades={cid:dict(Counter(str(v) for (q,c),v in grades.items() if c==cid)) for cid in newids}
    # All old algorithm/data files remain exactly unchanged against the chosen base.
    modified=subprocess.check_output(['git','diff','ba5308d1619e53ee8b1b6c223480a439f5adcf8b','--diff-filter=MDR','--name-only'],cwd=ROOT,text=True).splitlines()
    allowed=['configs/.gitattributes','scripts/.gitattributes','src/ax_research/.gitattributes','tests/.gitattributes']
    assert set(modified)<=set(allowed),modified
    result={'source_base':'ba5308d1619e53ee8b1b6c223480a439f5adcf8b','design_commit':'97e3af27','prediction_commit':'fa993183','rankings_checked':runs,'fraction_macro_metric_checks':checked,'literal_quote_checks':quotes,'replay_equal':replay_equal,'algorithm_settings_corpus_labels_demo_changed':False,'existing_metadata_only_changes':modified,'rank_movement_event_counts_D_SINGLE':dict(counts),'old_error_flag_counts_D_SINGLE':dict(flagcounts),'grade0_top5_A_D_examples':baseline_errors[:10],'newly_recognized_case_grade_distributions':recognition_grades,'unit':'rank changes count query-repeat-case; overlapping flags not bug counts; grade0 separate from grade1/2','paid_api_calls':0,'new_model_inference':0,'cost_usd':'0.00','independent_test_read':False,'post_result_tuning':False}
    write(OUT/'verification.json',result)
    print('Verified',runs,'rankings;',checked,'Fraction macro values;',quotes,'quotes; all6 replay hashes equal')


if __name__=='__main__':main()
