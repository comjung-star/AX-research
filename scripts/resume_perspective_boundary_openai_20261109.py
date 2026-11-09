"""Resume only nine quota-blocked batches; preserve all completed judgments and partial reports."""
import argparse,json,shutil,random
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
from scripts.perspective_boundary_openai_20261109 import OUT,ROOT,read,save,sha,guard,sources,api,prev,evaluate,verify,selected

def prepare():
    guard();plan=read(OUT/'resume-plan.json');assert plan['count']==9
    history=OUT/'pre-resume';history.mkdir(exist_ok=True)
    for name in ['labels.json','metrics.json','verification.json','final-status.json','report-provenance.json','cost-breakdown.json','RESULTS.ko.md','README.ko.md']:
        src=OUT/name;dest=history/name
        if src.exists() and not dest.exists():shutil.copyfile(src,dest)
    receipts={p.name:sha(p) for p in (OUT/'api').glob('*.json') if not p.name.endswith('.request.json')}
    requests=[];a,b=api.PRICES['openai'];reserved=0.
    for item in plan['missing_batches']:
        path=OUT/item['input_path'];assert sha(path)==item['sha256']
        request=read(path);original=read(OUT/f"api/{item['original_id']}.json")
        assert original['status'] in ('HTTP_ERROR','NOT_SENT_CREDIT_BLOCKED')
        expected=api.body('openai',request['system'],request['payload'],request['schema'],12288)
        assert expected==request['body'],'Frozen request must not change'
        ident=item['original_id'].removeprefix('openai_')+'_resume1'
        if not (OUT/f'api/openai_{ident}.json').exists():reserved+=(len(json.dumps(expected,ensure_ascii=False).encode())*a+12288*b)/1e6
        requests.append((item,ident,request))
    current=api.ledger()['reserved_usd'];assert current+reserved<=api.BUDGET
    path=OUT/'resume-execution.json'
    if not path.exists():
        save(path,{'at':datetime.now(timezone.utc).isoformat(),'user_instruction':'Credit recharged; finish grading only.',
            'missing_batches':9,'expected_case_judgments':252,'model':'gpt-5.4','effort':'medium','output_cap':12288,'workers':4,
            'unchanged':['questions','catalog','selections','rankings','source case order','prompts','schemas','label rubric','metrics'],
            'continuation_after_partial_metrics_seen':True,'reason':'Explicitly authorized continuation of credit-blocked or unattempted labels, not quality-driven regrading.',
            'existing_api_receipt_hashes':receipts,'existing_reserved_usd':current,'additional_reserved_usd':reserved,'budget_usd':api.BUDGET})
    return requests

def run():
    requests=prepare();stopped=False
    # A first missing actual evaluation also confirms recharge; no extra test call.
    for offset in range(0,len(requests),4):
        group=requests[offset:offset+4]
        def work(job):
            item,ident,r=job
            return api.call('openai',ident,r['system'],r['payload'],r['schema'],r['body']['max_output_tokens'])
        with ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(work,group))
        if any(r['status']=='HTTP_ERROR' and ('credit_balance' in r.get('error','') or 'insufficient_quota' in r.get('error','')) for r in results):
            stopped=True;break
    original=read(OUT/'resume-execution.json');assert all(sha(OUT/'api'/p)==h for p,h in original['existing_api_receipt_hashes'].items())
    save(OUT/'resume-run.json',{'finished_at':datetime.now(timezone.utc).isoformat(),'stopped_for_quota':stopped,
        'existing_receipts_unchanged':True,'results':{ident:(read(OUT/f'api/openai_{ident}.json')['status'] if (OUT/f'api/openai_{ident}.json').exists() else 'NOT_ATTEMPTED') for _,ident,_ in requests},'cost':api.ledger()})
    print('RESUME_FINISHED',flush=True)

