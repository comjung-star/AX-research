"""Bounded Responses calls, blind judgments, and frozen heldout inference adapter."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import shutil
from decimal import Decimal
from ax_research.heldout import read,write,jsonl,sha
from scripts.stage45_offline import ROOT,PAYLOAD,MODEL
from scripts import validation123_api as A

OUT=ROOT/'docs/heldout-final-resume-2026-11-03'
PRIVATE=Path.home()/'.ax-heldout-resume/20261103'
PRIOR=ROOT/'docs/ax-stage4-stage5-independent-2026-11-03'


def configure():
    A.OUT=PRIVATE;A.OLD=PRIVATE/'inputs'


def prepare():
    OUT.mkdir(exist_ok=False);PRIVATE.mkdir(parents=True,exist_ok=False);(PRIVATE/'inputs/input').mkdir(parents=True)
    shutil.copyfile(PAYLOAD/'questions.jsonl',PRIVATE/'inputs/input/questions.jsonl')
    qs=jsonl(PAYLOAD/'questions.jsonl');old=jsonl(PAYLOAD/'qrels.jsonl');cases=read(ROOT/'docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases'];jobs=[]
    for q in qs:
        for category,status in [('missing','UNJUDGED'),('audit45','JUDGED')]:
            ids=sorted(r['case_id'] for r in old if r['query_id']==q['query_id'] and r['status']==status)
            for start in range(0,len(ids),12):
                chunk=ids[start:start+12];jobs.append({'query_id':q['query_id'],'repeat':len(jobs)+1,'category':category,'payload':{'query_id':q['query_id'],'business_problem':q['text'],'cases':[{'case_id':c,'Problem':cases[c]['problem'],'Task':cases[c]['task'],'Context':cases[c]['context']} for c in chunk]}})
    write(PRIVATE/'jobs.json',{'jobs':jobs})
    configure();bodies=[]
    for q in qs:
        for rep in (1,2,3):bodies.append(A.body('views',q['query_id'],rep))
    for j in jobs:
        A.request_for_review=lambda q,j=j:j['payload'];bodies.append(A.body('review',j['query_id'],j['repeat']))
    maximum=sum((Decimal(len((b['input']+b['instructions']).encode())+512)*Decimal('.125')+Decimal(b['max_output_tokens'])*Decimal('.50'))/1_000_000 for b in bodies)
    from scripts.heldout_run import freeze
    write(OUT/'plan.json',{'base_commit':'58acb10ed8e77f2689cbed1a57c715644a98a3ae','user_confirmed_sufficient_balance':True,'cost403_not_generation_blocker':True,'api_model':A.MODEL,'budget_usd':2,'planned_view_calls':45,'planned_label_calls':len(jobs),'planned_success_upper_usage_usd':str(maximum),'per_attempt_extra_failure_reserve_usd':'.01','budget_enforced_before_each_call':True,'review_prompt_sha256':A.digest(A.REVIEW_SYSTEM),'view_prompt_sha256':A.digest(A.view_system()),'questions_sha256':sha(PAYLOAD/'questions.jsonl'),'original_qrels_sha256':sha(PAYLOAD/'qrels.jsonl'),'original45_immutable':True,'review_jobs_sha256':sha(PRIVATE/'jobs.json'),'label_policy':'same0to3 >=2; ABSTAIN null; source Task quote; original45 preserved, new1635 one-model blind AI-Silver; no Gold claim','audit45':'All45 also blind re-reviewed separately; discrepancies flagged, originals never silently replaced','generation':'query only;1to6;3repetitions; same frozen prompt','mapping':'same fixedC0C1 and50:50; exact existing original and perspective aggregation; no tuning','metric_policy':'full112JUDGED requiredRecallF1nDCG; allcomparedsystems commonquestions; zero positiveR/F1undefined; precision onlyfullyjudgedTopK; three runs averaged withinquestion','test_exposure':'Original predictions and45labels already examined; not untouched Test; no parameter selection','private_artifact_location':str(PRIVATE),'model_environment':freeze(MODEL),'api_code_sha256':sha(Path(__file__))})
    write(OUT/'final_status.json',{'status':'RUNNING','user_balance_confirmation_accepted':True,'no_tuning':True,'human_gold':False})


def call_valid(kind,qid,rep):
    for tag in ('','format_retry'):
        try:return A.call(kind,qid,rep,tag)
        except RuntimeError as e:
            # One explicit retry only for a fully RECEIVED format-invalid response.
            # Never replay HTTP errors, timeouts or otherwise uncertain calls.
            if str(e)!='RECEIVED_BUT_INVALID_NO_AUTOMATIC_RETRY' or tag:raise
    raise RuntimeError('No valid response')


def views(rep):
    configure()
    for q in jsonl(PRIVATE/'inputs/input/questions.jsonl'):call_valid('views',q['query_id'],rep)
    export_ledger()


def judgments():
    assert (PRIVATE/'predictions/complete.json').exists(),'Seal predictions before further labels'
    configure();results=[]
    for j in read(PRIVATE/'jobs.json')['jobs']:
        A.request_for_review=lambda q,j=j:j['payload'];r=call_valid('review',j['query_id'],j['repeat'])
        results.append({'category':j['category'],'result_id':r['id'],'assessments':r['data']['assessments']})
    write(PRIVATE/'judgments.json',{'results':results});export_ledger()


def export_ledger():
    configure();rows=[read(p) for p in (PRIVATE/'api/attempts').glob('*.json')]
    obj={'budget':A.budget(),'calls':rows,'usage_tokens':{k:sum(r.get('usage',{}).get(k,0) for r in rows) for k in ('input_tokens','output_tokens','total_tokens')},'response_and_request_hashes':{p.name:sha(p) for p in (PRIVATE/'api').glob('*.json')},'raw_payloads_private':True,'actual_billing_balance_not_queried':True,'user_confirmation_accepted':True}
    p=OUT/'api_ledger.json';p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def infer():
    configure();from scripts import validation123_multiview as M
    # Build inference-only old-format adapter, without copying any qrels.
    scaffold=PRIVATE/'original';(scaffold/'predictions').mkdir(parents=True,exist_ok=False)
    old=read(PRIOR/'stage5/predictions/rankings.json');systems={'C0':old['systems']['T1'],'C1':old['systems']['T3'],'C1_NO_EMBEDDING':old['systems']['T3_NEUTRAL']}
    write(scaffold/'predictions/rankings.json',{'case_ids':old['case_ids'],'query_ids':old['query_ids'],'systems':systems})
    scratch=ROOT.parent/'AX-stage45-heldout-original-20261103';shutil.copyfile(scratch/'evidence.json',scaffold/'predictions/evidence.json')
    details=read(PRIOR/'stage5/predictions/score_evidence.json')['records'];write(scaffold/'predictions/C1_details.json',{'records':[{'query_id':r['query_id'],'case_id':r['case_id'],'new_rule':r['C1_rule']} for r in details]})
    def load_views():
        paths=[];sources={}
        for rep in (1,2,3):
            for q in jsonl(PRIVATE/'inputs/input/questions.jsonl'):
                prefix=f"views_{q['query_id']}_r{rep}";p=PRIVATE/'api/results'/(prefix+'.json')
                if not p.exists():p=PRIVATE/'api/results'/(prefix+'_format_retry.json')
                r=read(p);A.validate('views',q['query_id'],r['data']);sources[p.name]=sha(p)
                for i,v in enumerate(r['data']['perspectives'],1):paths.append({'query_id':f"p_{q['query_id']}_r{rep}_{i}",'text':v['title']+'\n'+v['description'],'parent_query_id':q['query_id'],'repeat':rep,'perspective':v,'source_result':p.name})
        return paths,sources
    M.OUT=OUT;M.OLD=scaffold;M.load_views=load_views
    M.infer(PRIVATE/'branch_raw',MODEL,PRIVATE/'predictions')
    # Preserve sealed raw inference artifacts locally. Public outputs omit raw Test text.
    public=OUT/'predictions';public.mkdir(exist_ok=False)
    for n in ('rankings.json','branch_rankings.json','branch_scores.jsonl','combined_scores.jsonl','freeze.json','post_freeze.json','access_audit.json'):
        shutil.copyfile(PRIVATE/'predictions'/n,public/n)
    write(public/'complete.json',{'all_four_conditions_complete':True,'private_prediction_seal_sha256':sha(PRIVATE/'predictions/complete.json'),'private_paths_sha256':sha(PRIVATE/'predictions/paths.json'),'private_profiles_sha256':sha(PRIVATE/'predictions/query_profiles.json'),'files':{p.name:sha(p) for p in public.iterdir()},'qrels_read':False,'original_T1_T3_reused_exactly':True})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','views','judgments','infer','ledger']);p.add_argument('--round',type=int,default=1);a=p.parse_args()
    {'prepare':prepare,'views':lambda:views(a.round),'judgments':judgments,'infer':infer,'ledger':export_ledger}[a.stage]()
