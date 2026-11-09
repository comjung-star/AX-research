"""One OpenAI-only development check and sealed fresh paired experiment; no old file mutation."""
import argparse,json,random,hashlib,uuid,os
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
from scripts import panels_full112_api_20261109 as api
from scripts import panels_full112_experiment_20261109 as prev
from ax_research.perspective_boundary import corrected_request
from ax_research.perspective_panels import request_body,schema,normalize,build_panels,query_text

ROOT=api.ROOT;OLD=api.OUT;OUT=ROOT/'docs/perspective-boundary-openai-20261109'
api.OUT=OUT;api.BUDGET=12.
read=api.read
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(tmp,path)
api.save=save
CAP=6144;WORKERS=4
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sources():return read(OLD/'stage4/catalog-expanded.json'),read(prev.REG)['cases'],read(OLD/'stage4/profiles.json')
def concurrent(fn,jobs):
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:return list(ex.map(fn,jobs))
def selected(s):return [d['id'] for d in s.get('decisions',[]) if d['status']=='SELECTED']

def selection(job):
    variant,qid,question=job;cat,_,_=sources()
    if variant=='FIXED':system,payload=corrected_request(question,cat)
    else:
        d=request_body(question,cat);system=d['system']+prev.SOURCE_QUOTE_RULE;payload=json.loads(d['messages'][0]['content'])
    r=api.call('openai',f'{variant}_{qid}',system,payload,schema(),CAP)
    if r['status']!='VALID_JSON':return {'question':question,'failed':r['status']}
    try:return normalize(question,r['parsed'],cat,'ACTUAL_OPENAI_'+variant+'_BOUNDARY_EXPERIMENT')
    except Exception as e:return {'question':question,'failed':str(e),'parsed':r['parsed']}

def development():
    old=read(OLD/'stage5/fresh-questions.json')['questions']
    vals=concurrent(selection,[('FIXED','DEV_'+q['id'],q['question']) for q in old])
    result={q['id']:s for q,s in zip(old,vals)};save(OUT/'development/selections.json',result)
    print('DEVELOPMENT',[(q,selected(s),s.get('failed','VALID')) for q,s in result.items()],flush=True)

def freeze():
    assert not (OUT/'freeze.json').exists()
    assert (OUT/'development/selections.json').exists()
    protocol={'purpose':'Two boundary repairs, OpenAI-only preliminary retrieval evidence. No causal attribution to API failures.',
        'changes':['Pass include/exclude criteria','Separate business work from meta request; out-of-card target must not be substituted'],
        'unchanged':['112 registry','49-case53-link catalog','perview5','no globalcut','BGE Task cosine','conditions as caveats','grade rubric'],
        'models':'gpt-5.4 medium, selector cap6144 both OLD and FIXED (previous run4096); judge12288;4 workers; no other provider calls',
        'fresh':'8 synthetic source-blind OpenAI author questions,4 symptoms2multiwork1physicalprediction1forecast; retain all once; authored only after freeze.',
        'comparisons':'OLD/FIXED on the same new8; all112 cases judged once/question in separate stateless OpenAI calls blinded to algorithms/ranks/selections.',
        'primary_budget':'Perquestion common maximum allowance K=max(5,uniqueOLD,uniqueFIXED); baselineTASK/PTC emitsK; each method may emit fewer. No globalcut or padding. Report counts and empty responses explicitly.',
        'secondary':'Same actualU baseline pervariant if U>0; U0 comparison NA, do not call abstention a retrieval win. Always report baselineTop5 opportunity cost.',
        'metrics':'All complete positive questions macroP/R/F1/coverage, gains/losses, paired question bootstrap10000 seed20261109; all8primary, preauthored6 ordinary questions secondary only.',
        'stop':'One8-question development pass plus2 source-rule clarification checks, then one frozen fresh run. No fresh-outcome-driven reruns or relabeling. At most one identical technical retry only before metrics; no provider substitution.',
        'development_history':'Initial8 exposed scope-narrowing on ordinary questions; clarified case inclusion rules vs query word matching within planned boundary repair; checked affected2 once. Both prompt versions and all outputs kept. No fresh questions used during development.',
        'budget_usd':12,'no_human_gold':True,'same_model_selector_judge_bias':True,'sealed_Test15_opened':False,
        'scope_errors':'Two author-specified explicitOOS tests count as developmental boundary probes, not independent human scope Gold. Semantic relevance still judged over full112.',
        'API_vs_logic':'Previous errorsFQ007/008 were completed valid OpenAI responses, not missing APIs. Claude/Gemini failures limited crosschecking; criterion omission objectively observed; causal contribution not isolated.'}
    save(OUT/'protocol.json',protocol)
    paths=[Path(__file__),ROOT/'src/ax_research/perspective_boundary.py',ROOT/'src/ax_research/perspective_panels.py',ROOT/'scripts/panels_full112_api_20261109.py',ROOT/'scripts/panels_full112_experiment_20261109.py',prev.REG,OLD/'stage4/catalog-expanded.json',OLD/'stage4/profiles.json']
    save(OUT/'freeze.json',{'at':datetime.now(timezone.utc).isoformat(),'sha256':{str(p.relative_to(ROOT)):sha(p) for p in paths},'protocol_sha256':sha(OUT/'protocol.json')})
    print('FROZEN_BEFORE_NEW_QUESTION_AUTHORING',flush=True)
