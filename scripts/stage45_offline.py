"""Frozen follow-up: source review, label-blind heldout inference, then evaluation.

Paid work is blocked because the requested credit-balance prerequisite could not
be verified with existing credentials. No key or sealed raw payload is exported.
"""
import argparse
import copy
import json
from pathlib import Path
import socket
import subprocess
import sys
from ax_research.heldout import read,write,sha,jsonl
from ax_research.functional_mapping import extract,compare
from ax_research.action_aggregation import purpose_filter
from ax_research.semantic_mapping import combined_score
from ax_research.new_validation import evaluate
from scripts.validation123_analyze import summarize

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/ax-stage4-stage5-independent-2026-11-03'
DEV=ROOT/'docs/validation-c0c1-stage1to3-2026-11-03'
PAYLOAD=Path.home()/'.ax-heldout-work-b/20261028'
MODEL=ROOT.parent/'AX-prototype/.local/models/bge-m3'
BASE='b5158583cc61da9f3f73961d2083e82b233ccb85'


def stage4():
    d=OUT/'stage4';d.mkdir(exist_ok=False)
    old=read(DEV/'stage1/qrels_v2.json');rows=copy.deepcopy(old['records']);reviews=read(DEV/'stage1/review19.json')['records'];audit=[]
    for item in reviews:
        r=copy.deepcopy(item);r['rechecked_by']='Same assistant source review; no new independent evaluator; not Human-Gold'
        r['stage4_grade']=r['final_grade'];r['stage4_status']=r['final_status']
        if r['case_id']=='AXV2H_0021_01' and r['query_id']=='NV20261102_09':
            r.update(stage4_grade=1,stage4_status='JUDGED',source_url='https://www.makinarocks.ai/news/makinarocks-hyundai-1400-robots-rpms/',source_checked='2026-11-03',source_evidence_paraphrase='로봇 동작 데이터로 장비 고장 사전예측, 구동부 진단·셋업 이상 탐지·상태 변동점 알림. 다음 생산 묶음의 제품 불량 예측은 확인되지 않음.',stage4_reason='예측 행동의 보조 공통점은 있지만 예측 대상과 산출물이 장비 고장이고 요청은 제품 품질 위험이다. 원출판물로 수행 범위가 확인돼 보류를1로 해결. 같은 제조업·예측이라는 이유만으로2를 주지 않는다.')
        elif r['case_id']=='AXV24_918f26607568' and r['query_id']=='NV20261102_08':
            r.update(source_url='https://cloud.google.com/customers/purplleai',source_checked='2026-11-03',source_evidence_paraphrase='반품 요청의 고객 사진 손상·유효기간을 판단하는 에이전트 흐름과 환불 처리 시간 단축을 소개. 승인된 계좌 변경을 ERP에 기록하는 실행은 명시하지 않음.',stage4_reason='반품 흐름의 의사결정과 계좌 변경의 실제 시스템 기록은 다르다. 기사에 환불 처리 업무가 있어도 구체적 쓰기 동작을 추정할 수 없어 보류 유지.')
        else:r['stage4_reason']='기존 블라인드 API·원문 Task/Context 근거와 v2의 기능적 응용/보조 기능 구분을 재확인. 새 원문 확인이 없는 항목은 v2 유지; 독립 재검증 주장 금지.'
        audit.append(r)
    for r in rows:
        if r['query_id']=='NV20261102_09' and r['case_id']=='AXV2H_0021_01':r.update(grade=1,status='JUDGED',rationale=next(x['stage4_reason'] for x in audit if x['review_no']==4),label_source='AI-Silver')
    assert sum(a!=b for a,b in zip(rows,old['records']))==1
    write(d/'qrels_v3.json',{'records':rows,'label_source':'AI-Silver; source reviewed by same assistant','previous_sha256':sha(DEV/'stage1/qrels_v2.json'),'human_verified':False})
    write(d/'review19.json',{'records':audit,'new_web_checked_pairs':2,'source_quotes_not_republished':True})
    pred=read(DEV/'stage3/predictions/rankings.json');allmetrics=[]
    for rep in (0,1,2,3):
        names=('E1','E3','E3_NEUTRAL') if rep==0 else ('E2','E4','E4_NEUTRAL')
        part={new:[{k:v for k,v in r.items() if k!='repeat'} for r in pred['systems'][oldname] if rep==0 or r['repeat']==rep] for new,oldname in zip(('C0','C1','C1_NO_EMBEDDING'),names)}
        r=evaluate({'query_ids':pred['query_ids'],'case_ids':pred['case_ids'],'systems':part},rows)
        write(d/f'metrics_v3_repeat{rep}.json',r)
        for x in r['per_query']:allmetrics.append({**x,'condition':names[('C0','C1','C1_NO_EMBEDDING').index(x['system'])],'repeat':rep})
    write(d/'v3_summary.json',{'macro':summarize(allmetrics,rows),'per_query':allmetrics,'comparison_warning':'v3 cohort can differ from v2; use common question IDs when comparing label versions'})
    # Label alternatives are explicitly sensitivity scenarios, never replacements.
    sensitivities=[]
    for name,changed in [('API_disagreements_only',lambda x:x['api_final_disagreement']),('all19_one_grade_lower',lambda x:True),('positive_boundary19_set1',lambda x:x['final_grade']==2)]:
        alt=copy.deepcopy(rows);by={(r['query_id'],r['case_id']):r for r in alt}
        for v in reviews:
            if not changed(v):continue
            x=by[v['query_id'],v['case_id']]
            if name=='API_disagreements_only':x.update(grade=v['blind_api_grade'],status=v['blind_api_status'])
            elif x['status']=='JUDGED':x['grade']=max(0,x['grade']-1) if name=='all19_one_grade_lower' else 1
        out=[]
        for rep in (0,1,2,3):
            names=('E1','E3','E3_NEUTRAL') if rep==0 else ('E2','E4','E4_NEUTRAL')
            pp={new:[{k:v for k,v in r.items() if k!='repeat'} for r in pred['systems'][oldname] if rep==0 or r['repeat']==rep] for new,oldname in zip(('C0','C1','C1_NO_EMBEDDING'),names)}
            e=evaluate({'query_ids':pred['query_ids'],'case_ids':pred['case_ids'],'systems':pp},alt)
            for x in e['per_query']:out.append({**x,'condition':names[('C0','C1','C1_NO_EMBEDDING').index(x['system'])],'repeat':rep})
        sensitivities.append({'name':name,'counterfactual_not_label_replacement':True,'macro':summarize(out,alt)})
    write(d/'label_sensitivity.json',{'scenarios':sensitivities,'not_tuning':True})
    pending=[r for r in audit if r['stage4_status']=='ABSTAIN' or r['api_final_disagreement']]
    write(d/'human_confirmation.json',{'records':pending,'human_verification_performed':False,'priority':'Remaining ERP execution ambiguity, functional transfer boundary and temperature examples. Full independent label audit still required.'})
    write(d/'complete.json',{'complete':True,'old_abstain':2,'resolved':1,'remaining':1,'reviewed':19,'human_verified':False,'files':{p.name:sha(p) for p in d.iterdir()}})


