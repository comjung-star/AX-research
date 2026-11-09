"""Transparent report of equal-count omission-review controls; all outcomes retained."""
import json
from scripts.perspective_omission_openai_20261109 import OUT,ROOT,read,save,sha,api,sources

NAMES={'A_BASE':'A 기본검색만','B_MAIN':'B 기본검색+주요관점','C_REVIEW':'C 기본검색+주요+추가검토관점'}
def pct(x):return '해당없음' if x is None else f'{100*x:.1f}%'
def write():
    m=read(OUT/'metrics.json');ranks=read(OUT/'rankings.json');ss=read(OUT/'fresh-selections.json');labels=read(OUT/'labels.json');cat,reg,_=sources()
    db=m['delta']['B_MAIN']['f1'];da=m['delta']['A_BASE']['f1']
    if m['complete_questions']<8:headline='평가 일부가 미완료여서 전체 효과 검증이 끝나지 않았다.'
    elif db and da and db['mean']>0 and da['mean']>0:headline='같은 사례 수에서 추가 검토 관점의 평균 개선 신호가 나왔다. 소수 합성 질문·단일 모델 채점의 탐색 결과다.'
    elif db and db['mean']>0:headline='추가 검토는 주요관점 조건보다 평균이 높았지만, 기본검색까지 앞선 전반적 개선은 확인되지 않았다.'
    elif da and da['mean']>0:headline='기본검색보다 높은 평균은 관찰했지만, 누락점검의 추가 이득은 확인하지 못했다.'
    else:headline='이번 새 질문에서 누락점검을 통한 평균 성능 개선을 확인하지 못했다.'
    lines=['# 관점 누락 점검 + 기본검색 보존 실험','',headline,'',
       '## 무엇을 바꿨나','',
       '한 번의 OpenAI 요청에서 네 관점 모두를 주요(MAIN), 추가 검토(ADDITIONAL), 보류·제외(NONE)로 판단했다. 추가 검토에는 원문 질문 근거·구체적인 연결 이유·미확인 가정을 요구했다. 독립된 두 번째 AI 검증이 아니라 같은 요청 안의 자기 점검이다. 추가 관점을 반드시 만들게 하거나 모든 관점을 선택하게 하지는 않았다.',
       '', '각 주요/추가 관점에서 승인된 사례를 최대5개씩 찾고 기본검색5개를 항상 보존했다. 적용 세부조건이 미확인이라는 이유로 사례를 걸러내는 강한 필터는 추가하지 않았다. 기본검색은 이전 비교에서 가장 좋았던 별도 Problem/Task/Context 코사인의 동일비중 평균으로 고정했다. 사례별 정렬은 기존 동결BGE Task 코사인을 그대로 썼다. 학습된 신경망·RootCause·Wald·전략추천 전체 모델의 검증은 아니다.',
       '', '## 공정한 비교','',
       '- A: 기본검색 상위U개.',
       '- B: 기본5개와 주요관점별 최대5개를 보존한 뒤, 부족한 개수를 같은 기본검색 순서로 채워U개.',
       '- C: 기본5개와 주요관점·추가관점별 최대5개를 보존. 그 합집합의 고유 레코드 수를U로 정의.',
       '', '따라서 세 조건은 질문마다 정확히 같은 고유 사례 수를 보여준다. 중복 멤버십은 한 사례로 세고 관점 갈래 자체는 유지한다. B에서 주요관점 사례를 탈락시키거나 C의 관점 결과를 전역Top5로 자르지 않았다. C-B는 같은 선택 결과에서 추가 관점 갈래의 효과를 비교한다. 새로운 자기점검이 이전 모델보다 추론능력 자체를 높였다는 인과 실험은 아니다.',
       '', '## 개발 확인과 새 질문을 구분','',
       '직전 실험의8개(BQ001~008)에서 구현을 점검하고 기존 평가 라벨로 개발 수치를 계산했다. 그 라벨은 선택·검색 입력에 주지 않았다. 개발1회 뒤 코드·모델·검색·평가 기준을 고정한 후 새8개(OQ001~008)를 작성했다. 새 질문 작성 요청에는 자료·카탈로그·이전 질문·순위·점수를 주지 않았다. 다만 여섯 업무 분야와 두 명시 목표업무를 지정한 합성 질문이므로 실제 사용자 분포의 무작위 표본이 아니다. 개발BQ004에서 이전에 놓친 AXV24_8e0eaf8a5cb9는 이번에도 A/B/C 모두에 없었다. 모든 알려진 누락을 복구했다고 주장하지 않는다(development-known-omission-check.json).',
       '', f"새8개 중 전체112개 평가 완료는 {m['complete_questions']}/8개이며, 유용한 정답이 있는 질문은 {len(m['eligible_positive_questions'])}개다. 아래 성능 평균은 그 질문들에 대해 계산했다. 정답이 없는 질문은 Recall/F1을 정의하지 않고 별도로 표시한다.",
       '', '## 새 질문 성능','', '| 조건 | 평균 고유 사례 수 | Precision | Recall | F1 | 관점 커버리지 |','|---|---:|---:|---:|---:|---:|']
    for v,s in m['summary'].items():lines.append(f"| {NAMES[v]} | {s['returned']:.2f} | "+' | '.join(pct(s[k]) for k in ('precision','recall','f1','view_coverage'))+' |')
    lines += ['', '관점 커버리지는 동일 채점자가 전체112개에 붙인 관점 태그를 세 조건 모두에 적용했다. 가능한 정답 관점이 없는 질문은 커버리지 평균에서 제외한다. 생성한 관점의 개수 자체를 개선 점수로 세지 않는다.',
       '', '| C 비교대상 | 새로운 유용사례 | 놓친 유용사례 | 추가된 덜유용사례 | 제외된 덜유용사례 |','|---|---:|---:|---:|---:|']
    for v,g in m['gains_losses'].items():lines.append(f"| {NAMES[v]} | {g['new_useful']} | {g['lost_useful']} | {g['new_nonuseful']} | {g['removed_nonuseful']} |")
    lines += ['', '질문×사례 쌍 단위다. C-B에서 놓친유용3개는 모두 비교개수를맞추려고 B에추가한기본검색채움분이다. 보존약속한기본5개나주요관점사례를C가삭제한것은아니다. 그래도같은수의결과에서그유용사례를제공하지못한기회비용이므로손실로기록했다. 같은 실제 사례가 여러 질문에 반복해 셀 수 있다.112개 레코드는83개 출처/누수 그룹에 속하므로 모두 독립 사건이라고 볼 수 없다. 방법별 출처 그룹 수도 metrics.json에 기록했다.',
       '', '| C의F1 비교 | 평균 차이 | 질문 단위 bootstrap95% |','|---|---:|---|']
    for v in ['B_MAIN','A_BASE']:
        d=m['delta'][v]['f1']
        if d:lines.append(f"| {NAMES[v]} | {100*d['mean']:+.1f}%p | "+' ~ '.join(f'{100*x:+.1f}%p' for x in d['paired_bootstrap95'])+' |')
    lines += ['', '8개 합성 질문의 탐색적 구간이다. 여러 지표·조건을 본 확증 검정이나 일반화 증거로 해석하지 않는다. 구간이0을 포함하면 질문에 걸친 일관된 추가 이득은 불확실하다.',
       '', '## 질문별 결과 — 불리한 결과도 포함','', '| 질문 | U | 주요 / 추가검토 관점 | 유용사례 A/B/C | F1 A/B/C |','|---|---:|---|---|---|']
    for q,row in ranks.items():
        sel=ss[q];main=[d['id'] for d in sel.get('decisions',[]) if d.get('search_role')=='MAIN'];extra=[d['id'] for d in sel.get('decisions',[]) if d.get('search_role')=='ADDITIONAL'];r=m['per_question'].get(q)
        hit=' / '.join(str(r[v]['hits']) for v in NAMES) if r else '평가 미완료';score=' / '.join(pct(r[v]['f1']) for v in NAMES) if r else '평가 미완료'
        lines.append(f"| {q} | {row['unique_budget']} | {main} / {extra} | {hit} | {score} |")
    lines += ['', '### 추가 이득의 범위와 남은 실패','',
       'C-B의F1구간은0을 포함하므로 질문에 걸친 일관된 추가 이득은 불확실하다. 유용사례 수는 OQ006만4개 늘었고 OQ002는동률, OQ004는1개줄었다. 이득이 한 질문에 집중됐다. 독립 태그 기준 관점 커버리지도 B73.6%→C69.4%로 낮아 관점 다양성까지 개선했다고 주장하지 않는다.',
       '', 'OQ007은 유용하다고 채점된사례가5개 있어도 A/B/C모두0개를찾았다. OQ008은 채점상유용사례0개라F1평균에넣지않았으며모든결과를보존했다. 질문내 제외문구가 기본검색에 미친 영향은 remaining-failures.json에 가설로만 기록했고, 결과를 본 뒤 재실험하지 않았다.',
       '', '### 질문 원문과 추가검토 근거','']
    for q,row in ranks.items():
        lines += [f"**{q}** {row['question']}",'']
        for d in ss[q].get('decisions',[]):
            if d['search_role']=='ADDITIONAL':lines.append(f"- {d['id']}: {d['bridge_reason']} 확인할 가정: {' / '.join(d['assumptions'])}")
        if q in m['per_question']:
            g=m['per_question'][q]['gains_losses']['B_MAIN'];lines.append('C가B대비 새로 찾은 유용사례: '+str(g['new_useful'])+'; 놓친 유용사례: '+str(g['lost_useful']))
            for c in g['new_useful']:lines.append(f"- {c}: 실제 Task 원문 `{reg[c]['task']}`")
        lines.append('')
    lines += ['## 한계와 종료','',
       '판단2점 이상을 유용한 참고로 계산했다. 실제 적용 가능성이나 성공을 확정하지 않는다. 질문 작성·관점 선택·채점은 모두 같은 OpenAI 모델 계열이며 별도 무기억 요청으로 분리했을 뿐 사람 정답이나 타 제공자 검증이 아니다. 원출판물 전체가 아니라 저장된 P/T/C 요약과 승인된53개 연결을 사용했다. 누락검토 역시 틀릴 수 있고 기본검색5개도 항상 유용하다는 보장은 없다.',
       '', '완료되었지만 정답이 없거나 제공 관점에 맞지 않는 질문도 제거하지 않았다. 기본검색과 같은 결과만 나온 질문을 누락점검의 이득으로 세지 않았다. 나쁜 결과에 맞춰 질문·관점·답을 바꾸거나 평가자끼리 동의할 때까지 재생성하지 않았다. 전체 평가 미완료 내역: '+json.dumps(m['incomplete'],ensure_ascii=False),
       '', 'Test15·모델 학습·다른 제공자 호출·원격 저장소 변경은 없다. 출처 지문·8개 로컬 전체 재현·세 조건의 정확히 같은 고유수·기본5개 및 주요갈래 보존·통계 재계산을 확인했다. 이 확인이 성능/의미 정확성의 완전 검증을 뜻하지는 않는다. 내부 패널의 구버전17-case문구·버전은 공유빌더의 유산 메타데이터다. 실제 범위49개 연결사례·전체112개 기본검색과 구분한다(shared-panel-metadata-note.json).',
       '', '## 사용량 비용','', '```json',json.dumps(api.ledger(),ensure_ascii=False,indent=2),'```',
       '', '이번 실험만의 사용량×공개단가 추정이며 실제 청구서가 아니다. 예약액은 비용 상한을 위한 보수적 금액으로 실제 소비가 아니다. 키는 기록하지 않았다. 요청·응답·실패는 api/, 사전 요청은 planned-requests/, 방법은 protocol.json, 지문은 freeze.json/rank-freeze.json, 검사는 verification.json에 있다.']
    text='\n'.join(lines)+'\n';(OUT/'RESULTS.ko.md').write_text(text,encoding='utf-8')
    save(OUT/'report-provenance.json',{'headline':headline,'complete_questions':m['complete_questions'],'positive_questions':len(m['eligible_positive_questions']),
        'sha256':{p:sha(OUT/p) for p in ['metrics.json','labels.json','rankings.json','RESULTS.ko.md','verification.json']}})
    print('REPORT',headline,flush=True)

if __name__=='__main__':write()
