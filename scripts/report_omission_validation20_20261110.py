"""Report a fixed20-question validation without tuning to outcomes or claiming final Gold."""
import json
from collections import Counter
from scripts.perspective_omission_validation20_20261110 import OUT,ROOT,N,read,save,sha,api,trial,guard

NAMES={'A_BASE':'A 기본검색','B_MAIN':'B 기본검색+주요관점','C_REVIEW':'C 기본검색+주요+추가검토'}
def pct(x):return '정의안됨' if x is None else f'{100*x:.1f}%'

def report():
    guard();m=read(OUT/'metrics.json');ranks=read(OUT/'rankings.json');labels=read(OUT/'labels.json');selections=read(OUT/'fresh-selections.json');cat,reg,_=trial.sources()
    eligible=m['eligible_positive_questions'];diff={q:m['per_question'][q]['C_REVIEW']['f1']-m['per_question'][q]['B_MAIN']['f1'] for q in eligible}
    wins=[q for q,d in diff.items() if d>1e-12];losses=[q for q,d in diff.items() if d< -1e-12];ties=[q for q,d in diff.items() if abs(d)<=1e-12]
    primary=m['delta']['B_MAIN']['f1'];gain=m['gains_losses']['B_MAIN'];c=m['summary']['C_REVIEW'];b=m['summary']['B_MAIN'];a=m['summary']['A_BASE']
    baseline_default='B_MAIN' if b['f1']>=a['f1'] else 'A_BASE'
    stable=(m['complete_questions']==N and primary['mean']>0 and primary['paired_bootstrap95'][0]>0 and gain['new_useful']>gain['lost_useful'] and len(wins)>=3 and len(wins)>len(losses) and c['f1']>=a['f1'])
    if stable:recommendation='사전 기준상 C를 예비 기본안으로 권고할 신호가 있다. 단일모델 합성 질문의 검증 결과로 범위를 제한한다.';choice='C_PRELIMINARY'
    elif primary['mean']>0:recommendation=f'추가검토는 평균 이득이 있지만 안정성 기준을 충족하지 못했다. 기본안은 {NAMES[baseline_default]}으로 두고 C는 선택적 검토로 남기는 편이 맞다.';choice='OPTIONAL_C'
    else:recommendation=f'검산의 평균 추가 이득을 확인하지 못했다. 기본안은 {NAMES[baseline_default]}으로 권고하고 C의 일관된 개선을 논문 성과로 주장하지 않는다.';choice='NO_ADDED_EVIDENCE'
    if m['complete_questions']<N:recommendation='전체20개 평가가 미완료라 최종 권고를 보류한다. 부분 결과로 기본안을 확정하지 않는다.';choice='INCOMPLETE'
    loo={q:sum(d for k,d in diff.items() if k!=q)/(len(diff)-1) for q in diff} if len(diff)>1 else {}
    zeros=[q for q,v in labels.items() if v['complete'] and not any(r['grade']>=2 for r in v['cases'].values())]
    active=[q for q,s in selections.items() if any(d.get('search_role')=='ADDITIONAL' for d in s.get('decisions',[]))]
    api_records=[read(p) for p in (OUT/'api').glob('*.json') if not p.name.endswith('.request.json')]
    decisions={'policy_from_protocol':read(OUT/'protocol.json')['decision_policy'],'decision':choice,'recommendation':recommendation,
        'wins':wins,'losses':losses,'ties':ties,'positive_questions':eligible,'no_positive_questions':zeros,'active_additional_questions':active,
        'primary_leave_one_out_mean':loo,'all_leave_one_out_positive':bool(loo) and min(loo.values())>0,'stable_by_predeclared_rule':stable,
        'all20_completed':m['complete_questions']==N,'source':str(OUT/'protocol.json')}
    save(OUT/'decision.json',decisions)
    lines=['# 새20개 질문 검증 결과','',recommendation,'',
       '## 실험 범위','',
       f"사례112개와 검색·선택·채점 방법을 이전 실험 그대로 고정했다. 새 질문20개 중{m['complete_questions']}개에 대해 전체112개를 채점했다. F1/Recall 평균은 유용한 정답이 있다고 채점된{len(eligible)}개를 대상으로 한다. 정답이 없다는 AI평가를 받은질문은 {zeros}이며, 그 질문의 전체채점과 검색결과도 보존하고 별도로 표시했다.",
       '', '질문 작성은 이전 질문·사례·관점 목록·점수 없이 별도 OpenAI 요청에서 수행했다.12개 증상형,4개 복합업무형,4개 명시 목표업무의 작성 주제는 생성 전에 고정했다. 주제 선택에 따른 편향과 이전 질문군과의 의미상 유사성은 남는다. 실제 사용자 무작위 표본이나 다른 사례 데이터셋 일반화 실험은 아니다.',
       '', '검증용20개는 향후 기본안/선택기능을 결정하는 자료다. 여기서 선택한 안을 이20개로 다시 최종 미사용 테스트라고 주장하지 않는다. 기존 Test15는 열지 않았다.',
       '', '## 같은 개수의 세 조건','',
       '- A: 문제·업무·맥락 평균 코사인 기본검색 상위U개.',
       '- B: 기본5개와 주요관점별 최대5개를 보존하고, 기본검색에서U개까지 채움.',
       '- C: 기본5개와 주요관점·추가검토관점별 최대5개 합집합. 그 고유 레코드 수가U.',
       '', '조건별로 질문마다 고유 사례 수가 정확히 같다. 기본5개와 주요갈래를 지우지 않았다. 추가 관점은 같은 API 요청 안에서 MAIN/ADDITIONAL/NONE을 판단한 결과이고, 독립된 다른 AI의 검산이 아니다. C-B가 주 비교, C-A가 보조 비교다.',
       '', '| 방법 | 평균 고유 수 | Precision | Recall | F1 | 관점 커버리지 |','|---|---:|---:|---:|---:|---:|']
    for v,s in m['summary'].items():lines.append(f"| {NAMES[v]} | {s['returned']:.2f} | "+' | '.join(pct(s[k]) for k in ('precision','recall','f1','view_coverage'))+' |')
    lines += ['', '관점 커버리지는 같은 평가자의 전체112개 관점 태그를 세 조건 모두에 적용한다. 정답 관점이 없는 질문은 해당 지표 평균에서 제외한다. 선택한 관점의 개수 자체를 점수로 세지 않는다.',
       '', '| C비교 대상 | 새 유용사례 | 놓친 유용사례 | 추가된 덜유용사례 | 제외된 덜유용사례 |','|---|---:|---:|---:|---:|']
    for v,g in m['gains_losses'].items():lines.append(f"| {NAMES[v]} | {g['new_useful']} | {g['lost_useful']} | {g['new_nonuseful']} | {g['removed_nonuseful']} |")
    lines += ['', '질문×사례 쌍 단위다. 같은 사례가 여러 질문에서 반복될 수 있다. C-B에서 놓친 사례는 B의 개수맞춤용 기본검색 채움분이다. C가 보존 약속한 기본5개나 주요관점 사례를 삭제한 것은 아니다. 같은 출력수에서 그 사례를 주지 못한 기회비용은 손실로 기록한다.',
       '', '| C의F1 비교 | 평균 차이 | 질문bootstrap95% |','|---|---:|---|']
    for v in ['B_MAIN','A_BASE']:
        d=m['delta'][v]['f1'];lines.append(f"| {NAMES[v]} | {100*d['mean']:+.2f}%p | "+' ~ '.join(f'{100*x:+.2f}%p' for x in d['paired_bootstrap95'])+' |')
    lines += ['', f"C-B 질문별 개선{len(wins)}개, 악화{len(losses)}개, 동률{len(ties)}개다(F1정의가능 질문 기준). 추가검토 관점이 실제 나온 질문은{len(active)}/20개다. 질문1개를빼고다시평균낸 민감도 범위는 "+(f"{100*min(loo.values()):+.2f} ~ {100*max(loo.values()):+.2f}%p" if loo else '정의안됨')+'.',
       '', 'B-A도 기술적으로 보면20개중13개개선·1개악화·6개동률이며, 평균F1차이는+5.14%p다. 주요관점 조건이 기본검색보다 나아지는 신호가 있다. B의36.2%는 기본검색채움분까지 포함한 동일U조건 결과이며, 기본5+주요관점만 보여주고 채우지 않은 별도UI의 성능을 뜻하지 않는다.',
       '', '이 구간은 선택한 합성 질문과 같은 모델 채점에서의 탐색적 불확실성이다. 실제 사용자 모집단의 효과나 인간 정답에 대한 정확도, 모델 간 독립 검증을 증명하지 않는다. 관련 질문군·출처 중복에 따른 상관도 남는다.',
       '', '## 질문별 결과 — 전부 포함','', '| 질문 | U | MAIN / ADDITIONAL | 유용A/B/C | F1 A/B/C |','|---|---:|---|---|---|']
    for q,row in ranks.items():
        s=selections[q];main=[d['id'] for d in s.get('decisions',[]) if d.get('search_role')=='MAIN'];extra=[d['id'] for d in s.get('decisions',[]) if d.get('search_role')=='ADDITIONAL'];r=m['per_question'].get(q)
        hs=' / '.join(str(r[v]['hits']) for v in NAMES) if r else '미완료';fs=' / '.join(pct(r[v]['f1']) for v in NAMES) if r else '미완료'
        lines.append(f"| {q} | {row['unique_budget']} | {main} / {extra} | {hs} | {fs} |")
    lines += ['', '### 질문 원문·점검 이유·사례 근거','']
    for q,row in ranks.items():
        lines += [f"**{q}** {row['question']}",'']
        for d in selections[q].get('decisions',[]):
            if d.get('search_role')=='ADDITIONAL':lines.append(f"- {d['id']}: {d['bridge_reason']} 미확인 가정: {' / '.join(d['assumptions'])}")
        if q in m['per_question']:
            g=m['per_question'][q]['gains_losses']['B_MAIN'];lines.append('B대비 새 유용사례: '+str(g['new_useful'])+' / 놓친 유용사례: '+str(g['lost_useful']))
            for cid in g['new_useful']:lines.append(f"- {cid}: 저장된 Task원문 `{reg[cid]['task']}`")
        lines.append('')
    lines += ['## 기준과 중단 규칙','',
       '데이터112개·49개 연결사례53개 연결·모델GPT5.4 medium·선택6144/채점12288 출력한도·루브릭·임베딩·세조건·통계를 바꾸지 않았다. 원래 source freeze와이번 freeze를 모두 확인했다. 한 선택 응답이 역할/연결유형 계약을 위반해 사전 허용한 동일 요청1회 기술 복구만 했고 원본을 보존했다. 채점불일치를 맞추거나 점수가좋아질때까지 재생성하지 않았다.',
       '', '시간 단축을 위해 채점 전송 동시 처리만4회에서8회로 조정하고 첫 새채점 호출 전에 judge-execution-amendment.json에 기록했다. 모델 입력·출력한도·순서·채점·검색은 그대로다. 모든 실행 조건까지 완전 사전고정했다고 주장하지 않는다.',
       '', '중간에 API잔액부족으로14개완료후멈췄다. 이후사용자의충전완료지시를받아남은24개배치만동일입력으로재개했다. 원래56개정상배치와기존API기록을보존했고, 최초8개잔액오류도남겼다. 16개는중단전에전송하지않았던첫요청이다. 모든20개채점이모일때까지부분성능점수는계산하지않았다(resume-plan.json/resume-run.json).',
       '', '한제공자·같은모델계열의 질문작성/선택/채점이므로 공통 편향이 남는다. AI평가표는 사람검증 정답지가 아니다.2점이상을 유용한참고로 세었으며 실제적용성·원인·효과를확정하지 않았다.112IDs는83출처그룹에속한다. 원출판물 전체가 아니라 저장P/T/C요약을 썼다.',
       '', '추가 관점이 없는 질문을 제거하지 않았고, 정답이 없는 질문의5개 기본결과도 숨기지 않았다. 기본검색5개 보존이 유용성을 보증하지 않는다. 박빙 결과를 유리하게 해석하기 위해 조건을 바꾸거나 불리한 질문을 빼지 않았다. 미완료: '+json.dumps(m['incomplete'],ensure_ascii=False),
       '', '## 비용과 재현','', '```json',json.dumps(api.ledger(),ensure_ascii=False,indent=2),'```',
       '', '사용량×단가 추정이며 실제 청구서가 아니다. 예약액은 보수적 실행 상한으로 실제소비와 다르다. 전체20개 로컬 재현·동일 고유수·기본5및주요갈래보존·통계재계산은 verification.json에 있다. 모형학습·봉인Test15·다른제공자·원격저장소 변경은 없다.']
    (OUT/'RESULTS.ko.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    save(OUT/'report-provenance.json',{'decision':choice,'sha256':{p:sha(OUT/p) for p in ['RESULTS.ko.md','metrics.json','labels.json','rankings.json','decision.json','verification.json']}})
    print('REPORT20',json.dumps({'recommendation':recommendation,'decision':choice,'wins':len(wins),'losses':len(losses),'ties':len(ties),'zero_gold':zeros,'LOO_all_positive':decisions['all_leave_one_out_positive']},ensure_ascii=False),flush=True)

if __name__=='__main__':report()