def prepare():
    from scripts.heldout_run import freeze
    m=read(PAYLOAD/'manifest.json');d=OUT/'preregistration';d.mkdir(exist_ok=False)
    state=freeze(MODEL);write(d/'model_environment.json',state)
    # Hash bytes without interpreting question/qrel contents.
    mh=sha(PAYLOAD/'manifest.json');q=sha(PAYLOAD/'questions.jsonl')
    assert q==m['files']['questions']['sha256']
    write(d/'plan.json',{'base_commit':BASE,'policy_sha256':sha(ROOT/'configs/heldout_policy_v1.json'),'manifest_sha256':mh,'manifest_metadata':m,'questions_sha256':q,'C0_core_sha256':sha(ROOT/'src/ax_research/functional_mapping.py'),'C1_core_sha256':sha(ROOT/'src/ax_research/action_aggregation.py'),'C1_config_sha256':sha(ROOT/'configs/action_aggregation_20261102.json'),'adapter_sha256':sha(Path(__file__)),'primary_candidate':'T4, preregistered before Test access; not selected by Test scores','conditions':{'T1':'C0 original','T2':'C0 original + LLM perspectives','T3':'C1 original','T4':'C1 original + LLM perspectives'},'generation':'Same prior view_system;1to6;3 repeats;query only','paid_work_state':'BLOCKED_BALANCE_VERIFICATION','reason':'User requires actual available balance checked first. Model GET200, org cost GET403, no admin key; actual credit cannot be verified. Do not assume zero or sufficient balance. No paid POST, no recharge. Execute offline T1/T3 and mark T2/T4 unavailable.','paid_cap_usd':2,'paid_calls':0,'scoring':'Original immutable heldout v1 threshold2; gains2**grade-1; all112 judged required for R/F1/nDCG; zero positives undefined; unknown never zero; pairwise common eligible questions','tie':'Frozen original hybrid RRF60, equal Dense/BM25; dynamic mean perspective-only paths if ever authorized/executable','aggregation':'Frozen rule max(original,branch); semantic(original+maxbranch)/2;50:50','test_qrels_opened':False,'before_question_body_access':True,'no_model_tuning':True,'raw_test_payload_export_to_git':False})


