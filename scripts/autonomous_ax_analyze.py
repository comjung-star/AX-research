"""Reliability audit and feasible label scenarios, never model tuning."""
from collections import Counter
from decimal import Decimal
from statistics import mean

import numpy as np

from ax_research.heldout import read, write, sha
from scripts import autonomous_ax_gate as run
from scripts import core_preservation_evaluate as metrics


def fixture_results(rows):
    result=[]
    for f in run.fixtures():
        for row in rows:
            if not row['fixture'] or row['id']!=f['query_id']:continue
            a=row['assessment']
            effective=row['grade'] if row['valid'] and a['category']=='JUDGEABLE' else None
            passed=row['valid'] and (effective is None if f['expected_uncertain'] else
                                     effective in f['expected_grade_band'])
            result.append({**row,'effective_grade':effective,'expected_grade_band':f['expected_grade_band'],
                           'expected_uncertain':f['expected_uncertain'],'policy_example_passed':passed,
                           'expectation_is_policy_example_not_human_Gold':True})
    return result


def audit_pending(rows):
    prior=read(run.PRIOR/'v2_reviewed_strict/labels.json')['records']
    sources=read(run.PRIOR/'source_registry.json')
    records=[];proposed={}
    for p in read(run.OUT/'pending75.json')['records']:
        reviews=[r for r in rows if not r['fixture'] and r['id']==p['id']]
        assert len(reviews)==2
        valid=[r for r in reviews if r['valid']]
        judgments=[r for r in valid if r['assessment']['category']=='JUDGEABLE' and r['grade'] is not None]
        agreement=len(judgments)==2 and judgments[0]['grade']==judgments[1]['grade']
        if agreement:
            classification='JUDGEABLE'
            grade=judgments[0]['grade']
        else:
            grade=None
            categories={r['assessment']['category'] for r in valid}
            if 'SOURCE_INSUFFICIENT' in categories:classification='INSUFFICIENT_SOURCE'
            elif 'EXPERT_REVIEW' in categories or len(valid)<2:classification='EXPERT_REVIEW'
            else:classification='CRITERION_DIFFERENCE'
        old=next(x for x in prior if (x['query_id'],x['case_id'])==(p['query_id'],p['case_id']))
        record={**p,'classification':classification,'proposed_grade':grade,
                'previous':old,'reviews':reviews,'source':sources[p['case_id']],
                'confirmed_for_tuning':False,'reason':'Policy reliability gate must pass before releasing any proposed grade.'}
        records.append(record)
        proposed[p['query_id'],p['case_id']]=record
    labels=[]
    for old in prior:
        p=proposed.get((old['query_id'],old['case_id']))
        if p is None or p['proposed_grade'] is None:
            labels.append(dict(old));continue
        labels.append({**old,'grade':p['proposed_grade'],'status':'JUDGED',
                       'rationale':'진단용 AI 일치 제안. 평가 기준 검증을 통과하지 않아 승인하지 않음.',
                       'label_source':'AI-Silver','diagnostic_only_not_released_for_tuning':True})
    return records,labels


