"""Offline evaluator comparison. No key lookup, API, or retrieval execution."""
from collections import Counter
from decimal import Decimal
from statistics import mean
import argparse

from ax_research.heldout import read, write, sha
from scripts import evaluator_abc as run
from scripts import core_preservation_evaluate as metrics
from scripts import autonomous_ax_analyze as uncertainty


def control_pass(item, row):
    return row['status'] != 'UNJUDGED' and (
        row['grade'] is None if item['expected_abstain'] else row['grade'] in item['expected'])


def dangerous(item, row):
    g = row['grade']
    return ((item['expected_abstain'] and g == 0) or
            (not item['expected_abstain'] and max(item['expected']) < 2 and g is not None and g >= 2))


def compare_controls():
    items = read(run.OUT/'benchmark.json')['records']
    rows = [{**r, 'provider':p} for p in run.CAPS
            for r in read(run.OUT/p/'benchmark_results.json')['records']]
    checks = [{**r, 'split':i['split'], 'kind':i['kind'],
               'expected':i['expected'], 'expected_abstain':i['expected_abstain'],
               'policy_pass':control_pass(i,r), 'dangerous_error':dangerous(i,r)}
              for i in items for r in rows if r['id']==i['id']]
    summaries=[]
    for split in ('REPRODUCTION','FRESH_VALIDATION'):
        for method in 'ABC':
            subset=[r for r in checks if r['split']==split and r['method']==method]
            pairs=[[r for r in subset if r['id']==i['id']] for i in items if i['split']==split]
            judged=[p for p in pairs if all(r['grade'] is not None for r in p)]
            summaries.append({'split':split,'method':method,'n':len(subset),
                'policy_pass':sum(r['policy_pass'] for r in subset),
                'dangerous_errors':sum(r['dangerous_error'] for r in subset),
                'output_evidence_failures':sum(r['status']=='UNJUDGED' for r in subset),
                'abstain':sum(r['status']=='ABSTAIN' for r in subset),
                'grade_agreements':sum(p[0]['grade']==p[1]['grade'] for p in judged),
                'binary_agreements':sum((p[0]['grade']>=2)==(p[1]['grade']>=2) for p in judged),
                'both_judged_pairs':len(judged),
                'failures':dict(Counter(r.get('failure') for r in subset if r.get('failure'))),
                'by_provider':{p:{'pass':sum(r['policy_pass'] for r in subset if r['provider']==p),
                                    'n':sum(r['provider']==p for r in subset)} for p in run.CAPS}})
    write(run.OUT/'benchmark_analysis.json',{'records':checks,'summary':summaries,
        'expectations_not_human_gold':True,'agreement_denominator':'Both providers have a non-null grade; ABSTAIN agreement not counted as grade accuracy.'})
    candidates=[r for r in summaries if r['split']=='FRESH_VALIDATION']
    for r in candidates:
        costs=[read(p).get('cost_usd','0') for provider in run.CAPS
               for p in (run.OUT/provider/'api').glob('*judge_'+r['method']+'_N*_receipt.json')]
        r['decision_cost_usd']=str(sum(map(Decimal,costs),Decimal()))
    def key(r):
        return (r['dangerous_errors'],-r['policy_pass'],r['output_evidence_failures'],
                -r['grade_agreements'],-r['binary_agreements'],Decimal(r['decision_cost_usd']),r['method'])
    choice=min(candidates,key=key)
    write(run.OUT/'method_selection.json',{'method':choice['method'],'candidates':candidates,
        'choice_rule':'Frozen lexicographic safety, adherence, failures, agreement, cost, ID.',
        'selected_only_for_pending_diagnostic_review':True,
        'policy_gate_passed':choice['policy_pass']==choice['n'] and choice['output_evidence_failures']==0,
        'no_relevance_or_retrieval_prompt_changes_after_controls':True,
        'not_a_verified_evaluator':True,'human_approved':False})
    print('Selection',choice['method'], 'fresh pass',choice['policy_pass'],'/',choice['n'])
    print([{k:r[k] for k in ('method','policy_pass','dangerous_errors','output_evidence_failures','both_judged_pairs')} for r in candidates])


