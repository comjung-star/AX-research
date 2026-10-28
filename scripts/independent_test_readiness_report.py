"""Metadata-only gate audit and existing-result reports. NEVER runs retrieval/Test."""
import csv
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];CONFIG=ROOT/'configs/independent_test_readiness_20261028.json'
CFG=json.loads(CONFIG.read_text(encoding='utf-8-sig'));OUT=ROOT/CFG['output']
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as s:
        for block in iter(lambda:s.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
def save(name,d):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def text(name,s):(OUT/name).write_bytes(s.encode())
def csvsave(name,rows):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as s:
        w=csv.DictWriter(s,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf-8').strip()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sem=ROOT/'docs/query-case-semantic-mapping-2026-10-28';publication=ROOT/'docs/query-case-semantic-mapping-report-2026-10-28';pilot=ROOT/'docs/blind-pilot-five-queries-2026-10-28'
    config=read(ROOT/CFG['semantic_config'])
    frozen_paths=[ROOT/p for p in [CFG['case_registry'],CFG['semantic_config'],CFG['rules_config'],'src/ax_research/functional_mapping.py','src/ax_research/semantic_mapping.py','src/ax_research/retrieval/bm25.py','scripts/blind_pilot_five.py','scripts/openai_triplicate_search.py','docs/stage123-openai-triplicate-2026-10-27/embeddings.npz','docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz','docs/query-case-semantic-mapping-2026-10-28/mapping/case_profiles.json','docs/query-case-semantic-mapping-2026-10-28/preregistration.json']]
    frozen={}
    for p in frozen_paths:
        rel=p.relative_to(ROOT).as_posix();old=subprocess.check_output(['git','show',CFG['base_commit']+':'+rel],cwd=ROOT)
        assert p.read_bytes().replace(b'\r\n',b'\n')==old.replace(b'\r\n',b'\n')
        frozen[rel]=sha(p)
    model=(ROOT/config['model_path']).resolve();models={n:sha(model/n) for n in read(sem/'preregistration.json')['model_sha256']}
    assert models==read(sem/'preregistration.json')['model_sha256']
    refs={}
    for branch,expected in CFG['source_refs'].items():
        actual=git('ls-remote','origin','refs/heads/'+branch).split()[0];assert actual==expected
        subprocess.run(['git','merge-base','--is-ancestor',expected,CFG['base_commit']],cwd=ROOT,check=True)
        refs[branch]=actual
    freeze={'algorithm_snapshot_complete':True,'executable_test_evaluation_protocol_complete':False,'reason':'No identified independent Test manifest/queries/qrels/schema; cannot finalize relevance threshold without metadata.','source_refs':refs,'frozen_files_sha256':frozen,'local_model_sha256':models,'settings':config,'config_sha256':sha(CONFIG),'preflight_commit':git('log','-1','--format=%H','--',str(CONFIG.relative_to(ROOT))),'test_question_or_label_payload_opened':False,'test_inference_executed':False}
    save('freeze_snapshot.json',freeze)
    # Filename/stat inventory only. Do not open any candidate question/qrel payload.
    scopes=[ROOT/x for x in ('data','experiments','configs','docs','.local')]+[ROOT.parent/'AX-prototype/.local']
    candidates=[];inventory=[]
    pattern=re.compile(r'(^|[/_.-])(test|testset|heldout|holdout|sealed|independent)([/_.-]|$)',re.I)
    payload=re.compile(r'(test|heldout|holdout|sealed).*(queries|questions|qrels|labels|manifest)|(queries|questions|qrels|labels).*(test|heldout|holdout)',re.I)
    for scope in scopes:
        n=0
        if scope.exists():
            for folder,dirs,files in os.walk(scope,followlinks=False):
                dirs[:]=[d for d in dirs if d not in ('node_modules','.git','.venv','__pycache__')]
                dirs[:]=[d for d in dirs if (Path(folder)/d).resolve()!=OUT.resolve()]
                for name in files:
                    p=Path(folder)/name;n+=1;rel=os.path.relpath(p,ROOT).replace('\\','/')
                    dedicated_scope=any(v.lower() in ('test','testset','heldout','holdout','sealed','independent_test') for v in Path(rel).parts)
                    if pattern.search(name) or dedicated_scope:candidates.append({'path':rel,'bytes':p.stat().st_size,'modified_ns':p.stat().st_mtime_ns,'payload_name_candidate':bool(payload.search(name)),'test_question_or_label_payload_opened':False})
        inventory.append({'root':os.path.relpath(scope,ROOT).replace('\\','/'),'exists':scope.exists(),'file_count':n})
    readiness=read(ROOT/'data/v2_5/research/readiness.json');pilot_state=read(pilot/'final_status.json')
    named=[c for c in candidates if c['payload_name_candidate']]
    # A filename match alone is never permission to treat a file as unused Test.
    gate={'status':'BLOCKED_INDEPENDENT_TEST_NOT_IDENTIFIED','checked_scope':'Three specified latest GitHub branches and listed local metadata roots; not proof no Test exists elsewhere.','metadata_roots':inventory,'test_named_paths':candidates,'question_qrel_manifest_name_candidates':named,'historical_readiness':{'source':'data/v2_5/research/readiness.json','heldout_test_queries':readiness['heldout_test_queries'],'heldout_test_ready':readiness['ready']['heldout_test'],'future_reservation_count':readiness['partition_counts']['FUTURE_TEST_RESERVATION_NOT_HELDOUT'],'historical_not_current_inventory':True},'latest_pilot':{'source':'docs/blind-pilot-five-queries-2026-10-28/final_status.json','human_graded_pairs':pilot_state['human_graded_pairs'],'status':pilot_state['status'],'review_pairs':pilot_state['review_pairs']},'independent_test_query_path':None,'independent_test_qrel_path':None,'unused_provenance_verified':False,'independent_label_schema_verified':False,'test_payloads_opened':0,'test_queries_evaluated':0,'test_case_pairs_evaluated':0,'test_dataset_size':None,'test_positive_pairs':None,'model_api_calls':0,'model_inferences':0,'new_questions_or_labels':0,'paid_api_usd':'0.00','substitute_dev_or_pilot':False}
    gate['metadata_documents_read']=['data/v2_5/research/readiness.json','docs/blind-pilot-five-queries-2026-10-28/final_status.json','docs/v2-independent-qa-2026-10-22.md (metadata/report excerpt, not qrel payload)','docs/experiments.md (declared Dev/Test policy)']
    save('readiness_gate.json',gate)
    # Only OLD Dev aggregates are read after snapshot. No Test payload is read.
    existing=read(sem/'evaluation/results.json')['macro'];published=read(publication/'performance_comparison.json')['rows']
    rows=[]
    for r in published:
        for field in ('precision','recall','f1'):assert r[field]==existing[r['system']][str(r['k'])][field]
        rows.append({'method':r['method'],'scope':r['scope'],'k':r['k'],'dev_precision':r['precision'],'dev_recall':r['recall'],'dev_f1':r['f1'],'dev_precision_questions':10,'dev_recall_f1_questions':6,'dev_label_type':'SAME_MODEL_TRIPLICATE_MEDIAN_AI_SILVER','test_precision':None,'test_recall':None,'test_f1':None,'test_ndcg':None,'test_status':'NOT_RUN_MISSING_VERIFIED_DATASET_AND_QRELS'})
    dense=existing['single_dense__original']
    for k,cell in dense.items():rows.append({'method':'Single Dense','scope':'O','k':int(k),'dev_precision':cell['precision'],'dev_recall':cell['recall'],'dev_f1':cell['f1'],'dev_precision_questions':10,'dev_recall_f1_questions':6,'dev_label_type':'SAME_MODEL_TRIPLICATE_MEDIAN_AI_SILVER','test_precision':None,'test_recall':None,'test_f1':None,'test_ndcg':None,'test_status':'NOT_RUN_MISSING_VERIFIED_DATASET_AND_QRELS'})
    save('dev_vs_test.json',{'rows':rows,'test_metrics_exist':False,'source':str(sem.relative_to(ROOT))+'/evaluation/results.json','notice':'All numeric performance values are historical Dev. Null Test fields mean not executed, never zero.'});csvsave('dev_vs_test.csv',rows)
    chart=[]
    for s in ('O','D'):
        for method in 'ABC':
            chart.append({'method':method,'scope':s,'f1_at5':next(r['dev_f1'] for r in rows if r['method']==method and r['scope']==s and r['k']==5),'label':'DEV_AI_SILVER_ONLY_NOT_TEST'})
    save('dev_chart_data.json',{'rows':chart})
    sourcepaths=[ROOT/'data/v2_5/research/readiness.json',pilot/'final_status.json',publication/'README.md',publication/'performance_comparison.json',sem/'evaluation/results.json',ROOT/'docs/dense-bm25-candidates-2026-10-27/README.md',ROOT/'docs/candidate-fusion-ablation-2026-10-27/README.md',ROOT/'docs/professor-feedback-2026-10-20.md',ROOT/'docs/v2-independent-qa-2026-10-22.md',ROOT/'docs/experiments.md']
    save('report_source_manifest.json',{'sources':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'kind':'Existing Dev report or metadata, not independent Test'} for p in sourcepaths]})
    save('test_execution_record.json',{'requested':'First independent Test comparison','execution_status':'NOT_RUN_PRECONDITION_FAILED','inference_runs':0,'questions_evaluated':0,'test_qrels_opened':False,'test_predictions_generated':False,'test_metrics_generated':False,'multiview_test':'NOT_RUN','paid_api_calls':0,'cost_usd':'0.00','runtime_environment':'Only standard-library metadata/report collector; pretrained encoder not loaded','performance_environment':'Not applicable: no model experiment executed','new_model_or_prototype':False})
    save('test_case_analysis.json',{'status':'UNAVAILABLE_NOT_RUN','successful_test_examples':[],'false_positive_test_examples':[],'missed_relevant_test_examples':[],'per_question_test_metrics':[],'multi_perspective_test_analysis':None,'reason':'No independent Test labels/predictions; do not manufacture 3-5 examples or transfer Dev cases.'})
    write_reports(rows,gate)
    save('verification.json',{'passed':True,'checks':['Source branch tips and ancestor relation match','Frozen12 files and10 localmodel files match base/registered hashes','18 published Dev metric rows match prior saved aggregate','All21 Test metric rows are null, never numeric zero','No Test inference/payload/label read or substitute','No new algorithm/rules/model/prototype'],'numeric_dev_rows':len(rows),'test_metric_values_created':0,'model_accuracy_verified':False,'reason_to_stop':'User-specified missing independent Test / qrels exception'})
    print('BLOCKED: no verified independent Test; reports describe Dev only. No encoder/API run.')