def inference(scratch):
    scratch.mkdir(exist_ok=False);d=OUT/'stage5/predictions';d.mkdir(parents=True,exist_ok=False)
    plan=read(OUT/'preregistration/plan.json');assert sha(Path(__file__))==plan['adapter_sha256']
    assert sha(PAYLOAD/'manifest.json')==plan['manifest_sha256'];assert sha(PAYLOAD/'questions.jsonl')==plan['questions_sha256']
    accesses=[]
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes)):
            s=str(args[0]).lower()
            if any(w in s for w in ('qrels','review_queue','work_b_build','human_confirmation')):raise RuntimeError('No labels or review queue during inference')
            if '.ax-heldout-work-b' in s:accesses.append(str(args[0]))
    sys.addaudithook(audit)
    def blocked(*a,**k):raise RuntimeError('No network during offline inference')
    socket.socket.connect=blocked;socket.create_connection=blocked
    qs=jsonl(PAYLOAD/'questions.jsonl');assert all(set(q)=={'query_id','text','split'} and q['split']=='TEST' for q in qs)
    assert len(qs)==len({q['query_id'] for q in qs})
    known=[q['text'] for q in jsonl(ROOT/'docs/c0-c1-new-validation-2026-11-02/input/questions.jsonl')]
    from scripts.heldout_run import predict,freeze,known_queries
    known += [q['text'] for q in known_queries()];exact=[q['query_id'] for q in qs if q['text'] in known]
    assert not exact,'Exact prior query reuse'
    before=freeze(MODEL);raw=predict(qs,MODEL,scratch)
    ev=read(scratch/'evidence.json');by={(r['query_id'],r['case_id']):r for r in ev['records']};rules=read(ROOT/'configs/functional_mapping_20261028.json');cfg=read(ROOT/'configs/action_aggregation_20261102.json');cp=read(ROOT/'docs/query-case-functional-mapping-2026-10-28/stage2/case_profiles.json');filtered={c:{role:purpose_filter(p,cfg) for role,p in roles.items()} for c,roles in cp.items()}
    systems={'T1':raw['systems']['C'],'T3':[],'T3_NEUTRAL':[]};detail=[]
    for q in qs:
        qid=q['query_id'];profile=purpose_filter(extract(q['text'],rules),cfg);scores={};neutral={}
        for c in raw['case_ids']:
            m=compare(profile,filtered[c]);sem=by[qid,c]['semantic'];scores[c]=combined_score(m['mapping_grade'],sem['score']);neutral[c]=m['mapping_grade']/8+.25
            detail.append({'query_id':qid,'case_id':c,'C0_rule':by[qid,c]['rule'],'C1_rule':m,'semantic':sem,'dense':by[qid,c]['dense'],'bm25':by[qid,c]['bm25'],'hybrid_tie':by[qid,c]['retrieval_tie'],'T1_score':by[qid,c]['combined'],'T3_score':scores[c]})
        for name,values in [('T3',scores),('T3_NEUTRAL',neutral)]:
            ranking=sorted(values,key=lambda c:(-values[c],-by[qid,c]['retrieval_tie'],c));systems[name].append({'query_id':qid,'ranking':ranking,'scores':values,**{f'top{k}':ranking[:k] for k in (5,10,20)}})
    pred={'case_ids':raw['case_ids'],'query_ids':raw['query_ids'],'systems':systems,'blocked_conditions':{'T2':'Credit-balance prerequisite not verified; no fabricated perspectives','T4':'Credit-balance prerequisite not verified; no fabricated perspectives'}}
    write(d/'rankings.json',pred);write(d/'score_evidence.json',{'records':detail,'original_case_registry':'docs/dense-bm25-candidates-2026-10-27/case_registry.json','query_profiles_preserved_locally':str(scratch/'evidence.json')})
    for k in (5,10,20):write(d/f'top{k}.json',{n:[{'query_id':r['query_id'],'case_ids':r[f'top{k}']} for r in rs] for n,rs in systems.items()})
    after=freeze(MODEL);assert before==after
    write(d/'inference_receipt.json',{'question_count':len(qs),'case_count':112,'questions_sha256':sha(PAYLOAD/'questions.jsonl'),'manifest_sha256':sha(PAYLOAD/'manifest.json'),'raw_evidence_sha256':sha(scratch/'evidence.json'),'new_query_vectors_sha256':sha(scratch/'new_query_vectors.npz'),'raw_payload_exported':False,'qrels_read':False,'sealed_files_opened_during_inference':accesses,'exact_prior_query_duplicates':exact,'semantic_independence_not_proven':True,'network_calls':0,'paid_calls':0,'model_freeze':before,'command':sys.argv})
    write(d/'complete.json',{'complete_available_conditions':True,'all_four_conditions_complete':False,'unavailable':['T2','T4'],'qrels_read':False,'files':{p.name:sha(p) for p in d.iterdir()}})
    print('Offline Test original predictions sealed',len(qs),'questions; no qrels',flush=True)


