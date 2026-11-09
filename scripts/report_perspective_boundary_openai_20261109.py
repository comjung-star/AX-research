"""Report the predeclared OpenAI-only boundary experiment, including abstention costs."""
from scripts.perspective_boundary_openai_20261109 import OUT,OLD,read,save,selected,api,sha

def pct(x):return '해당없음' if x is None else f'{100*x:.1f}%'
def run():
    m=read(OUT/'metrics.json');rs=read(OUT/'rankings.json');ss=read(OUT/'fresh-selections.json');labels=read(OUT/'labels.json');dev=read(OUT/'development/selections.json');checks=read(OUT/'development/case-vs-query-clarification.json')
    lines=['# OpenAI 단독 관점 범위 수정 실험','',
       '**실행 중 OpenAI API 잔액 소진 오류가 발생하여 새8개 전체 평가는 미완료다.** 아래 평균은 전체112개 평가가 완료된 일부 질문의 결과이며 전체8개 성능 개선으로 주장하지 않는다. 잔액 오류 확인 뒤 새 전송을 막았으며 충전·다른 모델 대체·오류 재시도는 하지 않았다.',
       '**API 문제와 의미 오류는 구분된다.** 이전 FQ007/008은 OpenAI 응답이 completed/VALID_JSON인 상태에서 잘못된 관점을 선택했다. Claude/Gemini의 호출 불가는 교차 확인을 제한했다. 관점 입력에서 포함·제외 기준이 빠진 사실은 확인됐지만, 그 누락과 메타요청 혼동 각각의 인과 효과는 분리하지 않았다.',
       '', 'FQ006의 별도 기술 오류는 출력 한도였으며 동일 설정 기술 복구로 완료된 기록이 있다. 모델 성능 차이나 다른 제공자를 썼을 때의 효과까지 이번 실험으로 배제하는 것은 아니다.',
       '', '## 수정 및 사전 개발','',
       '이전 자료·카탈로그·벡터·최대관점별5개·참고기준은 유지했다. 실제 선택기 입력에 카드의 include_if/exclude_if를 전달하고, 사례 검색 요청과 실제 업무를 구분하는 설명을 추가했다. 새 필터·새 관점·모델 학습은 없다.',
       '', '기존8개는 수정 개발 자료로만 사용했다. 초기 수정에서 두 예측 질문은 관점을 선택하지 않았다. 일반 업무의 관점이 줄어드는 현상이 있어 사례 분류 기준과 사용자 질문 문구 일치를 구분하는 설명을 명확히 했고, 영향받은2개를 한 번 확인했다. 그 뒤 방법을 고정하고 새 질문을 생성했다. 기존8개를 새로운 검증 성과로 세지 않는다.',
       '', '| 개발 질문 | 초기 수정 선택 | 설명 명확화 후 1회 확인 |','|---|---|---|']
    for q,s in dev.items():lines.append('| '+q+' | '+str(selected(s))+' | '+(str(selected(checks[q])) if q in checks else '재호출하지 않음')+' |')
    lines += ['', '## 새8개 비교','',
       '질문은 방법 고정 뒤 별도·무기억 OpenAI 요청에서 작성했다. 작성자는 실제 자료·카탈로그·순위·기존 질문을 받지 않았다. 다만4개 증상형·2개 복합업무형·2개 구체 예측 업무로 분야를 지정한 합성 질문이다. 광범위한 실제 사용자 질문 표본이 아니다.',
       '', 'OLD와 FIXED 모두 GPT5.4 medium, 출력한도6144, 같은 카탈로그·순위 계산이다. 이전 실험4096과 출력한도가 다른 점은 자원 설정 변경이며 이번 OLD/FIXED 양쪽에는 동일하게 적용했다. 채점은 별도 무기억 OpenAI 호출에서 질문별 전체112개를 수행했다. 채점자에게 방법·선택 관점·검색결과를 주지 않았다. 같은 모델 계열의 편향은 남는다.',
       '', '공통 최대 사례 예산 K=max(5,OLD고유사례수,FIXED고유사례수)로 기준검색을 비교했다. 관점 결과를 전역으로 자르거나 빈 결과를 채워 넣지 않았다. 실제 반환 수가 적을 수 있으므로 같은 실제 개수라고 부르지 않는다. 반환 사례가 있을 때만 같은 실제U 기준검색도 별도로 기록했다. 결과0개를 기준검색0개와 비교해 개선으로 세지 않았다.',
       '', '| 방법 | 평균 실제 반환 수 | Precision | Recall | F1 | 관점커버리지 |','|---|---:|---:|---:|---:|---:|']
    for v,s in m['summary'].items():lines.append('| '+v+' | '+f"{s['returned']:.2f}"+' | '+' | '.join(pct(s[k]) for k in ('precision','recall','f1','view_coverage'))+' |')
    lines += ['', f"전체112개 평가가 완료된 질문은 {m['complete_questions']}/8개다. 평균은 완료 질문 중 유용한 정답이 있는 질문을 대상으로 한다. 정답이 있는데 결과를 내지 않으면0점으로 포함한다. 범위 밖이라고 답하는 능력과 원하는 사례를 찾아주는 능력은 별개다.",
       '', '| 질문 | K | OLD→FIXED 선택 | OLD→FIXED 유용사례 수 | OLD→FIXED F1 | TASK F1 |','|---|---:|---|---|---|---|']
    for q,row in rs.items():
        r=m['per_question'].get(q)
        if r:lines.append(f"| {q} | {row['allowance_K']} | {selected(ss['OLD'][q])} → {selected(ss['FIXED'][q])} | {r['OLD']['hits']} → {r['FIXED']['hits']} | {pct(r['OLD']['f1'])} → {pct(r['FIXED']['f1'])} | {pct(r['TASK']['f1'])} |")
        else:lines.append(f'| {q} | 평가 미완료 | — | — | — | — |')
    lines += ['', '### 범주별 참고 분석','', '| 사전 지정 범주 | OLD F1 | FIXED F1 | TASK F1 |','|---|---:|---:|---:|']
    for title,ids in [('증상형4개',range(1,5)),('복합업무형2개',range(5,7)),('일반업무6개(참고)',range(1,7)),('명시 예측업무2개',range(7,9))]:
        qs=[f'BQ{i:03}' for i in ids if f'BQ{i:03}' in m['per_question']]
        vals=[None if not qs else sum(m['per_question'][q][v]['f1'] for q in qs)/len(qs) for v in ('OLD','FIXED','TASK')]
        total=len(list(ids));lines.append('| '+title+f' (완료{len(qs)}/{total})'+' | '+' | '.join(pct(x) for x in vals)+' |')
    lines += ['', '이 표는 전체8개 주 결과를 대체하지 않는 기술 분석이다. 질문 수가 작고 채점도 한 모델이므로 논문 전체의 성능 증명으로 해석하지 않는다.',
       '', '### FIXED의 F1 차이와 불확실성','', '| 비교대상 | 평균 차이 | 질문 단위 bootstrap95% |','|---|---:|---|']
    for v,x in m['delta'].items():
        d=x['f1']
        if d:lines.append('| '+v+' | '+f"{100*d['mean']:+.1f}%p"+' | '+' ~ '.join(f'{100*y:+.1f}%p' for y in d['paired_bootstrap95'])+' |')
    utility=read(OUT/'partial-utility-audit.json')
    lines += ['', f"평가 완료5개에서 새로 얻은 유용 사례는{utility['new_useful']}개, 놓친 유용 사례는{utility['lost_useful']}개, 제외된 덜유용한 사례는{utility['removed_nonuseful']}개다. 채점되지 않은 두 예측 질문에서 줄어든15개를 모두 덜유용하다고 가정하지 않았다. 상세는 partial-utility-audit.json에 있다."]
    initial=read(OUT/'api-vs-logic.json');fp={v:sum(len(rs[q]['sets'][v]) for q in ('BQ007','BQ008')) for v in ('OLD','FIXED')}
    lines += ['', '마지막2개의 명시 예측 업무에서 반환한 사례 수: '+str(fp)+'. 저자가 정한 범위 검사이므로 사람 정답의 범위 판정 정확도로 부르지 않는다. 실제 유용성은 전체112개 평가 점수를 함께 봐야 한다.',
       '', '## 해석','']
    d=m['delta']['OLD']['f1'];task=m['delta']['TASK']['f1']
    if d and d['mean']>0:lines.append('평가 완료된 일부 새 질문에서 수정 전보다 평균F1이 높았다. 전체8개가 미완료이며 누락 질문의 성격도 다르므로 전체 성능 개선으로 해석하지 않는다.')
    else:lines.append('새 질문에서 수정 전보다 평균F1이 높아졌다는 근거는 나오지 않았다. 범위 오류를 줄이는 수정과 유용한 사례를 더 찾는 개선을 구분해야 한다.')
    if task and task['mean']<=0:lines.append('공통 최대예산 기준에서는 단순 TASK 검색보다 전체 평균F1이 높지 않았다. 범위 밖에서 답변을 보류하는 것을 검색 성공으로 세지 않았다.')
    lines += ['', '관점은현재4개, 연결사례는49개로 한정된다. 다른63개 레코드는 원래 검색 자료에는 있지만 이 관점 경로에 배정되지 않았다. 예측 업무를 적절히 보류하는 것만으로 예측 사례 검색을 제공하게 되는 것은 아니다. 기본검색 경로 또는 추가 관점이 필요한지는 별도 가설이다. 이번 실험에서 사후에 그 경로를 추가하거나 새질문을 고치지 않았다.',
       '', '질문별 원문과 이유는 fresh-questions.json, fresh-selections.json에 있다. API 오류는 의미 평가와 분리해 api/에 보존했다. 검증은 파일·출처·16개 패널 재현·최대사례예산·완료된 부분의 통계 재계산을 뜻하며, 전체 평가·사람 정답·다중모델 검증을 뜻하지 않는다. Test15는 열지 않았다.',
       '', '## 비용 및 종료','', '```json',__import__('json').dumps(api.ledger(),ensure_ascii=False,indent=2),'```',
       '', '사용량×단가 추정이며 실제 청구서와 다를 수 있다. 이 집계는 이번 OpenAI단독 실험만 포함한다. ledger의 attempts에는 호출 전에 차단한8개 예약 파일도 포함되므로 실제 전송 시도51건과 구분한다. 정상응답50건, 잔액오류1건, 전송전차단8건이다. 다른 제공자 호출은0건이다. 새질문을 본 뒤 유리한 답변을 다시 생성하거나 채점을 맞추는 반복은 하지 않았다. 잔액이 확보될 경우 누락된9개 평가 배치만 같은 고정 입력으로 이어갈 수 있도록 저장했다.']
    (OUT/'RESULTS.ko.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    save(OUT/'report-provenance.json',{'results_sha256':sha(OUT/'RESULTS.ko.md'),'metrics_sha256':sha(OUT/'metrics.json'),'only_provider':'openai','scope_probes_case_counts':fp})
    print('REPORT_WRITTEN',flush=True)

if __name__=='__main__':run()