def label_scenarios(prediction,labels,count=4096,grade_options=None):
    """Feasible complete label assignments are witnesses, not guessed qrels."""
    rng=np.random.default_rng(20261107)
    ids=prediction['case_ids'];queries=prediction['query_ids'];conditions='ABCE'
    original={(r['query_id'],r['case_id']):r for r in labels}
    matrices={};per_query={};eligible=[]
    for q in queries:
        values=np.tile(np.array([original[q,c]['grade'] or 0 for c in ids],dtype=np.int8),(count,1))
        unknown=[j for j,c in enumerate(ids) if original[q,c]['status']!='JUDGED']
        if unknown:
            if grade_options is None:
                values[:,unknown]=rng.integers(0,4,size=(count,len(unknown)))
                for i,grade in enumerate((0,3,1,2)):values[i,unknown]=grade
            else:
                for j in unknown:
                    choices=grade_options[q,ids[j]]
                    values[:,j]=rng.choice(choices,size=count)
                    values[0,j]=choices[0];values[1,j]=choices[-1]
                    values[2,j]=choices[min(1,len(choices)-1)]
                    values[3,j]=choices[max(0,len(choices)-2)]
        matrices[q]=values
        positives=(values>=2).sum(axis=1)
        gains=2.**values-1
        sorted_gains=np.sort(gains,axis=1)[:,::-1][:,:10]
        discount=1/np.log2(np.arange(2,12))
        ideal=(sorted_gains*discount).sum(axis=1)
        valid_f=positives>0;valid_n=ideal>0
        eligible.append((valid_f,valid_n))
        for c in conditions:
            ranks=[r['ranking'] for r in prediction['systems'][c] if r['query_id']==q]
            f=[];n=[]
            for rank in ranks:
                positions=[ids.index(cid) for cid in rank]
                hits=(values[:,positions[:5]]>=2).sum(axis=1)
                f.append(2*hits/(5+positives))
                dcg=(gains[:,positions[:10]]*discount).sum(axis=1)
                n.append(np.divide(dcg,ideal,out=np.zeros_like(dcg),where=ideal>0))
            per_query[c,q,'F1@5']=np.mean(f,axis=0)
            per_query[c,q,'nDCG@10']=np.mean(n,axis=0)
    summary=[];witnesses=[]
    for metric,elig_index in (('F1@5',0),('nDCG@10',1)):
        valid=np.logical_and.reduce([e[elig_index] for e in eligible])
        scores={c:np.mean([per_query[c,q,metric] for q in queries],axis=0) for c in conditions}
        for c in conditions:
            values=scores[c][valid]
            summary.append({'metric':metric,'condition':c,'valid_full8_scenarios':int(valid.sum()),
                            'observed_min':float(values.min()) if len(values) else None,
                            'observed_max':float(values.max()) if len(values) else None})
        indices=np.flatnonzero(valid)
        if not len(indices):continue
        difference=scores['E']-scores['C']
        for bound,index in [('min',indices[np.argmin(difference[valid])]),
                            ('max',indices[np.argmax(difference[valid])])]:
            assignment=[{'query_id':q,'case_id':cid,'hypothetical_grade':int(matrices[q][index,j])}
                        for q in queries for j,cid in enumerate(ids) if original[q,cid]['status']!='JUDGED']
            witnesses.append({'metric':metric,'bound_among_sampled_scenarios':bound,'scenario_index':int(index),
                              'E_minus_C':float(difference[index]),
                              'scores':{c:float(scores[c][index]) for c in conditions},
                              'uncertain_assignments':assignment,'not_real_labels':True})
    return {'seed':20261107,'scenario_count':count,'fixed_question_count':len(queries),
            'unknown_grade_set':[0,1,2,3] if grade_options is None else 'per-case observed reviewer options',
            'summary':summary,'witnesses':witnesses,
            'interpretation':'Existential sensitivity witnesses. Sampled extrema are not exact global bounds, probabilities, confidence intervals, or measured recommendation performance. No hypothetical grade is written into qrels.'}


def ndcg_outer_bounds(prediction,labels):
    """Safe outer ratios; shared ideal-DCG dependencies make bounds loose."""
    result=[];ids=prediction['case_ids'];d=1/np.log2(np.arange(2,12))
    for q in prediction['query_ids']:
        known={r['case_id']:r for r in labels if r['query_id']==q}
        low=np.array([known[c]['grade'] if known[c]['status']=='JUDGED' else 0 for c in ids])
        high=np.array([known[c]['grade'] if known[c]['status']=='JUDGED' else 3 for c in ids])
        lg=2.**low-1;hg=2.**high-1
        ideal_low=float(np.sort(lg)[::-1][:10]@d);ideal_high=float(np.sort(hg)[::-1][:10]@d)
        for c in 'ABCE':
            ranks=[r['ranking'] for r in prediction['systems'][c] if r['query_id']==q]
            numerator_low=[];numerator_high=[]
            for rank in ranks:
                pos=[ids.index(x) for x in rank[:10]]
                numerator_low.append(float(lg[pos]@d));numerator_high.append(float(hg[pos]@d))
            result.append({'query_id':q,'condition':c,'lower':mean(numerator_low)/ideal_high if ideal_high else None,
                           'upper':min(1.,mean(numerator_high)/ideal_low) if ideal_low else None,
                           'eligibility_uncertain':ideal_low==0})
    return {'records':result,'interpretation':'Conservative outer bounds only; do not treat independently extremized numerator/denominator as an attainable exact score.'}