def write_reports(rows,gate):
    def lookup(method,scope,k):return next(r for r in rows if r['method']==method and r['scope']==scope and r['k']==k)
    table=['|방식|원질문 Dev F1@5|원질문+관점 Dev F1@5|독립 Test|','|---|---:|---:|---|']
    for m in 'ABC':table.append(f"|{m}|{lookup(m,'O',5)['dev_f1']*100:.2f}%|{lookup(m,'D',5)['dev_f1']*100:.2f}%|미실행|")
    t='\n'.join(table)
    report_a='''# 보고서 A: AX 연구 전체 진행 현황

2026-10-28 KST. **독립 Test는 준비 조건 미충족으로 실행하지 않았다.** 아래 성능은 모두 기존 개발 자료 결과다.

## 1. 연구 목적

사용자의 업무 문제를 보고 실제로 적용할 만한 AX 사례를 추천하는 연구다. 같은 업종이나 비슷한 단어만이 아니라 실제 수행 기능이 맞는지 확인하려 한다.

## 2. 아키텍처와 실제 구현

교수님 구조의 큰 흐름은 업무 문제 이해 → 동적 관점 분해 → Problem/Task/Context 표현 → Dense/BM25 후보 확보 → Query–Case 상호작용 → 근거를 가진 추천이다. 향후 Factor Anchor/Wald/전략 추천까지 확장하는 구상과 현재 검증 범위는 구분한다.

현재112사례의 관점별 검색 경로와 전체 후보, 점수·원문 근거를 보존했다. A는18종 기능 규칙, B는BGE-M3 필드 임베딩, C는둘의50:50 결합이다. 이번A/B/C는 비학습 검증용 구현으로 교수님이 제안한 학습형Interaction 신경망의 완성판은 아니다. 추가학습·새알고리즘·프로토타입 개발은 이번에 하지 않았다.

## 3. 사례와 정답

기존 운영 사례112개, Dev질문10개, 원질문×사례1120쌍을 사용했다. 같은OpenAI모델이3회평가한3360점의중앙값을AI-Silver로사용한다. 양성은18쌍이고4질문은양성이없다. P평균은10질문,R/F1평균은양성6질문이며결측을0으로채우지않았다. 사람Gold나독립Test정답이아니다. 사례는기존구조화요약이며원출판물의사실성을이번에다시검증하지않았다.

## 4. Dense/BM25와 후보 결합: 기존 Dev 결과

|조건|F1@20|해석|
|---|---:|---|
|원질문 Single Dense|19.92%|기본 검색 기준|
|원질문3-View Dense|18.81%|항상 개선하지 않음|
|원질문 BM25|11.22%|기존 보조 기준선|
|원질문 Single+BM25|17.36%|Single 단독보다 하락|
|다중관점 Single 평균RRF|18.81%|동일 관점 집계 기준|
|다중관점 Single+BM25|15.40%|평균RRF Dense보다 하락|

RRF60·각50%는 고정 실험 조건이며 교수님 아키텍처의 최적값으로 확정한 것이 아니다. 전체112후보를남긴것자체를Recall개선으로세지않았다.

## 5. 다중관점 검색: 기존 Dev 결과

Single 구조에서Top20 F1은Round-robin17.95%, 평균RRF18.81%였다. 결합 방식을 바꾸면 일부 누락을 복구했으나 원질문Single19.92%를 넘지 못했다.3-View에서도Round-robin16.25%,RRF17.95%로부분복구만확인했다. 관점의 유용성과 최종 결합 방식의 효과를 같은 것으로 해석하지 않는다.

## 6. A/B/C 정밀 매핑: 기존 Dev 결과

__TABLE__

C는 원질문+관점에서 A보다 F1@5가 약 1.48%p 높았다. 그러나 개선은 고객 문의 Q1에 집중됐고 나머지 양성 5개 질문은 같았다. B 단독의 일반적 우위는 보이지 않았다. 원질문만으로도 C의 F1@5는 47.58%여서, 이 개선을 관점 추가만의 효과로 주장할 수 없다. C의 관점 추가 효과는 F1@10에서 34.01→35.67%로 관찰됐지만 @5/@20은 같았다.

규칙이 인식하지 못한 33개 사례 전체를 임베딩으로 처리할 수 있게 됐다. 하지만 기존 10개 질문의 Silver에서 이 사례들에 대한 양성은 0쌍이다. 따라서 미인식 사례의 실제 유용성이나 회복률 개선을 입증하지 못했다. 명시된 Output을 양쪽에서 비교한 쌍도 0개다.

## 7. 독립 Test 검증 상태

이번 실행은 입력 준비 확인 단계에서 중단했다. 과거 연구 준비 기록에는 heldout_test_queries=0, heldout_test=false가 남아 있다. 지정한 3개 최신 브랜치와 관련 로컬 경로에서도 독립 Test 질문·정답 묶음을 확인하지 못했다. 이는 점검한 범위의 결론이며, 사용자 컴퓨터 어디에도 자료가 없다는 증명은 아니다.

과거 FUTURE_TEST_RESERVATION_NOT_HELDOUT 1,820개 기록은 추후 검토를 위한 예약 자료이며 Test 질문·정답 1,820개가 아니다. train_holdout_audit라는 파일명도 독립 Test를 증명하지 않는다. Q11~Q15는 이미 추천을 확인한 목적 파일럿이고 사람 평가도 103쌍 중 0건이다. 독립 Test 대신 쓰지 않았다.

## 8. 지금까지 검증한 성과

- 검색·관점·후보 결합·기능 매핑을 분리해 비교하고 나쁜 결과도 보존했다.
- 112후보와원문근거를유지하면서A/B/C를재현가능하게동결했다.
- 새질문5개의추천과점수공란인블라인드평가표103쌍을준비했다. 아직사람성능결론은없다.
- 없는Test나정답으로성능을만들지않고실행차단사유를기록했다.

## 9. 현재 한계

작은 Dev, 같은 모델의 Silver, 적은 양성, 질문·출처 중복, 제한된 규칙, 얕은 의미역 추출, 미사용 Test 부재가 남아 있다. cosine은 유사도이며 실제 업무 일치의 보증이 아니다. 자동 검사는 코드·자료 일치 확인이며 추천 정확도 검증이 아니다. Test 우수·실패 사례와 일반화 성능은 아직 없다.

## 10. 다음 연구 계획: 아직 수행하지 않은 일

1. 기존파일럿103쌍을사람이평가해기능일치판단의문제를먼저파악한다. 이는진단용이며독립Test로승격하지않는다.
2. 교수님과관점의필요성·의미매핑의기여·질문/정답구축방식을합의한다.
3. 확정모델과평가기준을고정한후기존질문/출처노출을점검한미사용독립질문·정답을별도준비한다. 이번에생성하지않았다.
4. 같은Test를보고가중치를조정하지않고한번의정식비교를한다. 모델수정후최종논문은새로운미사용Test로검증한다.

출처와해시는report_source_manifest.json. 전수수치는기존 semantic mapping 보고서 및dev_vs_test.csv 참조. [그림](dev_only_performance.png)은Dev전용이며Test성능그래프가아니다.
'''.replace('__TABLE__',t)
    text('report-A-research-status.md',report_a)
    report_b='''# 보고서 B: 1차 독립 Test 사전 점검 및 미실행 상세

**실행 결과가 아닌 실행 중단 보고서다.** Test 성능과 성공·실패 추천 사례는 생성하지 않았다.

## 1. Test 데이터 구성

검증된 독립 Test 식별자, 질문 경로, 정답 경로, 라벨 척도와 관련 기준을 찾지 못했다. 데이터셋의 질문 수·양성 수는 미확정(null)이다. 실제 평가한 질문과 쌍 수는 0이다. Q11~Q15나 기존 Dev를 대신 투입하지 않았다.

## 2. 환경과 동결

알고리즘기준c0f81b7e,지정3브랜치최신SHA를확인했다. 사전게이트/동결정책은먼저커밋했고freeze_snapshot.json에112사례·A/B/C함수·18규칙·벡터·로컬모델해시를기록했다. BGE-M3 CLS1024/L2/CPU float32/batch8/threads4/max4096과기존가중치·O/D집계·검색동점정렬을보존했다. 학습·추론·새벡터·유료API·키읽기0이다.

모델 스냅샷은 고정했지만 Test 라벨 메타데이터가 없어 실행용 평가 프로토콜은 미완료다. Dev의 3점 이상이나 파일럿의 2점 이상을 임의로 선택하지 않았다. Test 질문·정답 본문은 열지 않았다.

## 3. 성능 비교표

|조건|P@5/10/20|R@5/10/20|F1@5/10/20|nDCG@5/10|
|---|---|---|---|---|
|Single Dense|미실행|미실행|미실행|미실행|
|A 규칙|미실행|미실행|미실행|미실행|
|B 임베딩|미실행|미실행|미실행|미실행|
|C 결합|미실행|미실행|미실행|미실행|
|다중관점/추가하이브리드Test|미실행|미실행|미실행|미실행|

0%가 아니다. 정답과 실행이 없어 수치 자체가 없다. 평균의 분모, Test 양성 수, 평가 제외 질문 수도 계산하지 않았다.

## 4. 그래프

독립 Test 성능 그래프는 만들 수 없다. dev_only_performance.png에는 기존 Dev 값만 그렸고 별도 영역에 Test 미실행을 명시했다. Test를 0점 막대로 그리지 않았다.

## 5~7. 질문별 성능·우수·실패/누락 사례

모두 미확인이다. 요청한 우수 3~5개, 오추천 3~5개, 누락 3~5개를 빈 Test에 맞춰 만들지 않았다. 업무 기능 오해, 업종·단어 중심, Problem 유사성, 관점의 잘못된 상승, 규칙 미인식은 향후 분석할 분류다. 이번 Test에서 관찰한 오류가 아니다. 다중관점 Test도 미실행이며 Dev 결과로 대신 설명하지 않는다.

## 8. Dev 대비 변화

dev_vs_test.csv/json의 Dev 숫자는 기존 AI-Silver 결과 그대로이며 Test 칸은 모두 null이다. A/B/C의 원질문과 원질문+관점을 분리했다. Test 정답 생성 기준이 확인되지 않아 직접적인 증감이나 일반화 여부를 판단할 수 없다.

## 9. 사전 점검에서 확인한 사실

- 과거readiness의독립Test질문0/준비false와미사용예약표시는실제완성된Test가아니다.
- 최신파일럿은사람채점0이며,5질문은이미노출된진단용표본이다.
- 독립Test의질문·정답·척도·미사용이력의메타데이터게이트가먼저필요하다.
- 이문제는추천모델이오답을냈다는실패가아닌검증입력준비부족이다.

## 10. 연구 시사점과 재개 조건

미사용Test의명세·경로·정답과독립작성/미노출근거를확보한뒤라벨척도와관련기준을메타데이터로확정하고Git에동결해야한다. 완전정답이아니면전체Recall/F1을확정하지않고미평가/보류를0으로처리하지않는다. 양성0질문Recall/F1과IDCG0 nDCG는미정이다. 이후한번만실행해모든결과를보존한다. 이번재개조건을충족시키려고임의Test나새정답은생성하지않았다.

관련기록: preflight-protocol.md,freeze_snapshot.json,readiness_gate.json,test_execution_record.json,test_case_analysis.json,verification.json. 이번상태는BLOCKED_INDEPENDENT_TEST_NOT_IDENTIFIED이며‘1차독립검증완료’가아니다.
'''
    text('report-B-independent-test.md',report_b)
    report_c='''# 보고서 C: 교수님 면담용 핵심 요약

2026-10-28 / 문장 임베딩 기반 기업 AX 전환 사례 추천 모델 연구

## 현재 결론

**개발 자료에서는 결합 방식의 일부 개선을 확인했지만, 독립 Test는 준비되지 않아 실행하지 못했습니다.** Test결과를만들거나파일럿을대체투입하지않았습니다.

## 무엇을 연구하고 어떻게 구현했나?

업무 문제를 보고 실제 수행 기능이 맞는 기업AX사례를 추천합니다.112사례의Problem/Task/Context를보존하고,단일/다중관점검색후A18규칙,B BGE-M3필드임베딩,C50:50결합을비교했습니다. 학습형신경망완성판이아닌비학습검증용구현이며,기존모델을재학습하지않았습니다.

## 검증한 Dev 사실과 한계

원질문+관점F1@5는A46.10%,B38.76%,C47.58%였습니다. C개선은주로고객문의한질문에집중됐습니다. 원질문만써도C47.58%여서다중관점이추가로반드시유리하다고말할수없습니다. 단일Dense원질문F1@5는31.47%이며처리조건이다른기준선임을구분합니다.

정답은같은모델3회중앙값AI-Silver이며사람Gold가아닙니다.10질문중양성이있는질문은6개,관련쌍은18개뿐입니다. B단독은A보다전반적으로좋지않았고,고정Dense/BM25혼합도대응Dense보다낮았습니다. 문장임베딩의유사도를실제업무일치로과장하지않았습니다.

## 독립 Test를 왜 실행하지 못했나?

기존준비기록은독립Test0개/준비false이며,최신지정브랜치와파일경로에서도질문·정답묶음을확인하지못했습니다. 미래Test예약자료는완성된Test가아닙니다. Q11~Q15는이미추천을확인한목적파일럿으로사람평가103쌍도아직0건입니다. 대체사용하지않았습니다.

알고리즘·112사례·모델·가중치의동결기록과중단사유는GitHub에남깁니다. 이번은‘독립검증시도중입력게이트중단’이지‘독립검증완료’가아닙니다. 추가추론·유료호출·최적화·프로토타입개발은0입니다.

## 다음 순서와 교수님께 여쭐 점

먼저파일럿사람채점으로기능판단오류를확인하고,교수님의견에따라모델기여와검증계획을정하겠습니다. 모델및평가기준고정후미사용독립질문·정답을별도로확보해야합니다. 교수님의견후모델을수정한다면최종논문성능은새로운미사용Test로검증해야합니다.

1. 원질문+결합만으로도성능이같은조건에서,다중관점의필요성을어떤추가발견/손실지표로검증하면좋겠습니까?
2. 필드별문장임베딩정밀매핑의연구적차별성을인정받으려면어떤기능불일치대조와구성요소제거실험이필요합니까?
3. 독립Test질문·정답은누가어떤업무/출처그룹으로설계하고검증하는것이적절합니까?
4. 범위를현재후보검색·기능매핑으로유지할지,충분한독립라벨확보후교수님Interaction신경망까지확장할지의견을부탁드립니다.

실제확인된성과는재현가능한단계별Dev비교·원문추적·부정적결과보존·블라인드평가준비입니다. 독립일반화성능과새학습형모델우수성은아직입증하지못했습니다.
'''
    text('report-C-professor-summary.md',report_c)
    index='''# 1차 독립 Test 요청: 사전 점검 중단 및 교수님 보고자료

**독립 Test는 실행하지 않았습니다.** 점검한 경로와 기록에서 미사용 독립 Test 질문·정답 묶음을 확인하지 못해 사용자 지시의 중단 조건을 적용했습니다. Dev/파일럿을 대신 넣거나 정답을 만들지 않았습니다.

## 보고자료

- [A: 연구 전체 진행 현황](report-A-research-status.md)
- [B: 독립 Test 사전 점검·미실행 사유](report-B-independent-test.md)
- [C: 교수님 면담용 요약](report-C-professor-summary.md)
- [C: 2페이지 PDF](professor-meeting-summary.pdf)
- [기존 Dev 전용 비교 그림](dev_only_performance.png)
- [Dev / Test 비교 CSV](dev_vs_test.csv) / [JSON](dev_vs_test.json)

Test쪽빈칸/null은0점이아니라미실행입니다. 실제Test우수/실패사례·질문별지표·다중관점효과는없습니다. 그림의모든숫자는기존Dev AI-Silver결과입니다. 현재프로그램을수정하지않았습니다.

사전정책은preflight-protocol.md와config,알고리즘파일/모델해시는freeze_snapshot.json,메타데이터조사는readiness_gate.json,추론0회기록은test_execution_record.json에있습니다. source manifest와verification은보고자료일치점검이지추천정확도검증이아닙니다.

재개하려면미사용독립Test의명세/경로/정답/척도와미노출근거를확인하고평가기준을동결해야합니다. 이번에Test를생성하지않았습니다. 모델수정후에는새미사용Test가필요합니다. 기존파일럿103쌍의사람채점도아직0건입니다.
'''
    text('README.md',index)

if __name__=='__main__':main()
