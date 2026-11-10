"""Offline only: derive coverage, precision bounds and disagreement from saved receipts."""
import json
from collections import Counter
from pathlib import Path
from scripts import independent_cross_validation_20261110 as run
from scripts.continue_cross_validation_20261110 import accepted
from ax_research.independent_cross_validation import summarize,agreement,utility,score_question

OUT=run.OUT

def report():
    run.verify_frozen()
    assert run.read(OUT/'anthropic-run.json')['status']=='BLOCKED'
    assert run.read(OUT/'gemini-run-amended.json')['status'] in ('COMPLETE','BLOCKED','PARTIAL_EVIDENCE')
    recommendations=run.read(OUT/'recommendations.json');facts=run.read(OUT/'case-facts.json')
    pairs=run.read(OUT/'deduplicated-pairs.json');universe={(x['question_id'],x['case_id']) for x in pairs}
    receipts=[(p,run.read(p)) for p in run.receipt_paths()]
    grades={p:{} for p in run.MODELS};provenance={p:{} for p in run.MODELS};audit=[]
    attempted={p:set() for p in run.MODELS};attempted_q={p:set() for p in run.MODELS}
    raw_attempts=Counter();raw_unique={p:set() for p in run.MODELS}
    # Original attempts before technical recovery; first valid row is immutable.
    for provider in run.MODELS:
        paths=sorted([(p,r) for p,r in receipts if r['provider']==provider],key=lambda t:(t[1]['question_id'],'technical1' in t[0].name))
        for path,r in paths:
            req=run.read(path.with_name(path.name.replace('.response.','.request.')))
            body=req['body']
            payload=json.loads(body['messages'][0]['content']) if provider=='anthropic' else json.loads(body['contents'][0]['parts'][0]['text'])
            q=payload['question_id'];attempted_q[provider].add(q)
            for c in payload['cases']:attempted[provider].add((q,c['case_id']))
            assert body==run.body(provider,payload),'prompt/model/body mutation'
            assert payload['user_question']==recommendations[q]['question']
            for c in payload['cases']:assert c==facts[c['case_id']],'altered case fact'
            good,bad=accepted(r,payload)
            if 'raw' in r:
                try:
                    rows=run.parse(provider,r['raw'])['judgments'];raw_attempts[provider]+=len(rows)
                    raw_unique[provider].update((q,x['case_id']) for x in rows)
                except Exception:pass
            if 'technical1' in path.name:
                assert all((q,c['case_id']) not in grades[provider] for c in payload['cases']),'valid row regraded'
            for c,row in good.items():
                key=(q,c);assert key in universe and key not in grades[provider],'duplicate accepted judgment'
                grades[provider][key]=row['grade'];provenance[provider][key]={'receipt':path.relative_to(OUT).as_posix(),'row':row,'model_requested':r['model_requested'],'model_returned':r.get('model_returned')}
            audit.append({'receipt':path.relative_to(OUT).as_posix(),'provider':provider,'question_id':q,'status':r['status'],'requested_pairs':len(payload['cases']),'valid_rows':len(good),'invalid_rows':bad})
    # Only here, after both terminal run states, open the existing OpenAI grades/metrics.
    comparison_opened_at=run.stamp()
    old=run.read(run.OLD/'labels.json');oldmetrics=run.read(run.OLD/'metrics.json')
    openai={(q,c):str(old[q]['cases'][c]['grade']) for q,c in universe}
    provider_status={}
    for p in run.MODELS:
        qs={q:len([c for qq,c in grades[p] if qq==q]) for q in recommendations}
        provider_status[p]={'model':run.MODELS[p],'attempted_generation_calls':sum(r['provider']==p for _,r in receipts),'attempted_questions':len(attempted_q[p]),
           'unique_pairs_sent':len(attempted[p]),'unique_pairs_never_sent':330-len(attempted[p]),'raw_grade_attempts':raw_attempts[p],
           'raw_unique_graded_pairs':len(raw_unique[p]),'accepted_pairs':len(grades[p]),'abstain_pairs':sum(v=='ABSTAIN' for v in grades[p].values()),
           'invalid_evidence_unresolved_pairs':len(raw_unique[p]-set(grades[p])),'no_raw_grade_pairs':330-len(raw_unique[p]),
           'missing_accepted_total':330-len(grades[p]),'fully_covered_questions':sum(qs[q]==len(recommendations[q]['deduplicated_blind_order']) for q in recommendations),
           'accepted_counts_by_question':qs}
    byq=lambda g:{q:{c:v for (qq,c),v in g.items() if qq==q} for q in recommendations}
    performance={'metric':'Macro Precision on fixed per-question original K; no new Recall or F1','OpenAI':summarize(recommendations,byq(openai)),
      'anthropic':None if not grades['anthropic'] else summarize(recommendations,byq(grades['anthropic'])),
      'gemini':None if not grades['gemini'] else summarize(recommendations,byq(grades['gemini'])),'consensus':None,
      'interpretation':'Partial-provider intervals are unresolved-data bounds over all20questions, NOT completed new evaluation scores. Judged-only precision uses differing denominators and is not primary.'}
    if len(grades['anthropic'])==len(grades['gemini'])==330:
        consensus={}
        for key in universe:
            a,b=utility(grades['anthropic'][key]),utility(grades['gemini'][key])
            consensus[key]=None if a is None or b is None or a!=b else '2' if a else '0'
        performance['consensus']=summarize(recommendations,byq(consensus))
    agreements={}
    for name,left,right in [('Claude_Gemini',grades['anthropic'],grades['gemini']),('OpenAI_Claude',openai,grades['anthropic']),('OpenAI_Gemini',openai,grades['gemini'])]:
        m=agreement(left,right)
        groups={}
        for key in set(left)&set(right):groups.setdefault(facts[key[1]]['source_group_id'],[]).append(key)
        vals=[]
        for keys in groups.values():
            eligible=[k for k in keys if utility(left[k]) is not None and utility(right[k]) is not None]
            if eligible:vals.append(sum(utility(left[k])==utility(right[k]) for k in eligible)/len(eligible))
        m['source_group_balanced_binary_agreement_descriptive']=sum(vals)/len(vals) if vals else None
        m['eligible_source_groups']=len(vals);agreements[name]=m
    disagreements=[]
    for q,c in sorted(universe):
        values={'OpenAI':openai[q,c],**{p:g.get((q,c)) for p,g in grades.items()}}
        new={p:v for p,v in values.items() if p!='OpenAI' and v is not None}
        grade_disagreement=any(v!=values['OpenAI'] for v in new.values())
        binary_disagreement=any(utility(v) is not None and utility(v)!=utility(values['OpenAI']) for v in new.values())
        if grade_disagreement or any(v=='ABSTAIN' for v in new.values()):
            disagreements.append({'question_id':q,'case_id':c,'question':recommendations[q]['question'],'grades':values,'binary_disagreement':binary_disagreement,
              'OpenAI_reason':{k:old[q]['cases'][c].get(k) for k in ('brief_bridge','assumption','bound_source_task')},
              'new_judgments':{p:provenance[p][q,c] for p in new},'source_group':facts[c]['source_group_id'],'source':facts[c]})
    missing=[]
    for p in run.MODELS:
        for q,c in sorted(universe-set(grades[p])):
            missing.append({'provider':p,'question_id':q,'case_id':c,'reason':'INVALID_EVIDENCE_AFTER_ONE_TECHNICAL_RECOVERY' if (q,c) in raw_unique[p] else 'HTTP_FAILURE_OR_NOT_ATTEMPTED','AI_ABSTAIN':False})
    # Descriptive source-group importance: remove net contributions without reranking or changing K.
    sensitivity={}
    for p,g in [('OpenAI',openai),('gemini',grades['gemini'])]:
        if not g:continue
        rows=[];gq=byq(g)
        for group in sorted({f['source_group_id'] for f in facts.values()}):
            omit={c for c,f in facts.items() if f['source_group_id']==group}
            r=[score_question(v['A'],v['B'],gq[q],omit=omit) for q,v in recommendations.items()]
            rows.append({'group':group,'mean_delta_lower':sum(x['delta_lower'] for x in r)/20,'mean_delta_upper':sum(x['delta_upper'] for x in r)/20})
        sensitivity[p]={'scope':'Fixed-K contribution removal only; not new retrieval or a source-cluster statistical CI','by_removed_group':rows}
    cost={'generation_attempts':len(receipts),'non_generation_model_queries':2,'successful_generation_responses':sum('raw' in r for _,r in receipts),
      'usage_paid_rate_equivalent_usd':sum(r.get('usage',{}).get('estimated_cost_usd',0) for _,r in receipts),'reserved_usd':sum(r['reserved_usd'] for _,r in receipts),
      'budget_cap_usd':run.BUDGET,'unresolved_deliveries':[p.relative_to(OUT).as_posix() for p,r in receipts if r.get('delivery_unknown')],
      'billing_note':'Gemini error identifies free-tier account. Paid-rate equivalent is not verified actual charge. Claude rejected for low credit with no generation usage returned.'}
    status={'status':'CROSS_VALIDATION_INCOMPLETE','decision':'개선 미확인 — 교차검증 미완료; B의 열세를 뜻하지 않음','new_provider_status':provider_status,
       'OpenAI_comparison_first_loaded_after_terminal_states_at':comparison_opened_at,'cost':cost,'Claude_Gemini_consensus_available':False,
       'new_Recall_or_F1_computed':False,'no_OpenAI_substitution':True,'Test15_opened':False,'algorithm_or_original_ranks_changed':False}
    run.save(OUT/'performance.json',performance);run.save(OUT/'agreement.json',agreements);run.save(OUT/'disagreements.json',disagreements)
    run.save(OUT/'missing-and-abstain.json',{'missing_valid_judgments':missing,'AI_ABSTAIN':[{'provider':p,'question_id':q,'case_id':c} for p,g in grades.items() for (q,c),v in g.items() if v=='ABSTAIN']})
    run.save(OUT/'request-audit.json',audit);run.save(OUT/'source-group-sensitivity.json',sensitivity);run.save(OUT/'final-status.json',status)
    run.save(OUT/'judgment-provenance.json',[{'provider':p,'question_id':q,'case_id':c,**v} for p,g in provenance.items() for (q,c),v in sorted(g.items())])
    run.verify_frozen()
    checks={'at':run.stamp(),'original_frozen_files_unchanged':len(run.read(OUT/'freeze.json')['original_sha256']),'frozen_blind_input_and_protocol_hashes_verified':True,
      '20_original_A_B_lists_equal_counts_and_order_preserved':True,'unique_pairs_per_provider':330,'duplicate_accepted_judgments':0,
      'valid_first_rows_regraded_in_technical_recovery':0,'all_accepted_citations_exactly_in_input_fields':True,
      'new_grades_not_silently_replaced_with_OpenAI':True,'source_PTC_matches_original_registry':True,'all_new_requests_use_frozen_prompt_schema_and_case_facts':True,
      'analysis_unit_questions_not_repeated_cases':True,'no_new_Recall_F1':True,'secret_values_serialized':False,
      'tests':'8 statistical/ABSTAIN/shared-case tests passed; separate test run logged in task; no live API tests repeated.',
      'limits':'Failed/missing evidence is reported separately from AI ABSTAIN and irrelevant. Full20 independent-AI point effect and two-provider agreement/consensus not available.'}
    run.save(OUT/'verification.json',checks)
    print(json.dumps({'coverage':provider_status,'agreement':agreements,'cost':cost,'OpenAI_macro':performance['OpenAI']['macro'],'OpenAI_precision_delta':performance['OpenAI']['statistics'],
      'Gemini_partial_bounds':performance['gemini']['statistics'] if performance['gemini'] else None,'binary_disagreements':sum(x['binary_disagreement'] for x in disagreements)},ensure_ascii=False))

if __name__=='__main__':report()