def guard():
    f=read(OUT/'freeze.json');assert all(sha(ROOT/p)==h for p,h in f['sha256'].items());assert sha(OUT/'protocol.json')==f['protocol_sha256']

def author():
    guard();sch=api.obj({'questions':{'type':'array','items':api.obj({'id':api.STR,'question':api.STR})}})
    system='독립적인 한국어 기업 업무문제 질문 작성자입니다. 검색 자료, 관점 목록, 기존 질문, 답/성능/방법을 보지 않습니다. 지정된8개 합성 질문을 각각2~3문장으로 자연스럽게 작성하세요. 질문에 해결책을 미리 넣지 말고 기업 AX 참고 사례와 적용 조건을 요청하세요. 정답·관점·사례ID는 쓰지 마세요.'
    payload={'ids':['BQ001','BQ002','BQ003','BQ004','BQ005','BQ006','BQ007','BQ008'],
       'settings':['고객센터 반복문의와 팀간 전달 지연 증상','금융 신청서의 재작업·입력오류 증상','사업부 규정 확인·승인 대기 증상','수리팀 노하우 인계 단절 증상','총무 문서 항목 정리와 증빙 대조를 함께 명시','온라인상품속성 정리와 고객문의 답변을 함께 명시','문서검색/고객챗봇을 명시제외하고 센서 기반 물리설비 예지보전 사례만 요청','매장 품목별 수요예측/재고배분 실제사례만 요청'],
       'avoid':'실제 기업의 미확인 수치·성과를 만들지 마세요. 앞6개는 업무문제4/복합업무2, 뒤2개는명시한목표업무입니다.'}
    r=api.call('openai','author',system,payload,sch,4096);assert r['status']=='VALID_JSON'
    qs=r['parsed']['questions'];assert len(qs)==8 and [q['id'] for q in qs]==payload['ids'];save(OUT/'fresh-questions.json',r['parsed'])
    print('FRESH_AUTHORED',8,flush=True)
def select_fresh():
    guard();qs=read(OUT/'fresh-questions.json')['questions'];jobs=[(v,q['id'],q['question']) for v in ('OLD','FIXED') for q in qs]
    vals=concurrent(selection,jobs);save(OUT/'fresh-selections.json',{v:{q['id']:vals[i*8+j] for j,q in enumerate(qs)} for i,v in enumerate(('OLD','FIXED'))})
    print('FRESH_SELECTED',[(v,sum('failed' not in x for x in vals[i*8:i*8+8])) for i,v in enumerate(('OLD','FIXED'))],flush=True)