def pending_labels():
    previous=read(run.VALIDATION/'v2_reviewed_strict/labels.json')['records']
    items=read(run.OUT/'pending_items.json')['records']
    reviews={p:{r['id']:r for r in read(run.OUT/p/'pending_results.json')['records']} for p in run.CAPS}
    records=[];proposals={}
    for item in items:
        pair=[reviews[p][item['id']] for p in run.CAPS]
        if any(r['status']=='UNJUDGED' for r in pair):category='TECHNICAL_OR_EVIDENCE_FAILURE'
        elif all(r['grade'] is not None for r in pair):
            category='EXACT_GRADE_AGREEMENT' if pair[0]['grade']==pair[1]['grade'] else 'GRADE_DISAGREEMENT'
        else:category='SEMANTIC_ABSTAIN'
        grade=pair[0]['grade'] if category=='EXACT_GRADE_AGREEMENT' else None
        if grade is not None:proposals[item['query_id'],item['case_id']]=grade
        records.append({**item,'reviews':{p:reviews[p][item['id']] for p in run.CAPS},
            'category':category,'provisional_grade':grade,'human_approved':False,
            'source':read(run.VALIDATION/'source_registry.json')[item['case_id']]})
    candidate=[]
    for old in previous:
        key=old['query_id'],old['case_id']
        if key not in proposals:candidate.append(dict(old));continue
        candidate.append({**old,'grade':proposals[key],'status':'JUDGED',
            'previous':old,'label_source':'AI-Silver provisional diagnostic',
            'rationale':'두 제공자의 독립 요청에서 등급이 일치했습니다. 정책 검증을 통과하지 않아 진단용이며 승인된 정답은 아닙니다.',
            'released_for_tuning':False})
    write(run.OUT/'pending75_review.json',{'records':records,'counts':dict(Counter(r['category'] for r in records)),
        'agreement_proposals':len(proposals),'human_approved':0,'approved_resolutions':0,
        'all_prior75_remain_unreleased':True})
    write(run.OUT/'labels_provisional_diagnostic.json',{'records':candidate,'released_for_tuning':False,
        'human_approved':False,'not_verification_complete':True})
    write(run.OUT/'labels_primary_unchanged.json',{'records':previous,'new_approved_changes':0})
    with (run.OUT/'expert_review_packet.jsonl').open('x',encoding='utf-8',newline='\n') as stream:
        import json
        for r in records:
            # The review packet intentionally hides AI scores and retrieval ranks.
            stream.write(json.dumps({k:r[k] for k in ('id','query_id','case_id','text','case','source')},ensure_ascii=False)+'\n')
    return previous,candidate,records


def evaluate_versions():
    previous,candidate,reviews=pending_labels()
    prediction=read(run.ROOT/'docs/core-preserved-three-views-2026-11-07/predictions.json')
    original=read(run.ROOT/'docs/core-preserved-three-views-2026-11-07/labels.json')['records']
    versions={'original':original,'primary_unchanged':previous,'provisional_diagnostic':candidate}
    all_metrics={}
    for name,labels in versions.items():
        rows,macro,leaveout=metrics.evaluate(prediction,labels)
        all_metrics[name]={'per_query':rows,'macro':macro,'leave_one_out':leaveout,
            'bootstrap':metrics.bootstrap(rows,macro),'counts':dict(Counter(r['status'] for r in labels)),
            'not_model_improvement':'Only label versions change. Same sealed predictions are reused.'}
    write(run.OUT/'evaluation_versions.json',all_metrics)
    write(run.OUT/'F1_uncertainty.json',{'primary':metrics.incomplete_f1_bounds(prediction,previous),
        'diagnostic':metrics.incomplete_f1_bounds(prediction,candidate)})
    write(run.OUT/'label_scenarios.json',uncertainty.label_scenarios(prediction,candidate,count=4096))
    write(run.OUT/'nDCG_outer_bounds.json',uncertainty.ndcg_outer_bounds(prediction,candidate))
    write(run.OUT/'ranking_diagnostics.json',metrics.diagnostics(prediction,candidate))
    protocol=read(run.OUT/'protocol.json')
    checks=[{'path':p,'expected':h,'actual':sha(run.ROOT/p),'unchanged':sha(run.ROOT/p)==h}
            for p,h in protocol['protected_sha256'].items()]
    write(run.OUT/'preservation_check.json',{'files':checks,'all_unchanged':all(r['unchanged'] for r in checks),
        'prompt_unchanged':sha(run.ROOT/'scripts/evaluator_abc_prompts.py')==protocol['prompt_file_sha256']})
    write(run.OUT/'cost_summary.json',run.aggregate_cost())
    print('Pending categories',dict(Counter(r['category'] for r in reviews)))
    print('Cost',run.aggregate_cost()['estimated_usd'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['controls','final'])
    args=parser.parse_args();(compare_controls if args.stage=='controls' else evaluate_versions)()
