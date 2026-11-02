"""Report fixed new validation results; do not alter predictions or judgments."""
from collections import Counter
import csv
from pathlib import Path
import numpy as np
from ax_research.heldout import read,write,sha,jsonl
from scripts.c0_c1_new_validation import ROOT,OUT,INPUT


def main():
    result=read(OUT/'evaluation/metrics.json');cohort=read(OUT/'evaluation/complete_cohort_summary.json');complete=set(cohort['complete_query_ids']);lookup={(r['system'],r['metric']):r['value'] for r in cohort['macro']};per={(r['system'],r['query_id']):r for r in result['per_query']};qs=jsonl(INPUT);qrels=read(OUT/'qrels.json')['records'];counts=Counter(r['grade'] for r in qrels);key=read(OUT/'review_key.json');cases=read(ROOT/'docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    changes=list(csv.DictReader((OUT/'evaluation/rank_changes.csv').open(encoding='utf-8')));top=list(csv.DictReader((OUT/'evaluation/topk_changes.csv').open(encoding='utf-8')));pred=read(OUT/'predictions/rankings.json')['systems']
    pct=lambda v:'—' if v is None else f'{100*v:.2f}'
    def table():
        text=['|조건(같은6질문)|P@5|R@5|F1@5|P@10|R@10|F1@10|P@20|R@20|F1@20|nDCG@5|nDCG@10|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        metrics=['Precision@5','Recall@5','F1@5','Precision@10','Recall@10','F1@10','Precision@20','Recall@20','F1@20','nDCG@5','nDCG@10']
        for n in ('C0','C1','C1_NO_EMBEDDING'):text.append('|'+n+'|'+'|'.join(pct(lookup[n,m]) for m in metrics)+'|')
        return '\n'.join(text)
    qtable=['|질문|업무|확정/112|확정된관련수※|F1@5 C0→C1|nDCG@10 C0→C1|','|---|---|---:|---:|---|---|']
    for q in qs:
        qid=q['query_id'];a=per['C0',qid];b=per['C1',qid];qtable.append(f"|{qid}|{q['target']}|{a['judged']}|{a['positive_count']}|{pct(a['metrics']['F1@5'])}→{pct(b['metrics']['F1@5'])}|{pct(a['metrics']['nDCG@10'])}→{pct(b['metrics']['nDCG@10'])}|")
    counttable=['|같은6문항|관련유지|추가|손실|0점C0→C1|1점C0→C1|','|---|---:|---:|---:|---|---|'];totals=[]
    for k in (5,10,20):
        group=[r for r in top if r['query_id'] in complete and int(r['k'])==k]
        vals={f:sum(int(r[f]) for r in group) for f in ('known_related_kept','known_related_added','known_related_lost','C0_grade0','C1_grade0','C0_grade1','C1_grade1')};totals.append({'k':k,**vals});counttable.append(f"|Top{k}|{vals['known_related_kept']}|{vals['known_related_added']}|{vals['known_related_lost']}|{vals['C0_grade0']}→{vals['C1_grade0']}|{vals['C0_grade1']}→{vals['C1_grade1']}|")
    human=read(OUT/'human_review_max20.json')['records'];hdoc=['# 사람 확인 후보19건','','채점 수백 건을 요청하는 자료가 아니다. 우선5개 보류 항목과 결과 해석에 중요한 응용 판정만 추렸다. 원문 전체와질문은 human_review_max20.json에 있다. 사람점수는공란이며이번AI판정을덮어쓰지않고별도버전으로관리한다.','','|번호|질문|실제Task|현재AI판정|확인할사항|','|---:|---|---|---|---|']
    for i,r in enumerate(human,1):hdoc.append(f"|{i}|{r['query_id']}|{r['Task']}|{r['current_grade'] if r['current_grade'] is not None else '보류'}|{r['human_confirmation_needed']}|")
    (OUT/'human_review_max20.md').write_text('\n'.join(hdoc)+'\n',encoding='utf-8',newline='\n')
    traces=[]
    for q,eid in [('NV20261102_10','E057'),('NV20261102_10','E094'),('NV20261102_01','E068'),('NV20261102_06','E046'),('NV20261102_05','E072')]:
        c=key[eid];r=next(r for r in changes if r['query_id']==q and r['case_id']==c);traces.append({'rank_change':r,'case':cases[c],'question':next(x['text'] for x in qs if x['query_id']==q),'judgment':next(x for x in qrels if x['query_id']==q and x['case_id']==c)})
    write(OUT/'case_examples.json',{'records':traces,'selection_after_evaluation_for_explanation_not_tuning':True})
    changed_full=[q['query_id'] for q in qs if q['query_id'] in complete and any(per['C0',q['query_id']]['metrics'][m]!=per['C1',q['query_id']]['metrics'][m] for m in per['C0',q['query_id']]['metrics'])]
    neutral_tradeoff=[]
    for q in complete:
        a=per['C1',q];b=per['C1_NO_EMBEDDING',q]
        neutral_tradeoff.append({'query_id':q,'with_embedding':a['metrics'],'neutral':b['metrics'],'F1@10_delta':a['metrics']['F1@10']-b['metrics']['F1@10'],'Recall@20_delta':a['metrics']['Recall@20']-b['metrics']['Recall@20']})
    write(OUT/'evaluation/embedding_by_query.json',{'records':neutral_tradeoff,'same_complete6':True,'not_new_model_training':True})
    vector_count=len(np.load(OUT/'predictions/new_query_vectors.npz',allow_pickle=False)['texts'])
    doc='''# 신규 업무 질문 기반 C0·C1 검증

작업 식별일2026-11-02 (정확한 시점은 Git 커밋 기록 참조) · research/c0-c1-new-validation-20261102

**현재 AI판정으로 완전 평가된6질문에서는 C1이높았지만, 개선은온도이탈감지1질문에집중됐다. 같은AI가질문을쓰고채점했으므로독립성능검증이나일반화입증은아니다.** 원문단독만실행했고다중관점은미완료다. 기존모델/시연/WorkB독립Test는그대로보존한다.

## ① 검증 목적

기존C1의업무목적구분이새질문에서도오탐을줄이고관련사례를유지하는지,기존BGE-M3성분이유용한지확인했다. C0/C1두모델만주비교하고C1의의미점수중립진단을곁들였다. C2/C3/C_ALL은새모델기준으로쓰지않았다. 기준은1e6ad428ac23f493df9a86b1d05fae05f818dd36이며원격tip과같음을확인했다.

## ② 검증 데이터

새한국어질문10개:IT운영2/인사2/재무·문서2/고객지원1/구매1/제조1/물류1. [질문원문](input/questions.jsonl), [정책](policy.json). 문서요약/검증,검색/분석,분류/판정,안내/실행,미래예측/현재감지차이를포함했다. 사례설명을복사하거나사례ID로정답을지정하지않았다. 기존Dev10·공개파일럿5와정규화문장중복0,문자유사도기록은 [중복검사](overlap_check.json)에있다. 같은업무기능의의미겹침과작성자의코퍼스사전지식은남아있다. WorkB의질문은중복검사용으로도열지않았다.

질문·정책SHA를저장한후커밋bda99829로고정했다. 이후모델결과를보고질문을고치거나제외하지않았다. 질문10×기존사례112=1120쌍을모두검토해**AI확정1115건+ABSTAIN5건**을남겼다. 미평가누락은0건이고보류는0점이아니다. 등급별분포는0점''' +str(counts[0])+'''/1점'''+str(counts[1])+'''/2점'''+str(counts[2])+'''/3점'''+str(counts[3])+'''/보류5다.

완전판정은질문01/02/05/06/07/10의6개(672쌍)다. 나머지03/04/08/09도유지했지만각1/1/2/1개보류가있어전체Recall/F1/nDCG를계산하지않았다. 이질문들의확정된관련수는총관련수의하한일뿐이다. 확정판정이없던자료를0으로채우지않았다.

**평가자정보:** 현재대화의동일AI가질문작성과유일한판정을했다. 새질문의모델순위·점수는채점이끝날때까지표시하지않았고,모든112사례를무작위익명ID의Problem/Task/Context자료로읽었다. 하지만같은대화/같은설계자의기억과사전노출은지울수없으며접근권한으로분리된독립평가도아니다. 사람Gold·복수독립모델합의정답으로표현하지않는다. [실제112개명시판정행렬](blind_review/assistant_review_decisions.tsv), [판정자료와근거](qrels.json), [원자료](blind_review/cases.json).

## ③ 실험 방법

기존C0/C1코어·18규칙·C1목적필터·50:50가중치·BGE-M3 CLS1024 정규화·Single Dense/BM25동점점수·112후보를변경하지않았다. 동일질문을원문만으로각각입력했다. 새질문/필드의고유문자열40개를로컬CPU로실제임베딩했고기존사례벡터를재사용했다. 새모델학습이아니다. 모델10파일/패키지/입력/코드/환경해시는 [동결기록](model_freeze.json)에있다.

질문정책bda99829 → 실행코드ab38c5c9 → 예측봉인7a642858 → 순위미표시판정봉인c8f49820 → 1회성능평가순서다. 판정에모델점수·순위·모델이름을제공하지않았다. 정답은예측후평가에서만읽었다. 사례전수판정자료는TopK결과로고른풀이아니다.

새척도0~3,관련>=2. 기존Dev0~4/관련>=3과다르므로47.58%같은이전점수와이번점수를직접빼서개선이라고주장하지않는다. Precision은TopK모두판정된경우만계산,Recall/F1은질문전체112판정과양성이있을때만계산했다. nDCG는gain2^grade-1,IDCG는112전체,IDCG0은미정이다. 모든모델에같은평가가능질문을사용한다.

**다중관점은NOT_RUN.** 새LLM관점생성API는승인받지않았으므로호출하지않았다. 기존Dev관점재사용이나단순문장분할을대신사용하지않았다. 따라서새질문의원문vs다중관점효과는아직답할수없다.

## ④ 실험 결과

아래주표는**결과가좋은질문을고른것이아니라112판정이완료된동일6개**의Macro다. 단위는지표값×100이며표본의성공확률/통계적유의성을뜻하지않는다.

'''+table()+'''

C1 F1@5는8.40→13.16%(+4.76%p),nDCG@10은23.61→35.33%(+11.73%p)다. **같은6개중온도이탈질문10만개선됐고다른5개의계산한지표는같았다.** 넓은업무범위에서일관되게효과가재현됐다고말할수없다. 질문01운영지침검색과02접속사건감지는C0/C1모두Top20관련2점이상0개였다. 현재추천의절대품질이충분하다는증거도아니다.

보류가있어도모든TopK가판정된질문에서Precision은계산가능하다. 사전정책그대로의주비교Precision@5는같은8질문에서20.00→22.50%,@10은같은7질문에서17.14→20.00%,@20은같은7질문에서13.57→14.29%다. 이표의분모6과다르므로섞지않는다. 임베딩비교의Precision공통분모도별도로저장했다. [전체지표·분모·제외ID](evaluation/metrics.json), [6문항동일분모표](evaluation/complete_cohort_summary.json).

'''+ '\n'.join(qtable)+'''

※부분질문의확정된관련수는하한이다. ‘—’는미정이며0이아니다. 특히증빙검증질문04는C1 Top5에보류사례가들어Precision@5도미정이므로C0와숫자를직접비교하지않는다. 질문별성과를숨기기위해제외한것이아니다.

'''+ '\n'.join(counttable)+'''

같은6질문의Top5자리수는30개다. 0점20→17,1점4→6,관련2점이상6→7로바뀌었다. 기존관련사례의Top5/10/20손실은이6문항에서는0이다. 0점판정은현재AI의기능판단이며인간검증무관정답이아니다. 부분판정4질문은확인된쌍의변화를기록하되전체관련보존율을확정하지않았다.

## ⑤ 실제 사례 — 개선과남은실패

**개선:** 온도범위이탈질문10에서C0는주문가격검증·HR신청검증·직원보고서검증을상위에두었다. 같은‘기록확인’이라도실제요청은현재센서이상감지다. C1은열펌프이상탐지(현재AI2점)를18→1위,장비위험감지(2점)를22→6위로올렸다. 다만열펌프/장비감지를냉장온도감지에충분히응용할수있다는판정자체를사람이확인해야한다. 이2개판정에개선해석이크게의존한다.

**남은실패:** 운영지침검색질문01의내부지식검색직접사례(3점)는43→43위였다. 은행대사질문06의은행거래대사직접사례(3점)는31→26위로올랐지만여전히Top20밖이다. C1은이문제를해결하지못했다. 신뢰할만한서비스추천성능으로승격하기어렵다.

**강한관련사례:** 계약요약직접사례(3점)는1위유지,고객응답·인계(3점)는2위유지다. 부분판정HR증빙질문04의지원서증빙대조(3점)는1→2위로다소내려갔지만Top5는유지했다. 전질문의3점사례는 [강한관련순위표](evaluation/strong_grade3_ranks.csv)에보존했다. [전112순위변화](evaluation/rank_changes.csv), [진입·손실](evaluation/events.json), [대표원문·판정·순위](case_examples.json).

**임베딩기여:** 같은6질문에서C1의실제의미성분은중립성분보다F1@5 9.70→13.16%,nDCG@10 24.52→35.33%로높았다. 계약요약사례는중립7위/실제1위여서관련자료를위로정렬하는데도움이됐다. 그러나모든질문에좋지는않았다. 운영지침검색의Recall@10은중립16.67%→실제0%,은행대사의Recall@10은중립66.67%→실제33.33%로악화됐다. 같은6질문의Recall@20도42.58→41.11%로하락했다. 평균F1상승만으로누락문제가없다고말하면안된다. [질문별중립진단](evaluation/embedding_by_query.json).

## ⑥ 연구적 의미

현재AI-Silver와원문조건에서C1의오탐억제·순서개선이새온도이탈질문한개에서관찰됐다. 기존동적관점Dev효과의독립재현이아니며다중관점검증도아니다. 기능목적구분의도움가능성을보여주는보조적신규검증이다. 같은데이터의임베딩중립진단은기존의미점수항이도움을줄수있고때로는누락을늘릴수있음을보였다. 새모델을학습했거나BGE-M3가다른모델보다우수하다는증거는아니다.

## ⑦ 한계와검증

- 질문작성자=유일AI평가자. 완전한인지적블라인딩·독립평가·Human-Gold없음. 1115점은사람의객관정답이아니다.
- 새질문은작성자가알던코퍼스/이전연구와완전히독립적이지않고기존기능과의미겹침이있다. 기존15개와문장중복0만확인했으며WorkB독립성검사때문에봉인본문을열지않았다.
- 전체지표는6질문,개선은1질문에집중. 작은표본이며통계적유의성/일반화향상주장불가. 원문의지식검색·감지2질문에서관련추천실패도남았다.
- 보류5건으로4질문전체지표미정. 보류해소후지표를고쳐이번결과를좋게만들지않고새버전평가로관리해야한다.
- 같은업무기능의다른업종응용2점은판정자의해석이며특히온도질문의관련판정은외부확인이필요하다. 원출판물재검증이아닌구조화Problem/Task/Context를사용했다. 없는Output/기술/효과/보안을추정하지않았다.
- 유료새관점생성·복수독립평가·사람판정은수행하지않았다. 계산가능한원문조건만완료했다.

기존148+신규15=163자동검사통과. 별도수식으로3360점수/30개전체순위/330개질문지표/44개공통분모평균을검산했다. 같은로컬모델로새질문벡터40개를다시계산한재현에서도30순위와3360점수파일이완전히일치했다. 키/WorkB/최종Test미열람,유료LLM API0,API비용$0. 기존112사례/기존정답/C0/C1/가중치/시연/C2/C3는변경하지않았다. 검사는계산과자료연결의정확성을확인하며AI판정정확성을보장하지않는다. [검증JSON](verification.json), [시험로그](pytest.txt).

## ⑧ 다음 단계

먼저 [사람확인후보19건](human_review_max20.md)의보류5건과중요응용판정을확인하는것이우선이다. 사람의점수는미리채우지않았다. 사용자에게수백건을채점해달라고요구하지않는다. 확인결과는별도버전으로보존한다. 그다음별도독립평가자와API예산승인이있을때새질문에대한새다중관점검증을진행할수있다. 이번질문·판정·모델을결과에맞춰조정하거나WorkB Test를열어보완하지않았다. 기존모델·시연프로그램으로자동반영하지않는다.

|질문|이번답변|
|---|---|
|C1정밀도향상?|같은완전6문항P@5 20.00→23.33%;전체분야일관개선은아님|
|Recall유지?|같은6문항C0대비모든K상승,기존관련TopK손실0;부분4문항은확정불가|
|F1/nDCG향상?|6문항평균상승이나1문항에효과집중|
|0점추천감소?|6문항Top5 20→17,판정출처는동일AI|
|강한관련누락?|C0대비주TopK손실없지만검색/대사직접사례가여전히낮은순위|
|효과큰업무?|현재온도이탈감지,해당응용판정사람확인필요|
|악화업무?|C0vsC1에서완전6문항수치악화없음;임베딩진단에서는검색·대사일부악화|
|기존효과재현?|원문조건의보조관찰만,기존D조건/다중관점재현아님|
|현재주장범위?|AI작성·채점신규6완전질문에서고정C1의국소효과관찰|

## 코드·실행·자료 보호

신규어댑터는기존scripts/heldout_run.py의추론core와src/ax_research/action_aggregation.py의동결C1을그대로호출한다. 새평가기는new_validation.py로분리했다. 질문입력/예측/채점행렬/qrels/evaluation을별도파일·해시로관리하며기존결과는덮지않는다. 실행환경/패키지/모델해시는model_freeze.json,정확한163검사명령은tests.json에있다.

```powershell
$env:PYTHONPATH='src;.'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
$py='../AX-prototype/.venv/Scripts/python.exe'
# 실제재현:존재하지않는새폴더사용.정답을읽지않고벡터부터다시계산한다.
& $py -m scripts.c0_c1_new_validation_reproduce --output '../AX-new-validation-replay-new'
& $py -m pytest -p no:cacheprovider tests/test_new_validation.py -q
```

첫실행기록은 `python -m scripts.c0_c1_new_validation freeze/predict/bundle/labels/evaluate` 순서다. 기록된결과가이미있으면덮어쓰기를거부한다. 재현용스크립트는기존봉인입력으로새폴더에서실제임베딩·추론을재실행하고저장결과와비교한다. qrels는재평가용자료이며추론에전달하지않는다. 예측/정답봉인해시와새검증파일해시를확인하며실패로그를삭제하거나미확정요청을재호출하지않는다.
'''
    (OUT/'README.md').write_text(doc.rstrip()+'\n',encoding='utf-8',newline='\n')
    write(OUT/'final_status.json',{'question_policy_commit':'bda99829','prediction_commit':'7a642858','judgment_commit':'c8f49820','question_count':10,'reviewed_pairs':1120,'AI_JUDGED':1115,'ABSTAIN':5,'complete112_questions':len(complete),'same_author_and_reviewer':True,'independent_evaluators':0,'Human_Gold':0,'primary_complete6_macro':cohort['macro'],'changed_complete_questions':changed_full,'effect_concentrated_in_one_question':True,'all_models_original_only':True,'dynamic_perspectives':'NOT_RUN_NO_PAID_API_APPROVAL','tests_passed':163,'fresh_query_field_texts_encoded':vector_count,'fresh_query_embedding_replay_equal':True,'old_models_weights_inputs_results_changed':False,'post_result_tuning':False,'paid_API_calls':0,'cost_usd':'0.00','WorkB_read':False,'final_independent_Test_executed':False,'human_review_candidates':len(human),'primary_complete_cohort_topk_counts':totals,'claim':'Limited same-author AI-Silver new-validation observation; no independent generalization or multi-perspective replication claim'})
    print('Report ready:10queries/1115AIgrades/5abstain; complete6; local effect only; human review19')


if __name__=='__main__':main()