def write_supporting_audits(rows,original,prediction):
    pairs={p['id']:p for p in read(run.OUT/'pending75.json')['records']}
    cases=read(run.ROOT/'docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    questions={q['query_id']:q['text'] for q in run.jsonl(run.client.old.QUESTIONS)}
    invalid=[]
    for item in rows:
        if item['fixture'] or item['valid']:continue
        p=pairs[item['id']];row=item['assessment'];reasons=[]
        if row is None:reasons.append('NO_COMPLETE_RECEIVED_ITEM')
        else:
            if any(not isinstance(q,str) or not q or q not in questions[item['query_id']]
                   for q in row.get('query_quotes',[])):reasons.append('NONLITERAL_QUERY_QUOTE')
            for claim in row.get('claims',[]):
                field=claim.get('field')
                if field not in ('Task','Context'):reasons.append('PERFORMED_CLAIM_FROM_UNAPPROVED_FIELD')
                elif not isinstance(claim.get('quote'),str) or claim['quote'] not in cases[p['case_id']][field.lower()]:
                    reasons.append('NONLITERAL_OR_WRONG_FIELD_CASE_QUOTE')
                if claim.get('role') not in ('ACTION','OBJECT','OUTPUT','CONDITION','AUTHORITY'):
                    reasons.append('INVALID_ROLE')
            if row.get('scope')=='FULL_CORE' and not {'ACTION','OBJECT','OUTPUT'}<= {
                    c.get('role') for c in row.get('claims',[])}:
                reasons.append('FULL_CORE_MISSING_NECESSARY_ROLE_EVIDENCE')
        invalid.append({**p,'provider':item['provider'],'request_id':item['request_id'],
                        'reasons':sorted(set(reasons)) or ['OTHER_SCHEMA_FAILURE'],
                        'assessment':row,'raw_response_retained':True})
    write(run.OUT/'source_validation_failures.json',{'records':invalid,'invalid_rows':len(invalid),
          'by_provider':dict(Counter(x['provider'] for x in invalid)),
          'reason_counts':dict(Counter(code for x in invalid for code in x['reasons'])),
          'valid_case_rows':sum(x['valid'] for x in rows if not x['fixture']),
          'missing_received_items':sum(x['assessment'] is None for x in rows if not x['fixture']),
          'interpretation':'Validation/output limitations, not proof that every case needs a business expert or every raw grade is false.'})
    recoveries=[]
    for identifier,payload in run.jobs():
        for provider in run.client.PROVIDERS:
            data=run.read_response(provider,identifier)
            if data and data.get('_received_token_limit'):
                recoveries.append({'provider':provider,'request_id':provider+'_'+identifier,
                    'response_sha256':sha(run.OUT/'api'/(provider+'_'+identifier+'_response.json')),
                    'complete_object_spans':data.get('_complete_object_spans',[]),
                    'received_assessment_count':len(data['assessments']),'expected_count':len(payload['cases']),
                    'no_missing_object_synthesized':True,'spans_refer_to_extracted_output_text_without_fences':True})
    write(run.OUT/'prefix_recovery_log.json',{'records':recoveries,'paid_retries':0,
          'method':'Decode complete JSON objects only; incomplete objects stay unavailable.'})
    sources=read(run.PRIOR/'source_registry.json')
    with (run.OUT/'expert_review_packet.jsonl').open('x',encoding='utf-8',newline='\n') as stream:
        for p in pairs.values():
            record={'query_id':p['query_id'],'case_id':p['case_id'],'business_problem':questions[p['query_id']],
                    'source':sources[p['case_id']],'grade':None,'status':'UNREVIEWED',
                    'label_source':'HUMAN_NOT_REVIEWED','rationale':'',
                    'request':'실제 수행 기능과 핵심 업무 전이 충분성을 검토. 원문 부족은 ABSTAIN. 추천·AI점수 비공개.'}
            stream.write(run.json.dumps(record,ensure_ascii=False)+'\n')
    options={}
    for item in read(run.PRIOR/'relevance_reviews.json')['records']:
        if item['valid'] and item['assessment']['status']=='JUDGED':
            options.setdefault((item['query_id'],item['case_id']),set()).add(item['assessment']['grade'])
    for item in rows:
        if item['fixture'] or not item['valid'] or item['assessment']['category']!='JUDGEABLE' or item['grade'] is None:
            continue
        p=pairs[item['id']];options.setdefault((p['query_id'],p['case_id']),set()).add(item['grade'])
    allowed={(x['query_id'],x['case_id']):sorted(options.get((x['query_id'],x['case_id']),set())) or [0,1,2,3]
             for x in original if x['status']=='ABSTAIN'}
    observed=label_scenarios(prediction,original,grade_options=allowed)
    observed['source_grade_options']=[{'query_id':q,'case_id':c,'observed_possible_grades':g}
                                      for (q,c),g in sorted(allowed.items())]
    observed['limits']='AI grade options are not certified ground truth; no real label changed.'
    write(run.OUT/'observed_reviewer_scenarios.json',observed)
    ledger=run.client.ledger()
    amount=sum((Decimal(x.get('cost_usd','0')) for x in ledger['calls'] if '_pending_' in x['id']),Decimal())
    write(run.OUT/'budget_followup.json',{'current_work_cost_usd':ledger['estimated_received_usd'],
        'remaining_work_cap_usd':str(Decimal(2)-Decimal(ledger['conservative_spent_or_reserved_usd'])),
        'pending75_phase_cost_usd':str(amount),'same_schema_4480_pairs_linear_cost_reference_usd':str(amount/75*4480),
        'not_an_exact_or_completed_Test_quote':True,'token_limited_outputs_make_this_inadequate_as_a_full_completion_upper_bound':True,
        'main_stop_reason':'Reliability, not account balance permissions','future_budget_reestimate_required_before_Test':True,
        'additional_topup_performed':False})


def main():
    run.setup()
    plan=read(run.OUT/'preregistration.json')
    assert all(sha(run.ROOT/p)==d for p,d in plan['protected_sha256'].items())
    rows=run.collect();fixtures=fixture_results(rows);audit,diagnostic=audit_pending(rows)
    write(run.OUT/'policy_fixture_results.json',{'records':fixtures,
          'passed':sum(r['policy_example_passed'] for r in fixtures),'total':len(fixtures),'not_human_Gold':True})
    write(run.OUT/'pending75_audit.json',{'records':audit,'classification_counts':dict(Counter(r['classification'] for r in audit)),
          'provisional_agreement_count':sum(r['proposed_grade'] is not None for r in audit),
          'final_confirmed_count':0,'primary_pending_count':75,
          'reason':'Failed independent policy checks prevent releasing proposed labels for tuning.'})
    write(run.OUT/'diagnostic_proposals.json',{'records':diagnostic,'not_approved_for_tuning_or_primary_performance':True})
    original=read(run.PRIOR/'v2_reviewed_strict/labels.json')['records']
    prediction=read(run.client.old.OUT/'predictions.json')
    write(run.OUT/'F1_uncertainty.json',{'records':metrics.incomplete_f1_bounds(prediction,original)})
    write(run.OUT/'nDCG_outer_bounds.json',ndcg_outer_bounds(prediction,original))
    scenarios=label_scenarios(prediction,original)
    write(run.OUT/'sensitivity_witnesses.json',scenarios)
    write_supporting_audits(rows,original,prediction)
    fixture_failures=[r for r in fixtures if not r['policy_example_passed']]
    semantic_failures=[r for r in fixture_failures if r['valid']]
    gate={'policy_fixture_gate_passed':not fixture_failures,'policy_fixture_failures':fixture_failures,
          'critical_semantic_policy_failures':semantic_failures,
          'primary_qrels_approved_for_tuning':False,'reliable_best_baseline_confirmed':False,
          'operational_baseline_registered':'E','operational_baseline_is_historical_observation':True,
          'decision':'STOP_BEFORE_PERFORMANCE_TUNING','improvement_iterations_executed':0,
          'final_candidate_frozen':False,'new_Test_created_or_executed':False,
          'reason':'Independent graders fail performed-work/functional-transfer/unknown-evidence policy examples. Current labels remain unapproved; hypothetical completions are not independent validation.'}
    assert semantic_failures,'Gate outcome needs reassessment rather than an automatic stop when policy checks pass'
    write(run.OUT/'entry_gate.json',gate)
    write(run.OUT/'iterations.json',{'max_authorized':5,'executed':0,'API_reviews_are_not_improvement_iterations':True,
          'records':[{'iteration':i,'status':'NOT_STARTED_RELIABILITY_GATE','change':None,
                      'F1@5':None,'nDCG@10':None,'adopted':False} for i in range(1,6)]})
    ledger=run.client.ledger()
    write(run.OUT/'status.json',{'classification':'검증 보류','completed':'Stage1 audit and reliability checks',
          'stage1_exit_passed':False,'stages2to4':'NOT_STARTED_ENTRY_GATE_FAILED',
          'improvement_iterations':0,'registered_baseline':'E','validated_best_model':None,
          'human_Gold':False,'new_Test_question_count':0,'new_Test_executed':False,
          'pending_primary_qrels':75,'provisional_AI_agreements':sum(r['proposed_grade'] is not None for r in audit),
          'source_policy_checks_passed':sum(r['policy_example_passed'] for r in fixtures),
          'source_policy_checks_total':len(fixtures),'semantic_policy_failures':len(semantic_failures),
          'report':'README.md','branch':'research/autonomous-ax-study-20261107',
          'API_calls':len(ledger['calls']),'API_cost':{k:v for k,v in ledger.items() if k!='calls'}})
    print('Gate STOP; fixture checks',sum(r['policy_example_passed'] for r in fixtures),'/',len(fixtures),
          'proposed source agreements',sum(r['proposed_grade'] is not None for r in audit),flush=True)


if __name__=='__main__':main()
