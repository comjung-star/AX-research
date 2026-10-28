"""Separate evaluator landing page from unblinded analyst comparisons."""
from scripts import blind_pilot_five as p

def main():
    counts=p.read(p.OUT/'pool_counts.json');pred=p.read(p.OUT/'analyst/predictions.json')['systems'];cases=p.read(p.RETR/'case_registry.json')['cases']
    detail={(x['qid'],x['case_id']):x for x in p.read(p.OUT/'analyst/score_details.json')['records']}
    rows=[]
    for method,qs in pred.items():
        for query in qs:
            for rank,cid in enumerate(query['ranking'],1):
                d=detail[query['qid'],cid]
                rows.append({'method':method,'qid':query['qid'],'rank':rank,'case_id':cid,'actual_task':d['actual_task'],'rule_case_recognized':d['rule_case_recognized'],'rule_query_recognized':d['rule_query_recognized'],'rule_strength':d['A_rule_evidence']['mapping_grade'],'semantic_score':d['B_semantic_components']['score'],'combined_score':d['C_combined_score'],'rule_functions':','.join(d['A_rule_evidence']['shared_functions']),'reason':'고정 규칙 근거/동일 필드 임베딩 유사도/고정 결합식의 정렬 결과. 사람 관련 정답이 아닙니다.'})
    p.csvsave('analyst/full_rankings.csv',rows);p.csvsave('analyst/top10_recommendations.csv',[r for r in rows if r['rank']<=10]);p.csvsave('analyst/top5_recommendations.csv',[r for r in rows if r['rank']<=5])
    landing='''# 신규 질문 5개 블라인드 파일럿

현재 상태: **추천 생성·평가 자료 준비 완료 / 사람 채점 대기**. 성능 개선 여부는 아직 판단하지 않았다.

## 먼저 평가할 분께

채점 전에 **evaluator 폴더의 파일만** 열어 주세요. analyst 폴더에는 추천 방식·순위·점수가 있어 먼저 열면 블라인드 평가가 깨집니다. 같은 비공개 저장소의 파일 분리이므로 접근 차단을 뜻하지 않습니다. 여러 평가자에게 보낼 때는 evaluator 파일만 전달하세요.

- [Excel 평가표](evaluator/blind_review.xlsx)
- [CSV 평가표](evaluator/blind_review.csv)
- [쉬운 채점 안내](evaluator/채점안내.md)

## ① 무엇을 검증하는가?

같은 새 질문을 세 가지 프로그램에 주었을 때, 실제로 도움이 되는 사례를 누가 더 잘 찾는지 사람이 확인하려는 준비입니다. 사람이 채점하기 전에는 승자를 정하지 않습니다.

## ② 신규 질문 5개

|질문|확인할 업무|사람 평가 쌍|
|---|---|---:|
'''
    for q in p.CFG['questions']:landing+=f"|{q['qid']}|{q['topic']}|{counts['questions'][q['qid']]['total']}|\n"
    landing+='''
질문 원문은 questions.json과 평가표에 그대로 있습니다. Q14는 기존 예측·제조 질문과 상당 부분 겹치고, 다른 질문도 업무 환경이나 일부 기능이 겹칩니다. 동일한 기존 질문이나 Task 문장을 그대로 포함한 문자열은 없었습니다. 문자열 차이가 의미의 독립성을 증명하지는 않습니다. 의도적으로 미인식 업무를 포함한 목적 표본이며 최종 독립 Test가 아닙니다.

## ③ A/B/C 추천 결과

A는 기존18개 규칙, B는 기존 BGE-M3 필드 임베딩, C는 기존50:50 결합입니다. 원질문만 사용한15개 전체112순위, Top5/10과 근거를 저장했습니다. 규칙·모델·가중치를 바꾸지 않았습니다. 어떤 사례를 각 방식이 골랐는지 보여주는 비교표는 **채점 후 열어 볼** [analyst 보고서](analyst/README.md)에 분리했습니다.

새 관점 생성은 이전과 같은 유료 OpenAI 절차가 필요해 수행하지 않았습니다. 새 질문에 대해 기존 관점을 재활용하거나 임의 관점을 만들지 않았습니다. 새 질문 필드와 원문19개만 로컬 BGE-M3로 인코딩했고 기존112사례와632개 필드 벡터는 재사용했습니다. 추가 API 비용은0입니다.

## ④ 블라인드 평가 준비

총 **103개 질문–사례 쌍**입니다. 질문별 A/B/C Top10을 합쳐 중복을 없앤93쌍과 미인식 사례 점검용10쌍입니다. 추가 사례는 질문마다 합집합 밖에서 고정 B순위가 높은 미인식 사례 최대2개를 고른 것이며 정답이 아닙니다. 모든 방식의Top10을 빠짐없이 포함했습니다.

평가 파일에는 무작위 평가ID, 질문, 사례의 기존 문제 설명, 실제Task, Context, 출처, 빈 점수·의견만 있습니다. 고정 시드20261028로 순서를 섞었습니다. 추천 방식·순위·AI점수·기존Silver·추가표본표시는 넣지 않았습니다. 원 출판물은 이번에 재검증하지 않았습니다.

## ⑤ 내가 해야 할 일

1. Excel 또는 CSV 중 하나만 사용하세요.
2. Excel은 ‘평가표’ 시트 **G열 관련성 점수**, **H열 평가 의견**만 입력하세요.
3. 3=직접 적용 가능, 2=유사 기능으로 응용 가능, 1=일부 관련되지만 차이 큼, 0=무관입니다. 어려우면 ‘판단 보류’를 고르세요.
4. 다른 열과 평가ID는 바꾸지 말고, 다른 파일명으로 저장해 이 대화에 첨부하세요.

점수와 의견은 현재 모두 공란입니다. AI가 사람 점수를 대신 채우지 않았습니다. 공란과 보류를0점으로 바꾸지 않습니다.

## ⑥ 평가 후 확인할 결과

사람 점수2~3을 관련 사례로 보고 Precision@5/10과 등급 기반nDCG@5/10을 계산합니다. 규칙이 놓쳤지만 임베딩이 찾은 관련 사례, 반대로 상위에 나온 무관 사례, 결합 방식의 득실, 미인식33개 사례의 유용성을 확인할 수 있습니다. 기존10질문의Silver와 새 사람점수를 섞지 않습니다.

Precision은TopK 모두 채점됐을 때만 계산합니다. nDCG의이상순위는 **해당 질문의 평가풀 전체**가 채점된 때 그 풀에서 만듭니다. 전체112개 정답 기준nDCG가 아니며, 전체Recall은 계산하지 않습니다. 무관련풀의nDCG는 미정입니다. 미평가가 남으면 정식5질문Macro를 내지 않고 누락과 부분평균의 분모를 별도로 표시합니다.

## ⑦ 결과·실행 기록

질문과 정책은 사전 커밋 e7f14133에 고정했습니다. 소스·설정·모델 파일 해시를 freeze.json에 보존하고, 기존15개 입력과 A/B/C를 그대로 사용했습니다. 새 알고리즘·학습·유료호출·키읽기·새 정답 생성·독립Test 열람은0입니다.

자동 검증은 verification.json, 테스트는 test_results.json, Excel 확인은 workbook_build_check.json, 원격 파일 내용 확인은 publication.json을 참고하세요. 점수 공란인 입력으로 분석기를 실행한 analysis_pending.json에도 현재 지표는 모두 미정으로 남겼습니다.

사람 평가를 마친 뒤 실행 예:

```text
PYTHONPATH=src;.
python -m scripts.blind_pilot_analyze 평가완료.xlsx --output 새_사람평가분석.json
```

출력 파일이 이미 있으면 덮어쓰지 않습니다. 평가 ID 중복·누락, 설명 변경, 범위 밖 점수와 수식을 거부합니다. 실제 사람 평가가 아직 없으므로 성능 개선·일반화 결론은 보류합니다.
'''
    (p.OUT/'README.md').write_bytes(landing.encode('utf-8'))
    analyst=['# 채점 후 열어 보는 A/B/C 추천 비교','','**평가자는 채점 전에 이 문서를 열지 마세요.** 추천 결과이며 사람 정답이 아닙니다. 이 문서를 먼저 본 경우 그 사실을 평가 기록에 남기세요.','','|질문|A 첫 추천|B 첫 추천|C 첫 추천|','|---|---|---|---|']
    for q in p.CFG['questions']:
        analyst.append('|'+q['qid']+'|'+'|'.join(cases[next(x for x in pred[s] if x['qid']==q['qid'])['ranking'][0]]['task'] for s in 'ABC')+'|')
    analyst.extend(['','전체Top5/10은 top5_recommendations.csv / top10_recommendations.csv, 전체112순위는 full_rankings.csv와 predictions.json에 있습니다. score_details.json에 기존규칙의 근거·인식여부·같은필드별 cosine·고정결합점수·실제Task·Context·출처ID를 남겼습니다. evaluation_key.json은 무작위평가ID를 사례/질문/알고리즘순위로 연결합니다. 평가자에게 먼저 전달하지 마세요.','','추천점수는 정답이나 관련 확률이 아닙니다. 사람이 아직 채점하지 않았으므로 5개 질문 모두Precision/nDCG/개선여부는미정입니다. 새 질문들은기존미인식업무의목적표본으로,기존10개Dev와동일모집단/동일정답척도의성능차이를직접계산하지않습니다.','','재현: PYTHONPATH=src;. 에서 python -m scripts.blind_pilot_five run, bundle, python -m scripts.blind_pilot_report, python -m scripts.blind_pilot_verify 순서로실행합니다. 기존사례벡터와같은로컬모델이필요하고다운로드는금지됩니다. 실제채점이시작된평가파일은재생성하지말고복사본을사용하세요. 새벡터NPZ는저장돼있어추론없이다시점수를검산할수있습니다.'])
    (p.OUT/'analyst/README.md').write_bytes(('\n'.join(analyst)+'\n').encode('utf-8'))
    p.save('final_status.json',{'status':'READY_FOR_HUMAN_BLIND_REVIEW','new_queries':5,'candidate_cases':112,'methods':['A','B','C'],'full_rankings':15,'review_pairs':103,'human_graded_pairs':0,'precision_ndcg':'UNDEFINED_PENDING_HUMAN_LABELS','recall':'NOT_COMPUTED_INCOMPLETE_CORPUS_LABELS','paid_api_calls':0,'key_reads':0,'cost_usd':'0.00','new_perspective_generation':False,'sealed_test_access':False,'model_rules_weights_unchanged':True,'blind_scope':'Reviewer workbook/CSV only; analyst files are separate but not access-controlled.'})

if __name__=='__main__':main()
