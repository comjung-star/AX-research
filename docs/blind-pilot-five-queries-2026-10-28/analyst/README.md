# 채점 후 열어 보는 A/B/C 추천 비교

**평가자는 채점 전에 이 문서를 열지 마세요.** 추천 결과이며 사람 정답이 아닙니다. 이 문서를 먼저 본 경우 그 사실을 평가 기록에 남기세요.

|질문|A 첫 추천|B 첫 추천|C 첫 추천|
|---|---|---|---|
|Q11|여러 사내 업무 시스템의 지식 통합 검색|Automate routine support-case administration|Book employee annual leave|
|Q12|반품 상품 사진 확인 및 환불 요청 처리|반품 상품 사진 확인 및 환불 요청 처리|반품 상품 사진 확인 및 환불 요청 처리|
|Q13|채용 지원서·증빙 자료 대조 검토|반품 상품 사진 확인 및 환불 요청 처리|직원 신원조회 보고서 검증|
|Q14|임대 전력·온도조절 장비의 고장 위험 예측|임대 전력·온도조절 장비의 고장 위험 예측|임대 전력·온도조절 장비의 고장 위험 예측|
|Q15|여러 사내 업무 시스템의 지식 통합 검색|Repair incomplete payment instructions|Document retrieval and cross-reference support|

전체Top5/10은 top5_recommendations.csv / top10_recommendations.csv, 전체112순위는 full_rankings.csv와 predictions.json에 있습니다. score_details.json에 기존규칙의 근거·인식여부·같은필드별 cosine·고정결합점수·실제Task·Context·출처ID를 남겼습니다. evaluation_key.json은 무작위평가ID를 사례/질문/알고리즘순위로 연결합니다. 평가자에게 먼저 전달하지 마세요.

추천점수는 정답이나 관련 확률이 아닙니다. 사람이 아직 채점하지 않았으므로 5개 질문 모두Precision/nDCG/개선여부는미정입니다. 새 질문들은기존미인식업무의목적표본으로,기존10개Dev와동일모집단/동일정답척도의성능차이를직접계산하지않습니다.

재현: PYTHONPATH=src;. 에서 python -m scripts.blind_pilot_five run, bundle, python -m scripts.blind_pilot_report, python -m scripts.blind_pilot_verify 순서로실행합니다. 기존사례벡터와같은로컬모델이필요하고다운로드는금지됩니다. 실제채점이시작된평가파일은재생성하지말고복사본을사용하세요. 새벡터NPZ는저장돼있어추론없이다시점수를검산할수있습니다.
