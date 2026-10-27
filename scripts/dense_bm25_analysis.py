"""Offline case analysis and design-only handover for future Query-Case mapping."""
import json
import statistics
from collections import defaultdict
from scripts import dense_bm25_candidates as c

NAMES={'A':'A 원질문 Single','B':'B 원질문3-View','C':'C 원질문 Single+BM25','D':'D 다중관점 Single','E':'E 다중관점3-View','F':'F 다중관점 Single+BM25','S_C3':'보조 원질문3-View+BM25','S_F3':'보조 다중관점3-View+BM25','S_BM25_O':'보조 원질문BM25','S_BM25_M':'보조 다중관점BM25'}
TOPICS={'V21D001':'고객 문의','V21D002':'이메일·후속조치','V21D003':'사내 지식','V21D004':'문서 검증','V21D005':'전사 데이터','V21D006':'상품 검색','V21D007':'구매·견적','V21D008':'예측','V21D009':'사내AI보안','V21D010':'품질·계획'}
def pct(v):return '평가 불가' if v is None else f'{v*100:.2f}%'
def pp(v):return f'{v*100:+.2f}%p'
def main():
    r=c.read(c.OUT/'results.json');systems=r['systems'];agg=r['aggregate'];qr=c.read(c.OUT/'query_registry.json')['paths'];cases=c.read(c.OUT/'case_registry.json')['cases'];bm=c.read(c.OUT/'bm25_paths.json')['paths'];ties=c.read(c.OUT/'bm25_tie_diagnostics.json')['paths']
    labels={(x['qid'],x['cid']):x['silver_score'] for x in c.read(c.SOURCE/'stage1_silver.json')['records']}
    with (c.OUT/'candidate_features.jsonl').open(encoding='utf-8') as f:features=[json.loads(line) for line in f]
    ix={(x['path_id'],x['backbone'],x['case_id']):x for x in features};changes=[];summary={};question=[]
    for cond,setting in c.CONDITIONS.items():
        for row in systems[cond]:
            if row.get('changes'):
                for k,ch in row['changes'].items():
                    changes.append({'condition':cond,'reference':row['reference'],'qid':row['qid'],'repeat':row['repeat'],'k':int(k),**ch,'new_tasks':{cid:cases[cid]['task'] for cid in ch['new_related']},'lost_tasks':{cid:cases[cid]['task'] for cid in ch['lost_related']}})
        if cond in ('C','F','S_C3','S_F3'):
            es=[x for x in changes if x['condition']==cond and x['k']==20]
            summary[cond]={'reference':setting['reference'],'query_runs':len(es),'new_related_events':sum(len(x['new_related']) for x in es),'retained_related_events':sum(len(x['retained_related']) for x in es),'lost_related_events':sum(len(x['lost_related']) for x in es),'unit':'question/repetition events, not distinct cases; original10 runs versus dynamic30 runs'}
    c.save('related_case_changes.json',{'records':changes,'summary':summary})
    for q in sorted(TOPICS):
        entry={'qid':q,'topic':TOPICS[q],'positive_cases':sum(g>=3 for (qid,cid),g in labels.items() if qid==q),'conditions':{}}
        for cond,rows in systems.items():
            rs=[x for x in rows if x['qid']==q];cell={}
            for k in c.CFG['K']:
                cell[str(k)]={}
                for metric in ('precision','recall','f1'):
                    vs=[x['metrics'][str(k)][metric] for x in rs if x['metrics'][str(k)][metric] is not None]
                    cell[str(k)][metric]=statistics.mean(vs) if vs else None;cell[str(k)][metric+'_stdev']=statistics.stdev(vs) if len(vs)>1 else None
            entry['conditions'][cond]=cell
        question.append(entry)
    c.save('question_summary.json',{'rows':question})
    targetids={'AXV2N_0121':'고객 도움말센터 질문응답','AXV2N_0124':'직원 HR 규정 질문응답','AXV2C_0093_01':'제조 품질 불량 원인 분석'};case_studies=[];examples=[]
    for backbone,dense_o,dense_m,hybrid_o,hybrid_m in [('single','A','D','C','F'),('three','B','E','S_C3','S_F3')]:
        for rep in (0,1,2,3):
            dcond=dense_o if rep==0 else dense_m;hcond=hybrid_o if rep==0 else hybrid_m;bcond='S_BM25_O' if rep==0 else 'S_BM25_M'
            d=next(x for x in systems[dcond] if x['qid']=='V21D001' and x['repeat']==rep);h=next(x for x in systems[hcond] if x['qid']=='V21D001' and x['repeat']==rep);b=next(x for x in systems[bcond] if x['qid']=='V21D001' and x['repeat']==rep)
            for cid,name in targetids.items():
                paths=[{'path':qr[p], 'features':ix[(p,backbone,cid)]} for p in h['path_ids']]
                row={'qid':'V21D001','original_query':qr[h['path_ids'][0]]['original_query'],'repeat':rep,'scope':'original' if rep==0 else 'dynamic','backbone':backbone,'cid':cid,'case_name':name,'actual_ptc':{k:cases[cid][k] for k in ('problem','task','context')},'existing_whole_query_silver':labels[('V21D001',cid)],'dense_final_rank':d['ranking'].index(cid)+1,'bm25_final_rank':b['ranking'].index(cid)+1,'hybrid_final_rank':h['ranking'].index(cid)+1,'path_details':paths,'not_a_new_judgment':True,'ranks_are_final_aggregates':rep>0}
                case_studies.append(row)
                if backbone=='single' and rep in (0,1):
                    examples.append({'qid':'V21D001','repeat':rep,'original_problem':row['original_query'],'case_id':cid,'case':row['actual_ptc'],'retrieval_paths':paths,'final_candidate_rank':row['hybrid_final_rank'],'whole_vs_perspective_scope':'Original problem preserved; perspective-specific actual work correspondence not yet judged.','mapping_status':'NOT_IMPLEMENTED_NOT_EVALUATED'})
    c.save('case_studies.json',{'cases':case_studies,'old_round_robin_not_the_matched_hybrid_control':True})
    c.save('mapping_input_examples.json',{'examples':examples,'evaluation_labels_excluded':True})
    c.save('mapping_schema.json',{'status':'DATA_CONTRACT_ONLY_NO_MAPPING_ALGORITHM','query_registry':'query_registry.json: path_id -> original_query, query_text, perspective and source_quote','case_registry':'case_registry.json: case_id -> raw Problem/Task/Context, evidence_ids, leakage_group_id','feature_rows':'candidate_features.jsonl: (path_id,backbone,case_id) -> Dense/BM25 ranks and scores, matched tokens, rank-RRF terms and path contribution','candidate_pools':'mapping_candidate_pools.jsonl: condition/qid/repeat -> all112 ranked candidate IDs and path provenance; do not prefilter Top20 before mapping','join_keys':['path_id','case_id','backbone'],'forbidden_input_fields':['silver_score','median','relevant','label','ratings'],'labels_kept_only_in_evaluation':'existing Stage1 whole-query Silver, never copied into mapping feature inputs','future_output_contract':{'assessment_status':'UNASSESSED','scope':'whole_question or named_perspective','performed_action_evidence':None,'functional_object_evidence':None,'produced_output_evidence':None,'query_evidence':None,'matching_explanation':None,'unsupported_claims':None,'source_offsets':None},'design_notes':['Read Task/explicit operational Context for actually performed work. Problem is a need/context, not proof of a capability.','Compare action, object and output; allow genuine cross-industry functional transfer and distinguish inquiry answering from quality-defect diagnosis.','Retrieval rank, token match or high cosine is not a relevance proof. No mapping score or LLM judgment produced here.','Current Silver is whole-query relevance, not independent labels for108 viewpoints. Do not copy a whole-query positive label to every perspective.','Separate future training/evaluation by query/source groups;18 positive pairs are insufficient to claim general model quality.']})
    # Original-channel complementarity is a diagnostic, not a hybrid ranking.
    comp=c.read(c.OUT/'channel_complementarity.json')['records'];origcomp={}
    for backbone in ('single','three'):
        origcomp[backbone]={}
        for k in c.CFG['K']:
            xs=[x for x in comp if x['path_id'].startswith('o_') and x['backbone']==backbone and x['k']==k]
            origcomp[backbone][str(k)]={f:sum(len(x[f]) for x in xs) for f in ('dense_only_related','bm25_only_related','common_related')}
    c.save('complementarity_summary.json',{'original_query_sum_over10':origcomp,'note':'Union of both TopK is larger than K; this is complement diagnosis only, not equal-budget performance.'})
    lines=['# Dense+BM25 후보 확보 실험 결과','',f"기준 `{c.CFG['base_commit']}` · 새 브랜치 `{c.CFG['branch']}` · 사전 설정 커밋 `{c.read(c.OUT/'preregistration.json')['config_preregistration_commit']}`.",'',
    '## ① 이번에 무엇을 했는가?','',
    '기존 Dense 순위와 점수를 그대로 두고, 같은112개 사례에 기존 Kiwi+BM25를 로컬 계산했다. 원질문10개와 기존108개 관점을 재사용했다. Dense·BM25 순위를 각각 `1/(60+순위)`로 바꾼 뒤 절반씩 합쳤다. 서로 단위가 다른 원점수는 더하지 않았다.','',
    '다중관점은 각 관점의 기여를 평균했다. M개 관점의 각 Dense/BM25 기여는1/(2M)이다. Dense 단독에도 같은 관점 평균RRF를 적용해 BM25 추가 효과만 비교했다. 중간 하이브리드 순위에 RRF를 다시 씌우지 않았다.','',
    '**C/F의 Dense는 Single을 주 조건으로 사전 고정했다.**3-View 하이브리드는 별도 보조 조건으로 평가했다. D/E는 과거Round-robin 결과가 아니라 이전 후보 결합 실험의 평균RRF이며, 전체112개 순위가 그 결과와 같음을 확인했다. 결합 방식과 검색 채널을 동시에 바꾼 효과로 오해하지 않아야 한다.','',
    'LLM 호출·키 접근·새 임베딩 계산·모델 학습·정답 변경은0이다. 후보마다112개 전체를 유지하고 최종Top5/10/20만 평가했다.','',
    '## ② 성능은 개선됐는가?','',
    '**이번 사전 고정50:50 조건에서는 하이브리드가 대응하는 Dense 단독보다 모든 평가K에서 MacroF1이 낮았다.** 성능을 높이려고 비중이나 토큰화를 바꾸지 않았다.','',
    'Precision 평균은10개 질문, Recall·F1 평균은 양성 있는6개 질문이다. Q2/Q5/Q7/Q9는 Recall·F1 평가 불가이며0점으로 채우지 않았다. 동적 조건은 질문별3회 평균 후 원질문 단위로 평균했다.','',
    '|조건|질의·검색|K|Precision|Recall|F1|','|---|---|---:|---:|---:|---:|']
    for cond in ('A','B','C','D','E','F'):
        for k in c.CFG['K']:
            z=agg[cond][str(k)];lines.append(f"|{cond}|{NAMES[cond][2:]}|{k}|{pct(z['macro_precision'])}|{pct(z['macro_recall'])}|{pct(z['macro_f1'])}|")
    lines+=['','### 보조 조건도 같은 방향인가?','', '|조건|F1@5|F1@10|F1@20|','|---|---:|---:|---:|']
    for cond in ('S_C3','S_F3','S_BM25_O','S_BM25_M'):lines.append('|'+NAMES[cond]+'|'+'|'.join(pct(agg[cond][str(k)]['macro_f1']) for k in c.CFG['K'])+'|')
    lines+=['','3-View를 Dense로 쓴 보조 하이브리드도 같은 구조의 Dense 단독보다 낮았다. 표의 모든K·구조를 보고하며 좋은 조건만 선택하지 않았다.','',
    '### Dense와BM25는 무엇을 서로 다르게 찾았나?','', '|원질문 검색 구조·K|Dense만 찾은 관련|BM25만 찾은 관련|공통 관련|','|---|---:|---:|---:|']
    for backbone,zs in origcomp.items():
        for k,z in zs.items():lines.append(f"|{backbone} K{k}|{z['dense_only_related']}|{z['bm25_only_related']}|{z['common_related']}|")
    lines+=['','이 표는 상위K 목록 두 개의 보완 가능성만 본 것이다. 두 목록의 합집합은 K보다 클 수 있으므로, 공정한 최종K 성능이라고 주장하지 않는다. 실제 하이브리드 결과는 위 성능표다.','',
    '## ③ 실제 관련 사례가 더 잘 발견됐는가?','',
    '|맞춘 비교|질문·회차 수|신규 관련 발견|기존 관련 유지|기존 관련 누락|','|---|---:|---:|---:|---:|']
    for cond,z in summary.items():lines.append(f"|{cond} 대 {z['reference']}|{z['query_runs']}|{z['new_related_events']}|{z['retained_related_events']}|{z['lost_related_events']}|")
    lines+=['','건수는 질문·생성 회차별 사건 수다. 같은 사례가 반복될 수 있어 고유사례 수와 다르다. 원질문Single 하이브리드는 신규1건을 얻고3건을 놓쳤다. 다중관점Single 하이브리드는 신규5건을 얻고12건을 놓쳤다. 전체적으로 신규 발견이 손실을 보상하지 못했다.','',
    '필수 사례의 고객 문의 문제(V21D001), Single 첫 생성 회차 결과다. 동적Dense 순위는 평균RRF 최종 순위이며, 관점 안에서의 순위와 구분한다.','',
    '|검색 범위|사례|Dense 순위|BM25 순위|하이브리드 순위|기존Silver|','|---|---|---:|---:|---:|---:|']
    for z in case_studies:
        if z['backbone']=='single' and z['repeat'] in (0,1):lines.append(f"|{'원질문' if z['repeat']==0 else '다중관점 회차1'}|{z['case_name']}|{z['dense_final_rank']}|{z['bm25_final_rank']}|{z['hybrid_final_rank']}|{z['existing_whole_query_silver']}|")
    lines+=['','- 도움말센터 질문응답은 원질문3→1위, 다중관점6→2위로 올라갔다. 원래Top20에 있던 사례이므로 이를 ‘새로운Top20 발견’이라고 세지 않았다. 다중관점에서는Top5에 새로 들어온 개선이다.',
    '- HR 규정 질문응답은 Single 원질문25→49위, 다중관점27→60위로 더 밀렸다. 기존Round-robin13위·RRF27위였던 기록과 구분한다. 현재의 맞춘 Dense 기준에서 이미Top20 밖이었으므로 새Top20 손실이라고 과장하지 않았다.3-View 원질문에서는20→42위로 내려 실제Top20 손실이 됐다.',
    '- 제조 품질 원인 분석은 고객 문의에 대한 기존Silver0이다. 원질문37→53위, 다중관점28→50위로 낮아졌다. 현재 최종Dense Top20에도 없었으므로 이를 처음 제거한 효과라고 주장하지 않는다. 개별 품질 관점에서의 상세 순위와 실제Task는 `case_studies.json`에 있다.','',
    '각 사례의 원래 문제, 실제Problem·Task·Context, 각 관점의 원점수·순위·일치 토큰·RRF 기여·최종 순위를 모두 보존했다. 새로운 관련도 평가는 하지 않았다.','',
    '구체적으로 원질문 Single의 Top20에는 결제 기술문의 검색·답변 사례(AXV2H_0071_01)가 새로 들어왔다. 대신 항공 고객 질문응답(AXV2P2_0060_01), 웹사이트 FAQ 응답(AXV2P2_0067_01), 금융상담사 내부 지식 검색(AXV2N_0110)이 빠졌다. 마지막 사례는 Q3에서의 손실이며 나머지는 Q1이다. 질문별 원문과 실제 Task는 related_case_changes.json에 남겼다.','',
    '제조 불량 원인 분석의 실제 Task는 “Analyze production quality defects and root causes”다. Q1 첫 회차의 “답변 품질의 일관성” 관점에서는 Dense 2위, BM25 63위, 하이브리드 14위였다. 따라서 최종 결합 순위가 Top20 밖이더라도 개별 관점의 상위 후보에는 여전히 남는다. 품질이라는 표현만으로 고객 답변 업무와 제조 불량 분석의 기능 일치를 확정할 수 없다는 후속 매핑 과제를 보여준다.','',
    '## ④ 어떤 문제가 남았는가?','',
    '확인된 사실은 다음과 같다.','',
    f"- BM250점 사례는 원질문당 평균{statistics.mean(x['zero_score_cases'] for x in ties if x['scope']=='original'):.1f}/112개, 관점당 평균{statistics.mean(x['zero_score_cases'] for x in ties if x['scope']=='dynamic'):.1f}/112개였다. 각 검색에서BM25 상위20개 자체는 모두 양수 점수였다.",
    '- HR 사례는 한국어 질문과 일치하는 BM25 토큰이 없어서0점·83위였다.0점 사례끼리의 순위는 기존과 같은ID 순이다. 이 순위가 낮다는 이유로 실제업무가 무관하다고 판정한 것은 아니다. 고정50% 비중의 순위 결합에서 불리한 경로가 더해졌음을 보여준다.',
    '- D/E와 기존 평균RRF 전체순위가 같아, 현재 맞춘 비교의 변화는 BM25 채널을 추가한 데 따른 것이다. 관점생성이나 P/T/C 가중치를 동시에 바꾸지는 않았다.',
    '- 후보합집합은 기존에도112개였다. 후보 수 자체는 늘지 않았고, 최종상위권의 관련 발견·순위가 실제로 달라졌다. 전체후보에정답이모두있다는자명한사실을 Recall 개선으로세지않았다.','',
    '추가 검증이 필요한 가설도 있다. 한국어 질문과 일부영어본문의 어휘 불일치, 자주 나오는 일반어의 영향,0점동점순서가 하락에 얼마나 기여했는지는 이번에 각각바꾸어분리하지않았다. 번역·토큰화·비중조정을하면좋아진다고단정하지않는다. 한가지50:50조건의하락을모든하이브리드검색의실패로일반화하지않는다.','',
    '## ⑤ 교수님 피드백에 얼마나 부합하는가?','',
    '원질문10개·관점108개에서 Dense와BM25 모두전체112개를 검색하고, 관점별 결과를 분리 보존했다. 먼저Top10/20으로 자르지 않았다. 후보ID를 중복 없이 묶고 검색 경로·순위·점수·원문근거로 이어지게 했다.','',
    '하지만 후보가 충분하다고 최종 추천이 정확한 것은 아니다. 이번은 후보 확보와순위결합을평가한것이며 Query–Case 정밀매핑을구현한것이아니다. RRF60·50:50은이번고정실험조건으로교수님이직접승인한최적값이라고표현하지않는다.','',
    '## ⑥ Query–Case 정밀 매핑은 어떻게 개발해야 하는가?','',
    '정밀매핑알고리즘은개발하지않고입력자료와계약만정리했다.','',
    '|자료|역할|','|---|---|',
    '|query_registry.json|원질문·관점·검색문장·관점원문근거를path_id로관리|',
    '|case_registry.json|112사례의원본Problem·Task·Context와출처근거ID|',
    '|candidate_features.jsonl|26432행:경로·구조·사례별Dense/BM25점수·순위·일치토큰·RRF기여|',
    '|mapping_candidate_pools.jsonl|80개하이브리드질문회차의전체112후보와최종검색순위·출처경로|',
    '|mapping_schema.json / mapping_input_examples.json|모델이나API없이구성한입력계약·6개예시;정답은제외|','',
    '다음에는 실제Task와Context에서 수행한 행동·대상·산출물을 확인하고, 원질문 전체와 개별관점의 관련성을 분리하는 구조가 필요하다. Problem의필요작업을실제수행으로추측하지않고,업종이다르더라도동일한업무기능이면인정해야한다. 검색점수나단어일치만으로기능일치를확정하지않는다.','',
    '현재Silver는전체질문단위이며108관점별정답이아니다. 전체질문의양성라벨을모든관점에복제하지말아야한다. 원문인용과출처위치를남기고,기능매핑의출력은UNASSESSED상태로비워뒀다. 개발·검증은질문/출처그룹을나누어설계해야한다. 이번에매핑점수나새로운AI판단을만들지않았다.','',
    '## ⑦ 최종 결론','',
    '**이번조건에서는 Dense+BM25가 Dense단독보다 유리하지 않았다.** 도움말센터처럼 실제로순위가개선된사례도있지만, 더많은관련사례가낮아져 모든맞춘조건의MacroF1이감소했다. 충분한후보보존의조건은지켰으나,최종순위의기능적정확성을보장하지는못했다.','',
    '이결과는동일모델3회중앙값AI-Silver의18양성쌍과개발질문10개에대한관찰이다.4개질문은무양성이라Recall/F1을평가하지못한다. 사람Gold나독립Test에서의효과로주장하지않는다. 기존평가의보수성·잠재적거짓음성도이번에수정하지않았다.','',
    '**API호출0·키접근0·추가Dense임베딩0·비용$0.00**. Stage4는열람하지않았다. 계산중Python네트워크연결을차단했고원본해시를검사했다. 과거실험은덮어쓰지않았다.','',
    '기술적사전검사에서bm25.py의기존Windows CRLF와Git LF가달라원본불일치로표시됐다. Git필터된blob이동일함을확인하고소스파일만줄바꿈을정규화해검사하도록고쳤다. 코드나데이터를다시쓰지않았고,데이터·Silver·임베딩·순위는계속바이트단위로검사한다. `preflight_repair.json`에기록했다.','',
    '재현: `PYTHONPATH=src;.`에서 `python -m scripts.dense_bm25_candidates run`, `python -m scripts.dense_bm25_analysis`, `python -m scripts.dense_bm25_verify`와 `python -m pytest tests/test_dense_bm25_candidates.py -q`. API키가필요없다. 설정은 `configs/dense_bm25_candidates_20261027.json`, 전체성능·질문별결과는 `macro_metrics.csv`, `query_run_metrics.csv`, `question_summary.json`, 검산은 `verification.json`이다.']
    lines.extend(['','자동 검증: 신규 단위 테스트 8개 통과(test_results.json). 별도 scalar 식으로 BM25 13,216점, Decimal 계산으로 236개 경로·200개 최종 순위·600개 지표·90개 Macro 값을 검산했다(verification.json). 핵심 결과 6종은 재실행 해시도 같았다(reproducibility.json). 비밀정보 검사는 업로드 대상의 알려진 키 패턴과 금지 경로를 검사하며 환경변수의 키 값을 읽지 않는다(security_scan.json).'])
    (c.OUT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    c.save('final_status.json',{'status':'LOCAL_HYBRID_CANDIDATE_EXPERIMENT_COMPLETE','base_commit':c.CFG['base_commit'],'branch':c.CFG['branch'],'preregistration_commit':c.read(c.OUT/'preregistration.json')['config_preregistration_commit'],'primary_conditions':['A','B','C','D','E','F'],'supplementary_conditions':['S_C3','S_F3','S_BM25_O','S_BM25_M'],'original_queries':10,'perspectives':108,'bm25_query_paths':118,'candidate_feature_rows':26432,'handover_pools':80,'candidates_each_path':112,'api_calls':0,'key_reads':0,'new_dense_embeddings':0,'api_cost_usd':'0.00','silver_sha256':r['silver_sha256'],'stage4_access':False,'mapping_algorithm_implemented':False,'human_gold':False,'conclusion':'Fixed50:50 Dense+BM25 reduced MacroF1 for all matched backbones/scopes and K, with some individual rank gains. Candidate completeness alone did not improve final-K performance.'})
    print({'hybrid_event_summary':summary,'original_complementarity':origcomp})
if __name__=='__main__':main()
