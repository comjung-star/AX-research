"""Readable Korean reports derived only from saved experimental outputs."""
from scripts import functional_mapping_run as f
from scripts.functional_mapping_evaluate import NAMES

def pct(v):return '평가 불가' if v is None else f'{v*100:.2f}%'

def main():
    result=f.read(f.OUT/'stage4_dev/results.json');macro=result['macro']
    selected=['single_dense__original','three_view_dense__original','single_dense__round_robin','single_dense__mean_rrf','single_dense__original_plus_mean_rrf','H_F','M_O_SINGLE','M_D_SINGLE']
    table=['|방식|F1@5|F1@10|F1@20|','|---|---:|---:|---:|']
    for s in selected:table.append('|'+NAMES[s]+'|'+'|'.join(pct(macro[s][str(k)]['f1']) for k in (5,10,20))+'|')
    primary=['|최종 개수|Precision|Recall|F1|','|---:|---:|---:|---:|']
    for k in (5,10,20):primary.append('|'+str(k)+'|'+'|'.join(pct(macro['M_D_SINGLE'][str(k)][m]) for m in ('precision','recall','f1'))+'|')
    records=f.read(f.OUT/'stage4_dev/mandatory_rank_comparison.json')['records']
    cases=['|Q1 사례|원질문 Single|관점 RRF 회차1|하이브리드 회차1|새 매핑 회차1|','|---|---:|---:|---:|---:|']
    for cid,name in [('AXV2N_0121','도움말센터 답변'),('AXV2N_0124','직원 HR 규정 답변'),('AXV2C_0093_01','제조 불량 원인 분석')]:
        ranks=[next(x['rank'] for x in records if x['system']==s and x['repeat']==rep and x['case_id']==cid) for s,rep in [('single_dense__original',0),('single_dense__mean_rrf',1),('H_F',1),('M_D_SINGLE',1)]]
        cases.append('|'+name+'|'+'|'.join(map(str,ranks))+'|')
    text='''# Query–Case 기능 매핑·최종 추천·개발 성능 비교

실행일: 2026-10-28. 기준 커밋: `cf30b73c0027a355bfd0de9bb181a335fd4a7d0f`.
새 브랜치: `research/query-case-functional-mapping-20261028`.

## ① 전체 연구 결과 요약

**2단계 매핑 → 3단계 최종 후보 생성 → 4단계 개발 자료 비교를 실행했다.**
원문에 적힌 행동과 대상을 일반적인 업무 기능으로 연결하는 규칙 기반 방식을 구현했다.
새 유료 호출이나 학습은 하지 않았다. 이번 방식은 교수님이 제안한 신경망의 완성판이 아니라 설명 가능한 검증용 실험이다.

기존 112개 사례, 10개 문제, 108개 관점과 검색 결과를 재사용했다.
설정과 규칙을 먼저 커밋하고, 13,216개 매핑 및 80개 질문·회차의 최종 순위를 저장·커밋했다.
그 다음 별도 평가기에서만 기존 Silver 정답을 읽었다. 성능을 보고 규칙을 고치지 않았다.

개발 자료에서 성능은 올랐다. 그러나 원질문만 매핑해도 상위 20개 결과는 같은 수준이었다.
따라서 개선 전체를 다중관점의 효과라고 주장할 수 없다.

## ② Stage 2 — 정밀 매핑 결과

18종의 업무 문법을 사용했다. 예를 들어 ‘질문 처리·답변’과 ‘Answer … questions’를 같은 질문응답 기능으로 연결한다.
‘품질’이라는 말만 같다는 이유로 제조 불량 분석을 고객 답변 업무로 연결하지 않는다.
업종이 달라도 수행 기능이 같으면 연결할 수 있다.

비교 항목은 업무 문제, Task, Context, 행동, 대상, 산출물이다.
실제 수행 기능은 **Task의 긍정 구절에서만** 인정한다. Problem의 필요 작업을 실제 구현으로 올리지 않는다.
Context는 적용 조건의 설명에 사용한다. 산출물은 동사에서 정한 기능 유형이며, 실제 산출물의 별도 원문을 확인했다는 뜻은 아니다.

점수 0~4는 규칙 근거의 강도다. 같은 행동·대상 기능이 확인되면 3점이다.
Task의 대상 영역과 추가 Problem/Context 기능 근거도 공유하면 4점이다.
2점은 행동만 부분적으로 겹친 경우, 1점은 대상 영역만 겹친 경우다.
이 점수는 기존 Silver 관련도나 정답일 확률이 아니다. 전체 문제에서 확인되지 않은 기능도 따로 남겼다.

기능을 인식한 범위는 사례 Task 79/112개, 질문·관점 71/118개다.
**33개 사례와 47개 경로는 인식하지 못했다.** 전체 13,216조합 중 7,607개는 UNKNOWN이다.
이를 무관 정답으로 바꾸거나 후보에서 삭제하지 않았다.
원질문 Q5의 기능을 읽지 못했고, 상품 검색어와 데이터의 연결을 데이터 통합으로 읽을 수 있는 등 문법의 한계도 확인했다.

필수 진단 사례의 Q1 전체 점수는 도움말센터 3점, HR 규정 3점, 제조 원인 분석 0점이다.
이 세 사례에서 기대한 방향을 보였다는 뜻이며 독립적인 의미 정확도 검증은 아니다.
사용자가 미리 지정한 사례이므로 완전한 눈가림 시험도 아니다.

[Stage 2 상세](stage2/README.md): `mappings.jsonl`, `query_profiles.json`, `case_profiles.json`, `branch_rankings.json`, `unresolved.json`에 각 관점의 점수, 원문 위치, 기존 검색 순위, 보류 사유를 남겼다.
출처 ID는 기존 자료를 연결하는 표식이며 원 출판물의 사실성을 이번에 재검증한 것은 아니다.

## ③ Stage 3 — 최종 추천 결과

원질문과 각 관점을 따로 비교했다. 전체 문제와 관점의 최고 근거를 함께 사용하며 관점 점수를 더하지 않았다.
기능 근거가 같으면 전체 문제 근거, 관점 근거, 기존 하이브리드 검색 점수 순으로 정렬했다.
따라서 특정 관점에만 맞는 사례도 남길 수 있고, 전체 질문에 대한 설명도 유지한다.

Q1 첫 회차의 상위 5개는 다음과 같다.

1. 결제 기술문의 검색·답변
2. 배달원 음성상담 자동응답
3. 고객 도움말센터 질문응답
4. RV 고객 문의 응대·상담원 인계
5. 직원 HR 질문응답

일부는 기존 Silver 기준의 관련 사례가 아니다. 같은 기능의 후보라는 것과 검증된 유용한 추천이라는 것은 다르다.
주 조건의 상위 20개 출력 600행 중 357행은 3점 미만의 약한 근거로 채워졌다.
`low_support_padding`으로 표시했으며 적합성을 보증하지 않는다.

[Stage 3 상세](stage3/README.md): 모든 질문·3회 반복의 Top-5/10/20, 실제 Task, 연결 관점, 추천 이유, 검색 순위와 주의사항을 `top20_explanations.csv/jsonl`에 저장했다.
전체 112개 후보의 설명도 `recommendations.jsonl`에 보존했다.

## ④ Stage 4 — 성능 비교

**이번 Stage 4는 개발 자료 비교다. 봉인된 독립 Test는 열지 않았다.**

__F1_TABLE__

주 조건의 Precision·Recall·F1은 다음과 같다.

__PRIMARY_TABLE__

Precision 평균은 10개 질문, Recall·F1 평균은 양성이 있는 6개 질문이다.
Q2/Q5/Q7/Q9는 Recall·F1을 계산할 수 없어 빈값으로 유지했다.
동적 조건은 질문별 3회 평균을 낸 뒤 원질문 단위로 평균했다.
F1은 질문별 F1의 평균이며, Macro Precision과 Recall을 다시 결합한 값이 아니다.

주 조건은 상위 20개에서 기존 양성 18쌍을 각 회차 모두 찾았다.
이는 **현재 Silver 기준 Recall 100%**이며 사람 정답 정확도 100%가 아니다.
질문 10개에 각각 20개를 제시하는 200자리 중 양성은 18개여서 Precision은 9%다.
112개 전체 후보에 정답이 있다는 이유가 아니라 실제 최종 Top-20에 포함된 결과로 계산했다.

원질문 Single 대비 상위 20개는 회차당 신규 3쌍, 기존 15쌍 유지, 누락 0이다.
3회 합계로는 신규 9건·유지 45건·누락 0건이며 고유 사례 수와 다르다.
기존 다중관점 하이브리드 대비 30개 질문·회차에서는 신규 19건·유지 35건·누락 0건이다.
반면 상위 5개에서는 원질문 Single의 관련 사례 6건, 상위 10개에서는 3건을 놓쳤다.

원질문만 매핑한 방식의 F1은 45.36% / 32.34% / 23.25%다.
관점을 함께 사용한 방식은 46.10% / 34.01% / 23.25%다.
차이가 작고 상위 20개에서는 같아, 관점 자체의 우월성을 입증한 결과는 아니다.

[Stage 4 상세](stage4_dev/README.md): 18조건·400개 질문/회차·1,200개 Top-K 평가를 저장했다.
전체 수치와 질문별 변동은 `macro_metrics.csv`, `query_run_metrics.csv`, `query_mean_metrics.csv`에 있다.

## ⑤ 실제 사례 분석

__CASE_TABLE__

도움말센터는 하이브리드 2위에서 새 매핑 3위로 한 칸 내렸지만 상위 5개를 유지했다.
HR 규정은 60위에서 15위로 복구됐다. 제조 불량 분석은 50위에서 65위로 내려갔다.
기능 매핑이 모든 관련 사례를 무조건 올린 것은 아니다.

원질문 Single에서 상위 20개 밖이던 은행 고객 질문응답(AXV2C_0092_01), 결제 기술문의 답변(AXV2H_0071_01), HR 규정 응답(AXV2N_0124)이 새로 포함됐다.

실패도 있다. Q1의 고객문의 자율응답(AXV2H_0001_01)과 항공 고객응답(AXV2P2_0060_01)은 원질문 Single의 상위 5개에 있었지만 새 상위 5개에서는 빠졌다.
4점 규칙을 받은 다른 후보와 동점 검색 순서가 앞섰기 때문이다. 이들은 상위 20개에서는 유지됐다.
전체 순위 변화와 근거는 `stage4_dev/rank_changes.csv`, `related_changes.json`, `mandatory_rank_comparison.json`에 있다.

## ⑥ 교수님 피드백 반영 평가

충분한 후보 확보 → 관점별 검색 결과 보존 → 원문 기능 매핑 → 최종 순위의 흐름을 실행했다.
관점별 112개 후보와 검색 경로를 보존했으며, 점수 합산으로 관점 수가 많은 경우를 유리하게 만들지 않았다.

다만 이번은 **비학습 규칙 실험**이다. 교수님이 제안한 Query–Case 신경망이나 FAME-AX 전체 모델의 완성을 뜻하지 않는다.
Root Cause·Strategy·Graph 분석은 이번 범위에 포함하지 않았다.

## ⑦ 남아 있는 문제점과 개선 방향

- 인식하지 못한 사례·관점이 많다. 보류 사례의 행동·대상·산출물을 사람이 검증한 작은 독립 자료로 먼저 측정할 필요가 있다. 이번에 사람 검증은 수행하지 않았다.
- 같은 동작 유형도 목적과 조건이 다를 수 있다. 산출물은 동사에 따른 유형이고 별도의 인용 근거가 아니며, 짧은 Task와 문법의 수식 범위에도 한계가 있다.
- 정해진 추천 수를 채우면 약한 근거의 후보가 많아진다. 후속 연구에서 판단 보류와 추천 개수 축소를 별도로 설계해야 한다.
- 현재 정답은 같은 모델 3회 중앙값 Silver이며 양성 18쌍뿐이다. 규칙 설계자는 과거 결과와 필수 사례를 이미 알았다. 라벨을 매핑 입력에 쓰지 않았어도 완전한 눈가림·일반화 실험은 아니다.
- 학습은 없었으므로 학습/검증 중복은 해당하지 않는다. 그러나 같은 출처의 여러 사례는 존재한다. 후속 학습에서는 질문·출처 그룹을 나눠야 한다. `leakage_audit.json`에 해당 그룹을 저장했다.
- 원질문 매핑만으로도 상위 20개 효과가 같았다. 기능 매핑 효과와 동적 관점의 추가 효과를 다음 검증에서도 구분해야 한다.

## ⑧ 최종 결론

**이번 개발 자료와 기존 Silver 기준에서는 기능 매핑을 적용한 후보 순위가 검색 기준선보다 좋아졌다.**
그러나 실제 관련성을 항상 정확하게 판별하거나 새 질문에서도 성능이 좋아진다는 사실은 입증하지 못했다.
특히 규칙의 의미 정확도와 다중관점의 고유 효과는 추가 검증이 필요하다.

API 호출·키 읽기·새 모델 다운로드·학습·추가 임베딩·추가 비용은 모두 0이다.
기존 데이터·평가·검색·프로토타입과 봉인된 독립 Test를 보존했다.

자동 테스트 23개를 통과했다. 별도 검산은 원문 위치 759개, 매핑 13,216행, 새 순위 80개, 성능 1,200세트와 Macro 162개 값을 확인했다.
핵심 결과 7종은 재실행 해시도 같았다. 이는 구현·계산 검증이며 의미 정답 정확도 검증은 아니다.

### 재현 및 기록

저장소에서 `PYTHONPATH=src;.`를 설정한 뒤 아래 순서로 실행한다.

```text
python -m scripts.functional_mapping_run stage2
python -m scripts.functional_mapping_run stage3
python -m scripts.functional_mapping_evaluate
python -m scripts.functional_mapping_verify
python -m scripts.functional_mapping_report
python -m pytest tests/test_functional_mapping.py tests/test_dense_bm25_candidates.py -q
```

평가기 실행 전 Stage 3 순위가 커밋되어 있어야 한다. 설정은 `configs/functional_mapping_20261028.json`이다.
실행 기록은 `manifest.json`, `verification.json`, `reproducibility.json`, `test_results.json`, `security_scan.json`과 작업일지에 있다.
비밀정보 검사는 알려진 키 패턴과 금지 경로를 검사하며 키 값을 읽지 않는다.

실행 오류는 새 출력의 Windows 줄바꿈과 Git 줄바꿈이 달라 저장 검사에 실패한 건이다.
새 출력의 내용 동일성을 검사하도록 수정하고 결정적 LF로 저장했다. 기존 입력은 계속 바이트 단위로 검사했다.
사전 규칙이나 순위는 바꾸지 않았으며 `execution_repairs.json`에 기록했다.
'''
    text=text.replace('__F1_TABLE__','\n'.join(table)).replace('__PRIMARY_TABLE__','\n'.join(primary)).replace('__CASE_TABLE__','\n'.join(cases))
    (f.OUT/'README.md').write_bytes(text.encode('utf-8'))
    dev=['# Stage 4: 개발 자료 성능 비교','','봉인된 독립 Test가 아니다. P는 10개 질문, R/F1은 양성이 있는 6개 질문의 평균이다. 동적 3회는 질문 안에서 평균한 뒤 Macro를 계산했다. 모든 결과는 기존 Silver 중앙값 3점 이상 기준이다.','','|방식|K|Precision|Recall|F1|','|---|---:|---:|---:|---:|']
    for s in NAMES:
        for k in (5,10,20):dev.append('|'+NAMES[s]+'|'+str(k)+'|'+'|'.join(pct(macro[s][str(k)][m]) for m in ('precision','recall','f1'))+'|')
    dev.extend(['','좋은 결과와 누락 사례를 모두 보존했다. 자세한 해석은 [종합 보고서](../README.md)의 ④~⑧을 참고한다. 질문별 값과 변동은 query_run_metrics.csv와 query_mean_metrics.csv, 순위 변화는 rank_changes.csv, 신규·유지·누락은 related_changes.json, 출처 중복과 한계는 leakage_audit.json에 있다.'])
    (f.OUT/'stage4_dev/README.md').write_bytes(('\n'.join(dev)+'\n').encode('utf-8'))
    f.save('final_status.json',{'stage2_experiment_complete':True,'stage3_experiment_complete':True,'stage4_dev_comparison_complete':True,'mapping_is_untrained_rule_baseline':True,'professor_neural_model_complete':False,'semantic_accuracy_independently_validated':False,'api_calls':0,'key_reads':0,'cost_usd':'0.00','independent_test_access':False,'human_gold':False,'primary':'M_D_SINGLE','primary_macro':macro['M_D_SINGLE'],'unknown_mappings':7607,'low_support_top20_rows':357,'limitation':'Known Dev and same-model Silver; no independent generalization; original-only mapping ties dynamic at K20.'})

if __name__=='__main__':main()