def rank():
    guard();cat,reg,profiles=sources();ss=read(OUT/'fresh-selections.json');qs=read(OUT/'fresh-questions.json')['questions'];s=prev.scorer()
    with np.load(OLD/'stage6/vectors.npz',allow_pickle=False) as a:
        for t,v in zip(a['texts'].tolist(),a['vectors']):s.bank.setdefault(t,v)
    texts=[r[f] for r in reg.values() for f in ('problem','task','context')]
    for q in qs:texts += [q['question']]+[query_text(q['question'],c) for c in cat['cards']]
    s.warm(texts);rows={}
    for q in qs:
        qid=q['id'];question=q['question'];methods={}
        for variant in ('OLD','FIXED'):
            sel=ss[variant][qid]
            if 'failed' in sel:panel={'panels':[],'case_details':{},'failed':sel['failed']}
            else:panel=build_panels(sel,cat,profiles,reg,s)
            panel['limits']='All112 source registry,49 linked records; not complete research architecture.'
            methods[variant]={'panels':panel,'cases':sorted(panel['case_details'])}
        k=max(5,*[len(m['cases']) for m in methods.values()]);task=s('BASE',question,list(reg));ptc={c:float(np.mean([s.bank[question]@s.bank[r[f]] for f in ('problem','task','context')])) for c,r in reg.items()}
        order=lambda scores:sorted(reg,key=lambda c:(-scores[c],c))
        rows[qid]={'question':question,'allowance_K':k,'methods':methods,'task_order':order(task),'ptc_order':order(ptc),
            'sets':{**{v:m['cases'] for v,m in methods.items()},'TASK':order(task)[:k],'PTC':order(ptc)[:k]}}
    save(OUT/'rankings.json',rows);used=sorted(set(texts));np.savez_compressed(OUT/'vectors.npz',texts=np.array(used),vectors=np.stack([s.bank[t] for t in used]))
    save(OUT/'rank-freeze.json',{'rankings':sha(OUT/'rankings.json'),'vectors':sha(OUT/'vectors.npz')});print('RANKED',[(q,{v:len(x) for v,x in r['sets'].items()}) for q,r in rows.items()],flush=True)

def judge():
    guard();assert not (OUT/'metrics.json').exists();cat,reg,_=sources();ranks=read(OUT/'rankings.json');assert sha(OUT/'rankings.json')==read(OUT/'rank-freeze.json')['rankings'];jobs=[]
    for q,row in ranks.items():
        ids=sorted(reg);random.Random(20261109+int(q[-3:])).shuffle(ids)
        for i in range(0,112,28):
            payload={'question':row['question'],'perspective_definitions':[{k:c[k] for k in ('id','definition','exclude_if')} for c in cat['cards']],
               'cases':[{'position':j,**{f:reg[c][f] for f in ('problem','task','context')}} for j,c in enumerate(ids[i:i+28])]}
            jobs.append((f'judge_{q}_b{i//28:02}',payload))
    # Reserve whole planned set before transmitting; no unbounded job queue on budget failure.
    a,b=api.PRICES['openai'];reserve=sum((len(json.dumps(api.body('openai',prev.JUDGE_SYSTEM,p,prev.judge_schema(),12288),ensure_ascii=False).encode())*a+12288*b)/1e6 for _,p in jobs)
    save(OUT/'budget-before-judge.json',{'existing_reserved':api.ledger()['reserved_usd'],'judge_reserved':reserve,'cap':api.BUDGET});assert api.ledger()['reserved_usd']+reserve<=api.BUDGET
    concurrent(lambda j:api.call('openai',j[0],prev.JUDGE_SYSTEM,j[1],prev.judge_schema(),12288),jobs)
    print('JUDGE_FINISHED',flush=True)

