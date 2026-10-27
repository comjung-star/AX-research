"""Offline immutable-evidence audit and budget closeout. Never calls any API."""
from collections import Counter,defaultdict
from decimal import Decimal
from scripts import independent_verifier_json as run
v=run.v;BASE=run.ROOTS[0]

def main():
    panel=v.summary(v.prepare(),'panel');stability=v.summary(v.prepare(),'stability')
    costs={}
    for p in v.CFG['models']:
        actual=Decimal(0);unknown=Decimal(0);tokens=Counter();states=Counter();invalid=0
        for root in (*run.ROOTS,v.OUT):
            for f in (root/'attempts'/p).glob('*.json'):
                d=v.api.read_json(f);states[d.get('state','UNKNOWN')]+=1;u=d.get('usage') or {}
                if u.get('usage_cost_usd') is not None:actual+=Decimal(u['usage_cost_usd'])
                else:unknown+=Decimal(d.get('reserved_usd','0'))
                for k in ('actual_input_tokens','actual_output_tokens_including_thinking','cached_input_tokens'):tokens[k]+=u.get(k,0) or 0
                if d.get('state')=='RECEIVED' and not d.get('validation',{}).get('valid'):invalid+=1
        costs[p]={'usage_based_usd':v.api.money(actual),'unconfirmed_reserved_usd':v.api.money(unknown),'conservative_usd':v.api.money(actual+unknown),'tokens':dict(tokens),'states':dict(states),'original_validation_rejections':invalid}
    audit=[]
    for record in panel['records']:
        issues=[];cid=record['case_id'];target=record['target']
        if cid=='AXV2C_0093_01' and target=='V21D010:INTEGRATION':
            for role in ('evaluation','review'):
                for link in record[role]['links']:
                    if link[1]=='DIRECT':issues.append({'role':role,'kind':'WRONG_FUNCTION_DIRECT_LINK','why':'Task states defect/root-cause analysis, not integration of data sources.','raw_link':link})
                    elif 'requires' in link[6].lower():issues.append({'role':role,'kind':'UNPROVEN_NECESSITY_CLAIM','why':'Claim that analysis requires integrated data is not proof of actual integration; partial relevance remains a review question.','raw_link':link})
        if cid=='AXV2N_0139' and not record['evaluation']['links'] and not record['review']['links']:
            issues.append({'kind':'SHARED_POSSIBLE_FALSE_NEGATIVE','why':'Requirement text itself calls static contract summaries partial rather than direct. Both models returned no link; needs review, not automatic agreement approval.'})
        if cid=='AXV2N_0125' and record['computed']['score']==4:
            issues.append({'kind':'SHARED_CONTEXT_BONUS_REQUIRES_REVIEW','why':'Both models cite divided attention/manual processing as an extra condition. That is not by itself the query-specific long-thread condition. Two actual core tasks may independently justify4, so review the bonus route rather than declare the case irrelevant.'})
        audit.append({'qid':record['qid'],'target':target,'case_id':cid,'evaluator':record['evaluator'],'candidate_score':record['computed']['score'],'issues':issues,'final_released_score':None,'human_gold':False,'audit_status':'HOLD_SOURCE_ISSUE' if issues else 'HOLD_DISAGREEMENT' if record['computed']['score'] is None else 'PROVISIONAL_NOT_RELEASED_DUE_FAILED_GATE'})
    cs,_=v.r.cases_queries();key='AXV2C_0093_01';paths=[]
    for a in (1,2):
        f=v.OUT/'attempts/claude'/f'stability_0000_gemini_review_a{a}.json'
        d=v.api.read_json(f);paths.append({'source':str(f.relative_to(v.ROOT)).replace('\\','/'),'validation':d['validation'],'response':d['response_text'],'claim':'Perform/consolidate MES ERP and quality data integration','source_case':{k:cs[key][k] for k in ('problem','task','context')},'finding':'Invented performed integration operation; second attempt quotes Problem as Task evidence. Repeated substantive source violation, not normal ordinal disagreement.'})
    gate={'passed':False,'reason':'REPEATED_INVENTED_FUNCTION_IN_BLIND_REVIEW','panel_complete':panel['paired_records']==60,'stability_complete':False,'pilot_collection_allowed':False,'full_silver_approved':False,'human_gold':False,'blocking_evidence':paths}
    v.save(BASE/'semantic_audit.json',{'records':audit,'blocking_evidence':paths,'human_gold':False,'reviewer':'Codex source comparison; not a human adjudication or independent Test','comparison_limit':'Known development diagnostics and reused responses; no Gold accuracy claim.'})
    v.save(v.OUT/'panel_gate.json',gate)
    for root in (BASE,v.OUT):v.save(root/'halt.json',{'active':True,'reason':gate['reason'],'no_unknown_replay':True})
    v.save(BASE/'gate.json',gate)
    # Cost sensitivity uses observed successful per-case output and previously
    # counted four-case input; explicitly not an exact new full-run invoice.
    old=v.api.read_json(BASE/'budget.json');estimates={}
    for p in v.CFG['models']:
        components={};stage1=Decimal(0)
        for role in ('evaluation','review'):
            outs=[]
            for j in v.jobs(v.prepare(),'panel'):
                if j['provider']!=p or j['role']!=role:continue
                f=v.OUT/'results'/p/(j['job_id']+'.json');d=v.api.read_json(f)
                outs.append(d['usage']['actual_output_tokens_including_thinking'])
            mean=Decimal(sum(outs))/len(outs)
            inp=old['costs'][p]['full_roles'][role]['measured_representative_input_tokens']
            value=v.api.token_cost(p,inp*280,int(mean*1120))*Decimal('1.25');stage1+=value
            components[role]={'observed_successful_single_case_rows':len(outs),'mean_output_tokens_per_case':float(mean),'old_four_case_representative_input_tokens':inp,'projected_usd_with_25pct_retry':v.api.money(value)}
        ancillary=sum((Decimal(old['costs'][p]['phases'][k]) for k in ('remaining_inventory_upper','stage3_views_upper')),Decimal(0))
        estimates[p]={'illustrative_remaining_stage1_usd':v.api.money(stage1),'ancillary_inventory_and_stage3_ceiling_usd':v.api.money(ancillary),'illustrative_total_including_new_work_spent_usd':v.api.money(stage1+ancillary+Decimal(costs[p]['conservative_usd'])),'roles':components,'not_a_budget_approval':True}
    v.save(BASE/'cost_sensitivity.json',{'estimates':estimates,'initial_upper_forecast':old['costs'],'caveat':'Illustration only. Old four-case inputs and observed successful single-case outputs are not exact v6 full inputs or future batch outputs. Rejected responses and reservations are included in spent, not sampled twice. Max-output/full-prompt budget has not passed. No full call authorized.'})
    result={'base_commit':'3e0e7517d09c49af1cd375639cfb9ea5549db3a4','branch':'research/stage123-independent-verifier-20261027','status':'HOLD_REPEATED_UNSUPPORTED_FUNCTION','completed':{'review_table_pairs':20,'panel_model_rows':panel['received_model_rows'],'panel_evaluation_review_pairs':panel['paired_records'],'panel_candidate_distribution':panel['score_distribution'],'panel_unreleased':60,'stability_model_rows':stability['received_model_rows'],'stability_paired_results':stability['paired_records']},'not_completed':['1/2/4 stability comparison: stopped in single-case phase','Existing36 pair pilot /108 evaluations','Stage1 new3360 scores','Stage2 and Stage3 retrieval performance','Stage4 sealed, never opened'],'costs':costs,'claude_prior_used_and_reserved_usd':'0.82338200','claude_conservative_balance_estimate_usd':v.api.money(Decimal('5')-Decimal('0.823382')-Decimal(costs['claude']['conservative_usd'])),'account_balance_checked':False,'safety_buffer_usd':'0.50','human_gold':False,'approved_silver_scores':0,'references_30_not_certified':True,'stage3_planned_generation_requests':90,'stage3_repeats_per_model_query':3,'semantic_gate':False,'normal_disagreements_not_global_stop_reason':True}
    v.save(BASE/'final_status.json',result)
    import hashlib,subprocess
    inputs=[]
    for name in ('dev_problem_views.csv','dev_queries.json','split_groups.csv'):
        path=v.r.DATA/name;rel=str(path.relative_to(v.ROOT)).replace('\\','/')
        current=path.read_bytes();oldblob=subprocess.check_output(['git','show','3e0e7517d09c49af1cd375639cfb9ea5549db3a4:'+rel],cwd=v.ROOT)
        inputs.append({'path':rel,'sha256':hashlib.sha256(current).hexdigest(),'identical_to_base':current==oldblob})
    assert all(z['identical_to_base'] for z in inputs)
    v.save(BASE/'input_preservation.json',{'inputs':inputs,'case_count':112,'query_count':10,'stage4_not_opened':True})
    print({k:result[k] for k in ('status','completed','costs','claude_conservative_balance_estimate_usd')})
if __name__=='__main__':main()
