"""Offline evidence/cost report. Does not call any model or relabel judgments."""
import hashlib
import json
from collections import Counter
from decimal import Decimal
from scripts import aoo_experiment as r

def finish():
    plan=r.api.read_json(r.OUT/'plan.json');diag=r.pilot_report(plan)
    costs={};versions={};findings=[]
    for provider in r.CFG['models']:
        actual=Decimal(0);upper=Decimal(0);tokens_in=0;tokens_out=0;confirmed=0;unknown=[]
        for folder in (r.ARCHIVE,r.OUT):
            attempts=[(p,r.api.read_json(p)) for p in (folder/'attempts'/provider).glob('*.json')]
            version={'confirmed_cost_usd':Decimal(0),'reserved_or_actual_usd':Decimal(0),'confirmed_responses':0,'http_statuses':Counter()}
            for p,a in attempts:
                cost=Decimal(a.get('usage',{}).get('usage_cost_usd','0'));reserved=Decimal(a.get('usage',{}).get('usage_cost_usd',a['reserved_usd']))
                actual+=cost;upper+=reserved;version['confirmed_cost_usd']+=cost;version['reserved_or_actual_usd']+=reserved
                if a.get('usage'):
                    confirmed+=1;version['confirmed_responses']+=1;tokens_in+=a['usage']['actual_input_tokens'];tokens_out+=a['usage']['actual_output_tokens_including_thinking']
                elif a['state']!='CANCELLED_BEFORE_DISPATCH':unknown.append({'file':str(p.relative_to(r.ROOT)).replace('\\','/'),'http_status':a.get('http_status'),'state':a['state'],'reserved_usd':a['reserved_usd']})
                if a.get('http_status'):version['http_statuses'][str(a['http_status'])]+=1
            version['confirmed_cost_usd']=r.api.money(version['confirmed_cost_usd']);version['reserved_or_actual_usd']=r.api.money(version['reserved_or_actual_usd']);version['http_statuses']=dict(version['http_statuses'])
            versions.setdefault(str(folder.relative_to(r.ROOT)).replace('\\','/'),{})[provider]=version
        costs[provider]={'confirmed_input_tokens':tokens_in,'confirmed_output_tokens_including_thinking':tokens_out,'confirmed_responses_including_rejected_outputs':confirmed,'confirmed_cost_usd':r.api.money(actual),'reserved_or_actual_usd':r.api.money(upper),'unconfirmed_reserved_usd':r.api.money(upper-actual),'unconfirmed_cost_requests':unknown}
    cl=Decimal(costs['claude']['reserved_or_actual_usd'])+Decimal(r.CFG['claude_prior_actual_or_reserved_usd'])
    report={'scope':'THIS_NEW_BRANCH_TASK_ONLY; v9 and v10 separate scores, combined costs','providers':costs,'versions':versions,'this_work_total_confirmed_usd':r.api.money(sum((Decimal(x['confirmed_cost_usd']) for x in costs.values()),Decimal(0))),
            'this_work_total_actual_plus_reserved_usd':r.api.money(sum((Decimal(x['reserved_or_actual_usd']) for x in costs.values()),Decimal(0))),
            'claude_preexisting_actual_plus_reserved_usd':r.CFG['claude_prior_actual_or_reserved_usd'],'claude_all_research_conservative_usd':r.api.money(cl),'claude_reported_credit_remaining_lower_bound_usd':r.api.money(Decimal(5)-cl),'claude_available_after_050_buffer_usd':r.api.money(Decimal('4.5')-cl),
            'account_balance_queried':False,'automatic_or_additional_topup':False,'official_price_per_million':{p:{'input':str(s['input']),'output':str(s['output'])} for p,s in r.api.CONFIG['models'].items()}}
    r.save(r.OUT/'cost_report.json',report)
    cases,queries=r.inputs()
    for provider,jobid,cid in [('gemini','pilot_0000','AXV2P2_0048_01'),('claude','pilot_0001','AXV2H_0002_01'),('claude','pilot_0000','AXV2P2_0048_01')]:
        path=r.OUT/'attempts'/provider/(jobid+'_a1.json');a=r.api.read_json(path)
        text=a.get('response_text','')
        try:row=json.loads(text)['ratings'][cid]
        except (ValueError,KeyError):continue
        job=next(j for j in plan['pilot'] if j['job_id']==jobid)
        findings.append({'provider':provider,'job_id':jobid,'case_id':cid,'query':queries[job['query_id']],'target_id':job['target_id'],'case_ptc':{f:cases[cid][f] for f in ('problem','task','context')},'original_row':row,'entire_response_validation':a.get('validation'),'source_file':str(path.relative_to(r.ROOT)).replace('\\','/'),'not_relabelled':True})
    r.save(r.OUT/'grounding_findings.json',{'agent_review_not_human_gold':True,'examples':findings})
    for p,h in plan['input_hashes'].items():assert hashlib.sha256((r.ROOT/p).read_bytes()).hexdigest()==h
    status={'status':'PILOT_NOT_PASSED_STOP_BEFORE_STAGE1','planned_pilot_pairs':36,'planned_pilot_scores':108,'latest_valid_score_count':sum(diag['received_valid_scores_by_model'].values()),'latest_valid_scores_by_model':diag['received_valid_scores_by_model'],'complete_three_judge_pairs':diag['complete_pairs'],
            'whole_query_aspect_all_pairs_verified':False,'new_stage1_scores':0,'stage2_executed':False,'stage3_executed':False,'dynamic_generation_calls':0,'approved_silver_pairs':0,'human_gold':False,'stage4_sealed':True,'original_input_hashes_unchanged':True,'models':r.CFG['models'],'new_api_dispatch_allowed':False}
    r.save(r.OUT/'final_status.json',status)
    rows=['# v10 부분 재시험 원점수 — 미승인','','미수집은 —. 사전 구간은 사람 정답이 아닌 에이전트의 점검 가설이며 모델에게 제공하지 않았다. 버전별 점수를 섞지 않는다.','','|질문|대상|사례|사전 진단 구간|GPT|Gemini|Claude|','|---|---|---|---|---:|---:|---:|']
    for e in diag['rows']:
        values=[str(e['scores'].get(p,'—')) for p in r.CFG['models']]
        rows.append('|'+ '|'.join([e['query_id'],e['target_id'],e['case_id'],e['diagnostic_band'],*values])+'|')
    path=r.OUT/'pilot_comparison.md';path.write_text('\n'.join(rows)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'status':status,'costs':report},ensure_ascii=False))
    return status,report

if __name__=='__main__':finish()