def collect():
    guard();_,reg,_=sources();labels={}
    for q in read(OUT/'rankings.json'):
        ids=sorted(reg);random.Random(20261109+int(q[-3:])).shuffle(ids);rs={};errors=[]
        for i in range(0,112,28):
            try:
                r=read(OUT/f'api/openai_judge_{q}_b{i//28:02}.json');assert r['status']=='VALID_JSON',r.get('error',r['status']);rows=r['parsed']['rows'];assert len(rows)==28 and {x['position'] for x in rows}==set(range(28))
                for x in rows:
                    c=ids[i+x['position']];assert x['grade'] in (0,1,2,3);rs[c]={**x,'bound_source_task':reg[c]['task']}
            except Exception as e:errors.append({'batch':i//28,'error':str(e)[:250]})
        labels[q]={'cases':rs,'complete':len(rs)==112,'errors':errors}
    save(OUT/'labels.json',labels);print('LABELS',[(q,len(v['cases'])) for q,v in labels.items()],flush=True)

def evaluate():
    guard();ranks=read(OUT/'rankings.json');labels=read(OUT/'labels.json');results={}
    for q,row in ranks.items():
        if not labels[q]['complete']:continue
        g=labels[q]['cases'];m={s:prev.metrics(pred,g) for s,pred in row['sets'].items()};m['same_actual_count']={}
        for v in ('OLD','FIXED'):
            n=len(row['sets'][v]);m['same_actual_count'][v]={'U':n,'task':prev.metrics(row['task_order'][:n],g) if n else None,'no_retrieval_win_claim_for_U0':n==0}
        m['baseline_top5']=prev.metrics(row['task_order'][:5],g);results[q]=m
    eligible=[q for q in results if results[q]['FIXED']['relevant_total']>0]
    summary={v:{k:prev.avg([results[q][v][k] for q in eligible]) for k in ('precision','recall','f1','view_coverage','hits','returned')} for v in ('OLD','FIXED','TASK','PTC')}
    delta={v:{k:prev.ci([results[q]['FIXED'][k]-results[q][v][k] for q in eligible if results[q]['FIXED'][k] is not None and results[q][v][k] is not None]) for k in ('recall','f1','view_coverage')} for v in ('OLD','TASK','PTC')}
    save(OUT/'metrics.json',{'per_question':results,'summary':summary,'delta':delta,'complete_questions':len(results),'cost':api.ledger(),'human_gold':False,'all8_primary':True,'zero_output_is_not_retrieval_success':True});print('SUMMARY',json.dumps(summary),flush=True)

def verify():
    guard();ranks=read(OUT/'rankings.json');f=read(OUT/'rank-freeze.json');assert sha(OUT/'rankings.json')==f['rankings'] and sha(OUT/'vectors.npz')==f['vectors']
    cat,reg,profiles=sources();ss=read(OUT/'fresh-selections.json')
    with np.load(OUT/'vectors.npz',allow_pickle=False) as a:bank=dict(zip(a['texts'].tolist(),a['vectors']))
    def score(p,t,ids):return {c:float(np.clip(bank[t]@bank[reg[c]['task']],-1,1)) for c in ids}
    for q,row in ranks.items():
        for v in ('OLD','FIXED'):
            if 'failed' in ss[v][q]:continue
            panel=build_panels(ss[v][q],cat,profiles,reg,score);assert [p['cases'] for p in panel['panels']]==[p['cases'] for p in row['methods'][v]['panels']['panels']]
            assert len(row['sets'][v])<=row['allowance_K']
        assert len(row['sets']['TASK'])==len(row['sets']['PTC'])==row['allowance_K']
    before=read(OUT/'metrics.json');evaluate();assert read(OUT/'metrics.json')==before
    save(OUT/'verification.json',{'status':'PASS_FROZEN_SOURCES_16_PANEL_REPLAYS_CASE_BUDGETS_AND_METRICS','api_calls':0,'Test15_opened':False});print('VERIFIED',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['development','freeze','author','select','rank','judge','collect','evaluate','verify']);a=p.parse_args()
    {'development':development,'freeze':freeze,'author':author,'select':select_fresh,'rank':rank,'judge':judge,'collect':collect,'evaluate':evaluate,'verify':verify}[a.action]()