def collect():
    guard();_,reg,_=sources();rs={};ranks=read(OUT/'rankings.json');plan=read(OUT/'resume-plan.json')
    resumed={x['original_id']:x for x in plan['missing_batches']}
    for q in ranks:
        ids=sorted(reg);random.Random(20261109+int(q[-3:])).shuffle(ids);cases={};errors=[]
        for i in range(0,112,28):
            ident=f'openai_judge_{q}_b{i//28:02}';path=OUT/f'api/{ident}.json'
            try:
                response=read(path)
                if ident in resumed:
                    path=OUT/f'api/{ident}_resume1.json';response=read(path)
                    assert read(path.with_name(path.stem+'.request.json'))==read(OUT/resumed[ident]['input_path'])
                assert response['status']=='VALID_JSON',response.get('error',response['status'])
                rows=response['parsed']['rows'];assert len(rows)==28 and {r['position'] for r in rows}==set(range(28))
                for r in rows:
                    c=ids[i+r['position']];assert r['grade'] in (0,1,2,3)
                    assert len(r['perspectives'])==len(set(r['perspectives']))
                    cases[c]={**r,'bound_source_task':reg[c]['task']}
            except Exception as e:errors.append({'batch':i//28,'error':str(e)[:250]})
        rs[q]={'cases':cases,'complete':len(cases)==112,'errors':errors}
    old=read(OUT/'pre-resume/labels.json')
    assert all(rs[q]['cases'][c]==row for q,v in old.items() for c,row in v['cases'].items()),'No earlier valid judgment may change'
    save(OUT/'labels.json',rs);print('FINAL_LABEL_COUNTS',[(q,len(v['cases'])) for q,v in rs.items()],flush=True)

def pct(v):return '해당없음' if v is None else f'{100*v:.1f}%'

def report():
    m=read(OUT/'metrics.json');labels=read(OUT/'labels.json');ranks=read(OUT/'rankings.json');ss=read(OUT/'fresh-selections.json');audit={};gained=lost=removed_bad=0
    for q,row in ranks.items():
        if not labels[q]['complete']:continue
        a,b=set(row['sets']['OLD']),set(row['sets']['FIXED']);g=labels[q]['cases']
        new=[c for c in b-a if g[c]['grade']>=2];gone=[c for c in a-b if g[c]['grade']>=2];bad=[c for c in a-b if g[c]['grade']<2]
        audit[q]={'new_useful':new,'lost_useful':gone,'removed_nonuseful':bad};gained+=len(new);lost+=len(gone);removed_bad+=len(bad)
    save(OUT/'completed-utility-audit.json',{'new_useful':gained,'lost_useful':lost,'removed_nonuseful':removed_bad,'details':audit})
    lines=['# OpenAI 단독 실험 — 누락 평가 재개 후 전체 결과','',
       f"새 질문8개 중 {m['complete_questions']}개의 전체112개 사례 채점을 완료했다. 기존23개 성공 배치를 보존하고 누락9개 배치만 동일 요청으로 이어갔다. 질문·관점·검색결과·모델·추론설정·출력한도·채점기준은 바꾸지 않았다. 초기 부분 보고서는 pre-resume/에 보존했다.",
       '', '원래 관점 오류FQ007/008은 정상 완료된 OpenAI 응답에서 발생했다. 이번 실험 중단은 별도로 실제 API 잔액 소진에 의한 것이다. 두 원인을 섞지 않는다.',
       '', '## 전체8개 결과','', '| 방법 | 평균 실제 반환 수 | Precision | Recall | F1 | 관점 커버리지 |','|---|---:|---:|---:|---:|---:|']
    names={'OLD':'수정 전 관점 방식','FIXED':'수정 후 관점 방식','TASK':'단순 Task 검색','PTC':'Problem/Task/Context 평균 검색'}
    for v,s in m['summary'].items():lines.append(f"| {names[v]} | {s['returned']:.2f} | "+' | '.join(pct(s[k]) for k in ('precision','recall','f1','view_coverage'))+' |')
    lines += ['', '주 비교는 질문별 공통 최대 사례 예산K=max(5,수정전고유수,수정후고유수)다. 반환을 보류해 실제 사례 수가 적을 수 있으며 같은 실제 출력 수라고 주장하지 않는다. 실제U를 맞춘 보조 결과는 metrics.json에 있다. 결과0개를 기준검색0개와 비교해 성공으로 세지 않았다.',
       '', '| 질문 | 수정 전→후 관점 | 수정 전→후 유용사례 | 수정 전→후 F1 | Task F1 |','|---|---|---|---|---|']
    for q,row in ranks.items():
        r=m['per_question'].get(q)
        if r:lines.append(f"| {q} | {selected(ss['OLD'][q])} → {selected(ss['FIXED'][q])} | {r['OLD']['hits']} → {r['FIXED']['hits']} | {pct(r['OLD']['f1'])} → {pct(r['FIXED']['f1'])} | {pct(r['TASK']['f1'])} |")
    lines += ['', '## 해석','', f'수정 후 새로 얻은 유용 사례는{gained}개, 놓친 유용 사례는{lost}개, 제외된 덜유용한 사례는{removed_bad}개다. 모두 질문×사례 쌍 단위이며 한 OpenAI 채점자의 판단이다.',
       '', '수정은 범위 밖 두 예측 질문에 억지 관점을 붙이는 행동을 멈췄다. 하지만 원하던 예측 사례를 찾아준 것은 아니다. 관점4개에 배정된49개 레코드만으로는112개 전체 업무 범위를 지원하지 못한다. 기본검색으로 돌아가는 경로나 추가 관점은 이번 실험에 사후로 넣지 않았다.',
       '', '다섯 질문의 결과는 수정 전후 완전히 같고, 나머지세 질문은 일부 또는 전체 관점이 줄었다. 새 방식의 사례 집합은 모두 수정 전의 부분집합이므로 이번 수정으로 새로운 유용 사례가 추가됐다고 주장할 수 없다. 범위 오류 예방과 사례 발견 개선을 구분해야 한다.',
       '', '### 사전에 지정한 일반업무6개 — 참고 분석','', '| 방법 | F1 | Recall |','|---|---:|---:|']
    for v in ('OLD','FIXED','TASK','PTC'):
        qs=[f'BQ{i:03}' for i in range(1,7) if f'BQ{i:03}' in m['per_question']]
        f=sum(m['per_question'][q][v]['f1'] for q in qs)/len(qs);r=sum(m['per_question'][q][v]['recall'] for q in qs)/len(qs)
        lines.append(f'| {names[v]} | {pct(f)} | {pct(r)} |')
    lines += ['', '이6개 분석은 전체8개 주 결과를 대체하지 않는다. 합성 질문·같은 모델 계열의 작성/선택/채점·사람 정답 없음·112개가83개 출처그룹에 속하는 한계가 있다. 개선의 일반화나 다중모델 검증을 완료했다고 말하지 않는다.',
       '', '### 수정 후 F1 차이의 불확실성','', '| 비교대상 | 평균 차이 | 질문 bootstrap95% |','|---|---:|---|']
    for v,vals in m['delta'].items():
        d=vals['f1'];lines.append(f"| {names[v]} | {100*d['mean']:+.1f}%p | "+' ~ '.join(f'{100*x:+.1f}%p' for x in d['paired_bootstrap95'])+' |')
    lines += ['', '탐색적 구간이며 여러 지표를 본 확증 검정으로 해석하지 않는다. 재개 전에 부분 점수를 이미 확인한 사실도 숨기지 않는다. 기존 성공 응답을 재생성하지 않고 누락된 평가만 채웠다.',
       '', '## 비용·재현','', '```json',json.dumps(api.ledger(),ensure_ascii=False,indent=2),'```',
       '', '총 사용량×단가 추정이다. 이전 ledger의 미전송차단8개도 기록 개수에 들어가므로 실제 시도 수와 구분한다. 이번 재개 비용은 resume-final-status.json의 incremental_cost_usd를 확인한다. 원래 잔액 오류와 미전송 기록을 덮어쓰지 않았다.',
       '', 'freeze.json 및 rank-freeze.json 확인,16개 패널 로컬 재현,공통 최대예산 확인,기존유효채점불변,전체896개 채점 출처 확인,통계 재계산을 수행했다. Test15·학습·원격 저장소 변경은 없다.']
    (OUT/'RESULTS-completed.ko.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    before=read(OUT/'pre-resume/metrics.json')['cost']['known_cost_usd'];now=api.ledger()
    originals=read(OUT/'resume-execution.json')['existing_api_receipt_hashes'];assert all(sha(OUT/'api'/p)==h for p,h in originals.items())
    status={'complete_questions':m['complete_questions'],'case_judgments':sum(len(v['cases']) for v in labels.values()),
        'existing_api_records_unchanged':True,'incremental_cost_usd':now['known_cost_usd']-before,'total_cost':now,
        'running_requests':0,'result':'RESULTS-completed.ko.md','human_or_multiple_model_gold':False,
        'source_hashes':{p:sha(OUT/p) for p in ['metrics.json','labels.json','RESULTS-completed.ko.md','verification.json']}}
    save(OUT/'resume-final-status.json',status);print('COMPLETE_SUMMARY',json.dumps({'summary':m['summary'],'delta':m['delta'],'utility':{'new':gained,'lost':lost,'removed_nonuseful':removed_bad},'status':status},ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['run','finish']);a=p.parse_args()
    if a.action=='run':run()
    else:collect();evaluate();verify();report()