def evaluation():
    src=OUT/'stage5/predictions';seal=read(src/'complete.json')
    for n,h in seal['files'].items():assert sha(src/n)==h
    d=OUT/'stage5/evaluation';d.mkdir(exist_ok=False);plan=read(OUT/'preregistration/plan.json');m=read(PAYLOAD/'manifest.json')
    assert sha(PAYLOAD/'manifest.json')==plan['manifest_sha256'];assert sha(PAYLOAD/'qrels.jsonl')==m['files']['qrels']['sha256']
    # FIRST qrels body read: after all executable predictions are sealed and
    # unavailable dynamic conditions are terminally recorded, not silently omitted.
    labels=jsonl(PAYLOAD/'qrels.jsonl');pred=read(src/'rankings.json');mapping={'C0':'T1','C1':'T3','C1_NO_EMBEDDING':'T3_NEUTRAL'}
    e=evaluate({**pred,'systems':{new:pred['systems'][old] for new,old in mapping.items()}},labels)
    e['scope']=m['judgment_scope'];e['system_names']=mapping;e['not_final_independent_test_claim']=True
    write(d/'metrics_partial_original.json',e)
    counts={s:sum(r['status']==s for r in labels) for s in ('JUDGED','ABSTAIN','UNJUDGED')};full=[q for q in pred['query_ids'] if all(r['status']=='JUDGED' for r in labels if r['query_id']==q) and sum(r['query_id']==q for r in labels)==112]
    changes=[];lab={(r['query_id'],r['case_id']):r for r in labels};lookup={(n,r['query_id']):r for n,rs in pred['systems'].items() for r in rs}
    for q in pred['query_ids']:
        pos={r['case_id'] for r in labels if r['query_id']==q and r['status']=='JUDGED' and r['grade']>=2}
        for k in (5,10,20):
            a=set(lookup['T1',q]['ranking'][:k])&pos;b=set(lookup['T3',q]['ranking'][:k])&pos
            changes.append({'query_id':q,'k':k,'known_relevant_added':sorted(b-a),'known_relevant_lost':sorted(a-b),'known_relevant_retained':sorted(a&b),'warning':'Only existing judged labels; not complete relevance inventory'})
    write(d/'known_gains_losses.json',{'records':changes})
    positive_ranks=[{'query_id':r['query_id'],'case_id':r['case_id'],'grade':r['grade'],'ranks':{n:lookup[n,r['query_id']]['ranking'].index(r['case_id'])+1 for n in pred['systems']}} for r in labels if r['status']=='JUDGED' and r['grade']>=2]
    write(d/'known_positive_ranks.json',{'records':positive_ranks,'never_a_complete_performance_claim':True})
    write(d/'complete.json',{'evaluation_of_available_predictions_complete':True,'final_test_complete':False,'prediction_seal_sha256':sha(src/'complete.json'),'qrels_sha256':sha(PAYLOAD/'qrels.jsonl'),'question_count':len(pred['query_ids']),'qrel_rows':len(labels),'counts':counts,'full_evaluable_question_count':len(full),'fully_judged_query_ids':full,'no_additional_labels_fabricated':True,'files':{p.name:sha(p) for p in d.iterdir()}})
    print('Existing label coverage',counts,'complete questions',len(full),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['stage4','prepare','infer','evaluate']);p.add_argument('--scratch',type=Path);a=p.parse_args()
    if a.stage=='stage4':stage4()
    elif a.stage=='prepare':prepare()
    elif a.stage=='infer':inference(a.scratch.resolve())
    else:evaluation()
