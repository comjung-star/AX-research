"""Read-only research report from frozen source links, rankings and model judgments."""
import json
from pathlib import Path
from scripts.panels_full112_api_20261109 import OUT,read,ledger,save

def pct(value):return '해당 없음' if value is None else f'{value*100:.1f}%'

def report():
    stage4=read(OUT/'stage4/summary.json');data=read(OUT/'stage6/metrics.json');ranks=read(OUT/'stage6/rankings.json')
    selections=read(OUT/'stage5/fresh-selections.json');summary=data['summary'];a=summary['openai'];b=summary['gemini']
    both=a['complete_questions']==b['complete_questions']==8
    delta=lambda s:s['paired_delta']['TASK']['f1']
    if both and delta(a) and delta(b) and delta(a)['mean']>0 and delta(b)['mean']>0:
        headline='두 모델 채점 모두에서 같은 수의 단일 질문 검색보다 평균 개선 신호가 나왔다. 다만 합성 질문 8개를 쓴 탐색 실험이며 논문 전체의 일반적 성능 개선을 확정하지는 못한다.'
    elif both:
        headline='관점별 사례 검색은 동작했지만, 두 모델 평가에 걸친 일관된 평균 개선은 확인하지 못했다. 유용한 추가 사례와 놓친 사례를 함께 봐야 한다.'
    else:
        headline='관점별 사례 검색은 실행했지만 평가 누락이 있어 두 모델에 걸친 개선 검증은 완료하지 못했다. 완료된 평가와 실패 범위를 구분해 보고한다.'
    lines=['# 4~6단계 결과와 중단 점검','',headline,'',
       '보조 검토 하나가 사용량 한도로 종료됐다. 두 112개 검토 파일과 마지막 점검 파일은 저장되어 있었고, 주 작업에서 형식·원문 인용을 확인했다. 완료되지 않은 단계의 결과를 완료로 취급하지 않았다.','',
       '## 4단계 — 전체 자료의 관점 연결','',
       f"112개×4관점의 448개 조합을 별도 두 번 검토했다. 공통 인정 57개에서 분류 경계 오류 4개를 보류해 **{stage4['unique_linked_cases']}개 사례, {stage4['accepted_links']}개 연결**을 확정했다.",
       '', '| 관점 | 승인 연결 |','|---|---:|']
    names={'P01':'문서·지식 탐색','P02':'정보 추출·구조화','P03':'문서·자료 대조 검토','P04':'문의 응대 부담'}
    for p,n in stage4['per_perspective'].items():lines.append(f'| {p} {names[p]} | {n} |')
    lines += ['', '기존 시범 승인 18개 연결은 유지하고 35개를 추가했다. 22개 검토 불일치는 보류했고, 공통 인정 중 별도의 4개도 보류했다. 네 관점에 배정하지 않은 사례는 63개다. 사례 전체를 배제한 것이 아니라 현재 네 관점의 검색 경로에 연결하지 않은 것이다.',
      '', '보류 4개: 문서 검토/답변 초안 업무에서 검색 수행을 가정한 2개, 설문 주제 요약을 추출·구조화로 본 1개, 차량 카메라 검사를 문서 대조로 본 1개. 모르는 적용 세부 조건 때문에 탈락시킨 것은 아니다.',
      '', '두 검토는 같은 모델 계열이며 과거 배정에 노출됐다. 마지막 검토는 의심 사례를 전달받았다. 사람 정답이나 완전 맹검이 아니다. 원 출판물 전체 대신 저장된 P/T/C 요약을 확인했다.',
      '', '## 5단계 — 실제 질문에서 관점 선택','',
      '초기 예시 6개는 통과했으나 최종 목록 예시 6개는 5개만 인용 검사까지 통과했다. 1개는 올바른 관점 ID를 선택했어도 질문에 없는 추정 조건을 원문 인용처럼 써서 차단됐다. 원문 조건과 추가 확인 항목을 구분하는 설명을 보완했고 해당 예시 1개를 재확인했다. 원래 오류는 보존했다. 이것을 의미 정확도 100%라고 보고하지 않는다.',
      '', '채점 형식 확인에서는 Gemini가 Task 인용란에 Problem 문장을 복사한 오류도 발견했다. 새 질문 개봉 전에 두 채점 모델 모두 인용문을 생성하지 않게 하고, 무작위 사례 위치와 연결된 실제 Task 원문을 프로그램이 직접 붙이도록 했다. 출처 연결은 보장하지만, 모델의 관련성 판단이 옳다는 증거는 별개다.',
      '', f"새 질문 8개 중 선택 계약을 통과한 질문은 {sum('failed' not in s for s in selections.values())}개다. 질문 작성자는 자료·검색 결과를 보지 않았고 주 작업자는 방법 고정 후 내용을 열었다. 다만 4개 증상형, 2개 복합업무형, 1개 명시 제외형, 1개 범위 밖 예측형이라는 작성 범주는 미리 지정했다. 실제 사용자 질문의 무작위 표본이 아니다.",
      '', '중요한 의미 오류도 남았다. FQ008은 재고 수요예측 업무가 아니라 “실제 운영에 적용한 기업 AX 사례”를 찾고 싶다는 요청 자체를 P01 문서검색 업무로 오인했다. FQ007은 물리 설비의 예지보전을 P03 문서·자료 대조로 과도하게 확장했다. 두 질문을 빼거나 결과를 본 뒤 관점을 고치지 않았다. 형식 통과가 의미 정확성을 보장하지 않는 실제 사례다.',
      '', 'FQ006은 첫 응답이 고정 출력 한도4096에 걸려 불완전했다. 사전에 허용한 동일 모델·동일 프롬프트·동일 한도의 1회 기술 복구로 정상 완료했다. 다른 유효 답변이나 평가 불일치는 다시 생성하지 않았다.',
      '', '## 6단계 — 같은 사례 수의 비교','',
      '관점마다 최대 5개를 보존한다. 중복 사례 ID를 한 번 세어 U를 정하고 단일 질문 검색도 U개를 반환한다. TASK는 질문↔Task 코사인, PTC는 별도 Problem/Task/Context 코사인의 동일 비중 평균이다. 학습된 게이트·상호작용 신경망이나 전략 추천 전체 모델을 검증한 것이 아니다.',
      '', '두 채점자는 검색 순위·방법·카탈로그 연결을 받지 않고 각 질문에 대해 전체 112개를 평가한다. 2점 이상을 유용한 참고로 센다. 다른 업무라도 합리적 문제 연결은 인정하고 적용 세부 조건의 미확인은 설명한다. 명시 제외와 원문에 없는 핵심 기능은 인정하지 않는다.',
      '', '| 평가자 | 전체 평가 완료 | 유용한 정답이 있는 질문 | 새 방식 F1 | TASK F1 | PTC F1 | 유용한 추가 / 놓침 (TASK 대비) |', '|---|---:|---:|---:|---:|---:|---:|']
    for provider in ('openai','gemini','intersection','union'):
        s=summary[provider];m=s['macro']
        lines.append(f"| {provider} | {s['complete_questions']}/8 | {s['informative_sameU_questions']} | {pct(m['PANELS']['f1'])} | {pct(m['TASK']['f1'])} | {pct(m['PTC']['f1'])} | {s['useful_new_total']} / {s['useful_lost_total']} |")
    lines += ['', '평균은 평가 완료 질문 중 유용한 정답이 있는 질문을 대상으로 한다. 결과 0개인 질문도 정답이 있으면 0점으로 포함한다. intersection/union은 두 채점의 교집합/합집합 민감도 분석이며 합의 정답이 아니다. 추가·놓침은 질문×사례 쌍 수이므로 같은 사례가 여러 질문에서 다시 셀 수 있다.',
      '', '| 평가자 | 새 방식 Recall | TASK Recall | 새 방식 관점 커버리지 | TASK 관점 커버리지 | F1 차이의 질문 단위 bootstrap95% |','|---|---:|---:|---:|---:|---|']
    for provider in ('openai','gemini'):
        s=summary[provider];m=s['macro'];d=delta(s);interval='평가 없음' if not d else ('표본1개: 구간 해석 불가' if d['n']<2 else ' ~ '.join(f'{x*100:+.1f}%p' for x in d['paired_bootstrap95']))
        lines.append(f"| {provider} | {pct(m['PANELS']['recall'])} | {pct(m['TASK']['recall'])} | {pct(m['PANELS']['view_coverage'])} | {pct(m['TASK']['view_coverage'])} | {interval} |")
    lines += ['', '관점 커버리지는 기준 검색에도 같은 채점자의 관점 태그를 적용했다. 정답 관점이 없는 질문은 커버리지 평균에서 제외한다. 작은 표본의 탐색적 구간이며 여러 지표를 동시에 본 확증 검정으로 해석하지 않는다.',
       '', '관점별 nDCG@5는 `stage6/metrics.json`에 기술 통계로 기록했다. 관점들을 임의의 전역 순위로 합쳐 nDCG를 유리하게 비교하지 않았다. CATALOG_RAW는 동일 연결 목록에서 관점 정의를 검색 문장에 덧붙이지 않은 보조 실험이며, 중복 후 사례 수가 다를 수 있어 같은 U의 주 비교와 구분한다.',
       '', '### 질문별 결과 — 불리한 질문도 포함','', '| 질문 | U | 관점 수 | OpenAI F1 새/TASK | Gemini F1 새/TASK |','|---|---:|---:|---:|---:|']
    for q,row in ranks.items():
        vals=[]
        for provider in ('openai','gemini'):
            v=data['per_question'][provider].get(q)
            vals.append('평가 미완료' if not v else pct(v['PANELS']['f1'])+' / '+pct(v['TASK']['f1']))
        lines.append(f"| {q} | {row['U']} | {len(row['panels']['panels'])} | {vals[0]} | {vals[1]} |")
    strata={'증상형4개':[f'FQ{i:03}' for i in range(1,5)],'복합업무형2개':['FQ005','FQ006'],
            '두 범주의6개(참고)':[f'FQ{i:03}' for i in range(1,7)],'예지보전·수요예측2개':['FQ007','FQ008']}
    lines += ['', '### 사전에 작성 범주를 지정한 질문별 참고 분석','',
        '다음은 범주별 기술 분석이다. 전체8개 주 결과를 대체하지 않고, 유리한6개를 새로운 전체 정답처럼 제시하지 않는다. OpenAI 한 평가자의 합성 질문 결과다.',
        '', '| 작성 범주 | 새 방식 F1 | TASK F1 | PTC F1 |','|---|---:|---:|---:|']
    for name,qs in strata.items():
        qs=[q for q in qs if q in data['per_question']['openai']]
        vals=[None if not qs else sum(data['per_question']['openai'][q][s]['f1'] for q in qs)/len(qs) for s in ('PANELS','TASK','PTC')]
        lines.append('| '+name+' | '+' | '.join(pct(v) for v in vals)+' |')
    lines += ['', '증상형·복합업무형6개는 TASK 대비5개 개선·1개 동률이며, 두 예측 질문은 모두 실패했다. 관점 목록이 지원하는 업무를 다룰 때 유용할 가능성과 범위 판단의 취약성을 동시에 보여준다. 사후 진단이므로 이6개만으로 일반 성능 개선을 주장하지 않는다.',
       '', '추가 유용사례39쌍·놓침23쌍으로 총 유용한 결과 쌍은 늘었는데 질문별 평균 Recall/F1은 낮아질 수 있다. 정답 사례가5개·4개인 두 예측 질문에서 새 방식이0개를 찾은 손실이, 정답이 많은 다른 질문에서 얻은 이득보다 질문 단위 비율에 크게 반영된다. 유리한 집계 방식으로 주 지표를 바꾸지 않았다.',
       '', '같은 선택 관점에서 관점 정의문을 검색 문장에 추가하지 않은 CATALOG_RAW도 결과가 비슷했다. 현재 자료로 정의문 추가 자체의 이득은 주장하지 않는다. 이 보조 조건에도 LLM 관점 선택이 들어가므로 LLM 전체가 불필요하다는 의미도 아니다.']
    lines += ['', '질문 원문 및 선택 이유·미확인 가정: `stage5/fresh-questions.json`, `stage5/fresh-selections.json`. 각 방법의 실제 사례와 출처: `stage6/rankings.json`.',
       '', 'U=0이면 같은 U 비교의 기준 검색도 0개여서 우월성을 주장할 수 없다. 별도로 기록한 TASK Top5를 확인해 단순 거절이 유용한 사례를 숨기지 않았는지 점검한다. 112개 레코드는 83개 출처/누수 그룹에 속한다. U는 독립적인 실세계 사례 수를 보증하지 않는다. 방법별 출처 그룹 수는 rankings에 기록했다.',
       '', '### 평가 불일치와 누락','', '```json',json.dumps(data['judge_disagreement'],ensure_ascii=False,indent=2),'```', '', '평가가 다르다고 유효한 응답을 다시 채점하지 않았다. 기술 실패만 같은 설정으로 최대 한 번 복구할 수 있게 했고, 원래 실패를 보존한다. 누락: `'+json.dumps(data['missing_queries_not_silently_dropped'],ensure_ascii=False)+'`.',
       '', 'Gemini는 실제 실행 중 무료 할당 하루20회 한도를 초과했다. 작게 호출 가능하다는 사전 확인은 전체 실험 할당 확보를 뜻하지 않았다. 미리 제출된 대기 요청까지 진행되어32개 배치 중10개 정상·22개 한도 오류가 남았다. 일일 할당 오류는 재시도하지 않고 다른 모델로 대체하지 않았다. 일부 배치가 빠진 질문을 전체112개 완료로 취급하지 않는다. 부분 결과는 labels.json에 그대로 남긴다.',
       '', 'OpenAI 실행 지연을 줄이기 위해 통계 계산 전에 실행 대기열만 분담했다. 사전 기록의 동시2회에서 추가 작업자4회(잠시 최대6회)로 달라졌다. 모델·질문·프롬프트·순서·출력한도·채점기준·검색결과는 그대로이며, 중복 호출은 원래 파일의 배타적 예약으로 막았다. 실행 변경 기록은 stage6/execution-concurrency-amendment.json에 있다. 모든 실행 조건까지 완전히 사전 고정했다고 주장하지 않는다.',
       '', '## 미흡한 부분과 이 실험의 끝','',
       '현재 결과는 네 관점으로 접근할 수 있는 사례 검색의 작은 탐색 실험이다. 합성 질문·모델 채점·저장 요약·네 관점으로 한정한 목록·출처 중복의 한계가 남는다. 사람이 검증한 정답, 실제 사용자 질문, 미관측 사례로의 일반화, 전략 추천 효과까지 증명하지 않는다.',
       '', '다음 수정 후보는 두 가지로 제한할 수 있다. 첫째, 사례를 찾아달라는 대화 지시와 사용자의 실제 업무문제를 분리한다. 둘째, 관점 카드의 포함·제외 기준을 선택 입력에 전달하고 명시한 목표 업무를 다른 업무로 바꿔 답하지 않게 한다. selector-input-audit.json에서 실제 전달 카드에 include_if/exclude_if가 없음을 확인했다. 이 누락이 오류의 직접 원인인지는 분리 실험하지 않았다. 이는 이번 실패를 보고 나온 후속 가설이며, 같은8개를 다시 맞혀서 새로운 검증 성과로 보고하면 안 된다.',
       '', '봉인 Test15는 열지 않았고 기존 84×30/112×20 라벨을 새 기준 정답으로 돌려 쓰지 않았다. 모델 학습과 원격 저장소 변경은 없다. 이번 실험 종료 후 결과에 맞춰 질문·관점·채점 기준을 고치거나 재채점하지 않는다. 다음 연구는 이번 실패 유형을 근거로 별도 가설과 새 질문을 정해 진행해야 한다.',
       '', '## 비용과 재현','', '```json',json.dumps(ledger(),ensure_ascii=False,indent=2),'```',
       '', '이번 작업의 토큰 사용량에 단가를 적용한 추정 비용이다. Gemini는 무료 할당으로 확인되어 실제 청구액과 다를 수 있다. 예약액은 과다 집행 방지를 위한 보수적 최악 금액이며 실제 청구액이 아니다. 이전 실험의 미확정 전송3건은 이 집계 밖이다. 클로드 잔액 부족 오류와 초기 인용 오류도 api/에 보존했다.',
       '', '고정 방법: `stage5/protocol.json`, 파일 지문: `stage5/freeze.json`, 출력 고정: `stage6/rank-freeze.json`, 재현 확인: `stage6/verification.json`. 검사 19개 및 모든 관점 결과의 로컬 벡터 재현·동일 U·통계 재계산을 확인한다.']
    (OUT/'RESULTS.ko.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    save(OUT/'report-provenance.json',{'headline':headline,'source':'stage6/metrics.json','report_code':str(Path(__file__).relative_to(OUT.parents[1]))})
    print(headline,flush=True)

if __name__=='__main__':report()
