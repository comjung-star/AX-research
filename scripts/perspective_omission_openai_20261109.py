"""One dev pass, freeze, fresh three-condition comparison. Paid calls only OpenAI."""
import argparse,json,random
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from scripts import perspective_boundary_openai_20261109 as prior
from ax_research.perspective_omission import review_request,review_schema,normalize_review,build_variants
from ax_research.perspective_panels import query_text

ROOT=prior.ROOT;PREVIOUS=prior.OUT;OUT=ROOT/'docs/perspective-omission-openai-20261109'
api=prior.api;api.OUT=OUT;api.BUDGET=15.
read=prior.read;save=prior.save;sha=prior.sha;prev=prior.prev
CAP=6144;WORKERS=4
def sources():return prior.sources()
def now():return datetime.now(timezone.utc).isoformat()

def execute(jobs,phase):
    """Groups bound outstanding requests; every request is persisted and resumable."""
    a,b=api.PRICES['openai'];extra=0.
    for ident,system,payload,sch,cap in jobs:
        if (OUT/f'api/openai_{ident}.json').exists():continue
        body=api.body('openai',system,payload,sch,cap)
        extra+=(len(json.dumps(body,ensure_ascii=False).encode())*a+cap*b)/1e6
    save(OUT/f'{phase}-budget.json',{'existing_reservation':api.ledger()['reserved_usd'],'planned_reservation':extra,'budget':api.BUDGET})
    if api.ledger()['reserved_usd']+extra>api.BUDGET:raise RuntimeError('Predeclared budget insufficient for entire phase')
    manifest=[]
    for ident,system,payload,sch,cap in jobs:
        item={'id':ident,'system':system,'payload':payload,'schema':sch,'body':api.body('openai',system,payload,sch,cap)}
        save(OUT/f'planned-requests/{ident}.json',item);manifest.append(ident)
    save(OUT/f'{phase}-manifest.json',manifest)
    for i in range(0,len(jobs),WORKERS):
        def work(job):
            ident,system,payload,sch,cap=job
            return api.call('openai',ident,system,payload,sch,cap)
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:records=list(ex.map(work,jobs[i:i+WORKERS]))
        if any(r['status']=='HTTP_ERROR' and any(s in r.get('error','') for s in ('credit_balance','insufficient_quota')) for r in records):
            save(OUT/'credit-stop.json',{'at':now(),'phase':phase,'completed_group':i//WORKERS,'not_submitted':manifest[i+WORKERS:],'no_retries_or_top_up':True})
            raise RuntimeError('API credit exhausted; remaining groups not submitted')

def select_questions(qs,phase):
    cat,_,_=sources();jobs=[]
    for q in qs:
        system,payload=review_request(q['question'],cat);jobs.append((phase+'_'+q['id'],system,payload,review_schema(),CAP))
    execute(jobs,phase);result={}
    for q in qs:
        r=read(OUT/f"api/openai_{phase}_{q['id']}.json")
        try:
            assert r['status']=='VALID_JSON',r.get('error',r['status']);s=normalize_review(q['question'],r['parsed'],cat)
        except Exception as e:s={'question':q['question'],'failed':str(e)}
        result[q['id']]=s
    save(OUT/f'{phase}-selections.json',result);print('SELECTIONS',phase,[(q,[(d['id'],d['search_role']) for d in s.get('decisions',[]) if d['status']=='SELECTED'],s.get('failed','VALID')) for q,s in result.items()],flush=True)
    return result

def scorer():
    cat,reg,profiles=sources();s=prev.scorer()
    for p in [PREVIOUS/'vectors.npz',prior.OLD/'stage6/vectors.npz',OUT/'vectors.npz',OUT/'development-vectors.npz']:
        if p.exists():
            with np.load(p,allow_pickle=False) as a:
                for t,v in zip(a['texts'].tolist(),a['vectors']):s.bank.setdefault(t,v)
    return s

def rank_questions(qs,selections,development=False):
    cat,reg,profiles=sources();s=scorer();texts=[r[f] for r in reg.values() for f in ('problem','task','context')]
    for q in qs:texts += [q['question']]+[query_text(q['question'],c) for c in cat['cards']]
    s.warm(texts);rows={}
    for q in qs:
        question=q['question'];ptc={c:float(np.mean([s.bank[question]@s.bank[r[f]] for f in ('problem','task','context')])) for c,r in reg.items()}
        order=sorted(reg,key=lambda c:(-ptc[c],c));row=build_variants(selections[q['id']],cat,profiles,reg,s,order)
        row.update({'question':question,'base_order':order,'base_scores':ptc});rows[q['id']]=row
    name='development-rankings.json' if development else 'rankings.json';vectors='development-vectors.npz' if development else 'vectors.npz'
    save(OUT/name,rows);used=sorted(set(texts));np.savez_compressed(OUT/vectors,texts=np.array(used),vectors=np.stack([s.bank[t] for t in used]))
    if not development:save(OUT/'rank-freeze.json',{'rankings_sha256':sha(OUT/name),'vectors_sha256':sha(OUT/vectors),'at':now()})
    print('RANKINGS',name,[(q,r['unique_budget'],len(r['main_cases']),len(r['additional_cases'])) for q,r in rows.items()],flush=True)
    return rows

def development():
    qs=read(PREVIOUS/'fresh-questions.json')['questions'];ss=select_questions(qs,'development');rows=rank_questions(qs,ss,True)
    labels=read(PREVIOUS/'labels.json');ms={q:{v:prev.metrics(cases,labels[q]['cases']) for v,cases in row['sets'].items()} for q,row in rows.items()}
    save(OUT/'development-metrics.json',{'per_question':ms,'development_only_not_independent_validation':True,'no_labels_sent_to_selector_or_ranker':True})
    print('DEV_MEANS',{v:prev.avg([m[v]['f1'] for m in ms.values()]) for v in ['A_BASE','B_MAIN','C_REVIEW']},flush=True)

def freeze():
    assert not (OUT/'freeze.json').exists();assert (OUT/'development-metrics.json').exists()
    protocol={'purpose':'Omission-review hypotheses plus preserved basic retrieval; feasibility only, not full trained AX architecture.',
        'selection':'One gpt-5.4 medium request/question cap6144; all4 cards classified MAIN/ADDITIONAL/NONE; additional requires concrete bridge/assumptions and original anchor; no forced count.',
        'retrieval':'Basic: equal mean separate P/T/C BGE cosine all112, top5 preserved. Each MAIN and ADDITIONAL branch uses same existing local query+card definition vs Task, up to5 approved links. Catalog49records53links unchanged; no globalcut or strict application filter.',
        'conditions':{'A_BASE':'PTC topU','B_MAIN':'Basic5+all MAIN branches, fill from same PTC order untilU','C_REVIEW':'Basic5+all MAIN+all ADDITIONAL branches; U=distinct IDs of this union'},
        'fairness':'Exactly equal distinct case counts A/B/C perquestion; every variant includes basic5; no output from MAIN removed inB/C; control fill only changes B baseline slots.',
        'fresh_questions':'8 synthetic source-blind separate OpenAI author request after freeze; six diverse business problems and two explicit target tasks; no actual dataset/card/old questions shown to author.',
        'evaluation':'Separate stateless gpt-5.4 medium12288 calls; same frozen previous relevance rubric, entire112 judged perquestion in deterministic random batches28; evaluator receives no method,roles,ranks or selected cases.',
        'primary_contrast':'C_REVIEW vs B_MAIN (incremental omission value); secondary C_REVIEW vs A_BASE. Relevantgrade>=2; macroP/R/F1,independently judged view coverage; useful gains and losses all reported; no arbitrary global nDCG.',
        'uncertainty':'Question paired bootstrap10000 seed20261109;8 synthetic questions one model family, no human Gold. Complete positive questions only; any incomplete question explicitly listed. No significance/generalization claim.',
        'stop':'One dev8 pass then freeze; one fresh8 run. No favorable-outcome reruns or question editing. Technical failure only at most one identical retry; API credit failures stop new groups.',
        'budget_usd':15,'workers':4,'model':'gpt-5.4','effort':'medium','no_other_providers':True,'no_Test15_or_training':True,
        'source_groups':'112 registry IDs belong to83 source/leakage groups. Count independent groups separately; case IDs are not necessarily independent incidents.',
        'author_settings':['public-service regulation handoff problem','trade document discrepancies','supplier product attribute consistency','supplier onboarding repeated evidence review','clinic referral information plus patient inquiries','expense settlement checks plus staff inquiries','physical image defect inspection only, explicitly exclude document search/chatbots','logistics route optimization only, not document search or inquiry automation']}
    save(OUT/'protocol.json',protocol)
    paths=[Path(__file__),ROOT/'src/ax_research/perspective_omission.py',ROOT/'src/ax_research/perspective_boundary.py',ROOT/'src/ax_research/perspective_panels.py',ROOT/'scripts/panels_full112_api_20261109.py',ROOT/'scripts/panels_full112_experiment_20261109.py',ROOT/'scripts/perspective_boundary_openai_20261109.py',prev.REG,prior.OLD/'stage4/catalog-expanded.json',prior.OLD/'stage4/profiles.json']
    save(OUT/'freeze.json',{'at':now(),'sha256':{str(p.relative_to(ROOT)):sha(p) for p in paths},'protocol_sha256':sha(OUT/'protocol.json'),'fresh_author_called_before_freeze':False});print('FROZEN_BEFORE_AUTHOR',flush=True)
def guard():
    f=read(OUT/'freeze.json');assert all(sha(ROOT/p)==h for p,h in f['sha256'].items());assert sha(OUT/'protocol.json')==f['protocol_sha256']

def author():
    guard();sch=api.obj({'questions':{'type':'array','items':api.obj({'id':api.STR,'question':api.STR})}})
    system='독립 한국어 기업문제 질문 작성자입니다. 자료·관점·기존 질문·실험 방법·점수를 받지 않습니다. 주어진8개 주제에서 각각2~3문장, 자연스러운 기업 AX 참고 사례 요청을 작성하세요. 앞6개는 현재 업무 증상과 복합업무를 설명하고 AI해결책을 미리 지정하지 마세요. 뒤2개는 명시한 목표업무 사례만 요청하세요. 기업 성과나 수치를 만들지 말고 관점/정답/사례ID를 쓰지 마세요.'
    payload={'ids':[f'OQ{i:03}' for i in range(1,9)],'settings':read(OUT/'protocol.json')['author_settings']}
    execute([('author',system,payload,sch,4096)],'author');r=read(OUT/'api/openai_author.json');assert r['status']=='VALID_JSON';qs=r['parsed']['questions'];assert len(qs)==8 and [q['id'] for q in qs]==payload['ids'];save(OUT/'fresh-questions.json',r['parsed']);print('AUTHORED8',flush=True)
def select_fresh():guard();select_questions(read(OUT/'fresh-questions.json')['questions'],'fresh')
def rank():guard();rank_questions(read(OUT/'fresh-questions.json')['questions'],read(OUT/'fresh-selections.json'))

def judge():
    guard();assert not (OUT/'metrics.json').exists();cat,reg,_=sources();ranks=read(OUT/'rankings.json');assert sha(OUT/'rankings.json')==read(OUT/'rank-freeze.json')['rankings_sha256'];jobs=[]
    for q,row in ranks.items():
        ids=sorted(reg);random.Random(20261109+int(q[-3:])).shuffle(ids)
        for i in range(0,112,28):
            payload={'question':row['question'],'perspective_definitions':[{k:c[k] for k in ('id','definition','exclude_if')} for c in cat['cards']],
                'cases':[{'position':j,**{f:reg[c][f] for f in ('problem','task','context')}} for j,c in enumerate(ids[i:i+28])]}
            jobs.append((f'judge_{q}_b{i//28:02}',prev.JUDGE_SYSTEM,payload,prev.judge_schema(),12288))
    execute(jobs,'judge');print('JUDGE_FINISHED',flush=True)

def collect():
    guard();_,reg,_=sources();labels={}
    for q in read(OUT/'rankings.json'):
        ids=sorted(reg);random.Random(20261109+int(q[-3:])).shuffle(ids);cases={};errors=[]
        for i in range(0,112,28):
            try:
                r=read(OUT/f'api/openai_judge_{q}_b{i//28:02}.json');assert r['status']=='VALID_JSON',r.get('error',r['status']);rows=r['parsed']['rows'];assert len(rows)==28 and {x['position'] for x in rows}==set(range(28))
                for x in rows:
                    c=ids[i+x['position']];assert x['grade'] in (0,1,2,3);assert len(set(x['perspectives']))==len(x['perspectives']);cases[c]={**x,'bound_source_task':reg[c]['task']}
            except Exception as e:errors.append({'batch':i//28,'error':str(e)[:300]})
        labels[q]={'cases':cases,'complete':len(cases)==112,'errors':errors}
    save(OUT/'labels.json',labels);print('LABELS',[(q,len(v['cases'])) for q,v in labels.items()],flush=True)

def evaluate():
    guard();ranks=read(OUT/'rankings.json');labels=read(OUT/'labels.json');results={};_,reg,_=sources()
    for q,row in ranks.items():
        if not labels[q]['complete']:continue
        g=labels[q]['cases'];m={v:prev.metrics(cases,g) for v,cases in row['sets'].items()};m['gains_losses']={}
        for control in ['A_BASE','B_MAIN']:
            a,c=set(row['sets'][control]),set(row['sets']['C_REVIEW']);rel={c for c,x in g.items() if x['grade']>=2}
            m['gains_losses'][control]={'new_useful':sorted((c-a)&rel),'lost_useful':sorted((a-c)&rel),'new_nonuseful':sorted((c-a)-rel),'removed_nonuseful':sorted((a-c)-rel)}
        m['source_group_counts']={v:len({reg[c]['leakage_group_id'] for c in cases}) for v,cases in row['sets'].items()};results[q]=m
    eligible=[q for q in results if results[q]['C_REVIEW']['relevant_total']>0]
    summary={v:{k:prev.avg([results[q][v][k] for q in eligible]) for k in ('precision','recall','f1','view_coverage','hits','returned')} for v in ['A_BASE','B_MAIN','C_REVIEW']}
    delta={v:{k:prev.ci([results[q]['C_REVIEW'][k]-results[q][v][k] for q in eligible if results[q]['C_REVIEW'][k] is not None and results[q][v][k] is not None]) for k in ('f1','recall','view_coverage')} for v in ['B_MAIN','A_BASE']}
    gain={v:{k:sum(len(results[q]['gains_losses'][v][k]) for q in results) for k in ('new_useful','lost_useful','new_nonuseful','removed_nonuseful')} for v in ['B_MAIN','A_BASE']}
    save(OUT/'metrics.json',{'per_question':results,'summary':summary,'delta':delta,'gains_losses':gain,'complete_questions':len(results),'eligible_positive_questions':eligible,'incomplete':{q:v['errors'] for q,v in labels.items() if not v['complete']},'cost':api.ledger(),'human_gold':False})
    print('SUMMARY',json.dumps({'summary':summary,'delta':delta,'gain':gain,'complete':len(results)},ensure_ascii=False),flush=True)

def verify():
    guard();ranks=read(OUT/'rankings.json');f=read(OUT/'rank-freeze.json');assert sha(OUT/'rankings.json')==f['rankings_sha256'] and sha(OUT/'vectors.npz')==f['vectors_sha256'];cat,reg,profiles=sources();ss=read(OUT/'fresh-selections.json')
    with np.load(OUT/'vectors.npz',allow_pickle=False) as a:bank=dict(zip(a['texts'].tolist(),a['vectors']))
    def score(p,t,ids):return {c:float(np.clip(bank[t]@bank[reg[c]['task']],-1,1)) for c in ids}
    for q,row in ranks.items():
        question=row['question'];scores={c:float(np.mean([bank[question]@bank[r[f]] for f in ('problem','task','context')])) for c,r in reg.items()};order=sorted(reg,key=lambda c:(-scores[c],c));assert order==row['base_order'];replay=build_variants(ss[q],cat,profiles,reg,score,order);replay.update({'question':question,'base_order':order,'base_scores':scores});assert replay==row
        for v in row['sets']:assert len(row['sets'][v])==len(set(row['sets'][v]))==row['unique_budget']
    before=read(OUT/'metrics.json');evaluate();assert read(OUT/'metrics.json')==before
    save(OUT/'verification.json',{'status':'PASS_ALL8_REPLAYS_EQUAL_UNIQUE_COUNTS_BASIC5_AND_MAIN_BRANCH_PRESERVATION_METRICS','question_count':8,'verification_paid_calls':0,'Test15_opened':False});print('VERIFIED',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['development','freeze','author','select','rank','judge','collect','evaluate','verify']);a=p.parse_args();{'development':development,'freeze':freeze,'author':author,'select':select_fresh,'rank':rank,'judge':judge,'collect':collect,'evaluate':evaluate,'verify':verify}[a.action]()
