"""Audit frozen C inputs. No new relevance labels, heldout data or API."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from ax_research.heldout import read,write,sha
from ax_research.semantic_mapping import aggregate,combined_score,ranking_key

ROOT=Path(__file__).resolve().parents[1]


def c0_reproduce(out):
    ret=ROOT/'docs/dense-bm25-candidates-2026-10-27';hist=ROOT/'docs/query-case-functional-mapping-2026-10-28';sem=ROOT/'docs/query-case-semantic-mapping-2026-10-28'
    load=lambda p:[json.loads(l) for l in p.read_text(encoding='utf-8-sig').splitlines() if l.strip()]
    mm={(r['path_id'],r['case_id']):r for r in load(hist/'stage2/mappings.jsonl')};ss={(r['path_id'],r['case_id']):r for r in load(sem/'mapping/mappings.jsonl')}
    queries=read(ret/'query_registry.json')['paths'];old=read(sem/'ranking/rankings.json')['systems'];previous=read(ROOT/'docs/mapping-improvement-2026-10-30/experiment/score_details.json')['records'];lookup={(r['condition'],r['qid'],r['repeat'],r['case_id']):r['combined_scores']['C0'] for r in previous}
    suffix={'C':'O_SINGLE','F':'D_SINGLE','S_C3':'O_THREE','S_F3':'D_THREE'};checked=0;rankchecks=0
    for pool in load(ret/'mapping_candidate_pools.jsonl'):
        suf=suffix[pool['condition']];op='o_'+pool['qid'];ps=[p for p in pool['path_ids'] if queries[p]['scope']=='dynamic'];scores={}
        for c in pool['candidate_ids_ranked_all112']:
            r=max([mm[op,c]['mapping_grade']]+[mm[p,c]['mapping_grade'] for p in ps]);b=aggregate(ss[op,c]['score'],[ss[p,c]['score'] for p in ps]);scores[c]=combined_score(r,b)
            assert scores[c]==lookup[suf,pool['qid'],pool['repeat'],c];checked+=1
        ranked=sorted(scores,key=lambda c:ranking_key(scores[c],pool['final_retrieval_score'][c],c))
        ref=next(r for r in old['COMB_'+suf] if r['qid']==pool['qid'] and r['repeat']==pool['repeat']);assert ranked==ref['ranking'];rankchecks+=1
    write(out/'c0_reproduction.json',{'full112_rankings_exact':rankchecks,'scores_exact':checked,'reference':'original C; not C_ALL','labels_read':False,'old_semantic_rankings_sha256':sha(sem/'ranking/rankings.json')})


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=False)
    ret=ROOT/'docs/dense-bm25-candidates-2026-10-27';hist=ROOT/'docs/query-case-functional-mapping-2026-10-28';sem=ROOT/'docs/query-case-semantic-mapping-2026-10-28'
    qs=read(ret/'query_registry.json')['paths'];cases=read(ret/'case_registry.json')['cases'];qp=read(hist/'stage2/query_profiles.json');cp=read(hist/'stage2/case_profiles.json')
    scores=read(ROOT/'docs/mapping-improvement-2026-10-30/experiment/score_details.json')['records'];rankings=read(sem/'ranking/rankings.json')['systems']
    records=[];types=Counter();promotion=[]
    for d in scores:
        q=d['qid'];cid=d['case_id'];condition=d['condition'];rep=d['repeat'];op=d['whole_path'];task=cases[cid]['task'];text=qs[op]['query_text'];qf=set(qp[op]['function_ids']);cf=set(cp[cid]['task']['function_ids']);flags=[]
        promoted=d['old_rule_strength']>d['whole_scores']['old_rule']
        sources=[{'path_id':p,'query_text':qs[p]['query_text'],'functions':qp[p]['function_ids'],**v} for p,v in d['branch_scores'].items()]
        if promoted:promotion.append({'condition':condition,'qid':q,'repeat':rep,'case_id':cid,'whole_grade':d['whole_scores']['old_rule'],'highest_grade':d['old_rule_strength'],'shared_original_case_functions':sorted(qf&cf),'branch_sources':sources})
        # Only the first category is a directly observed parser collapse. Others are distinct tasks to review, not automatic errors.
        if {'summarize_content','identify_followup'}&qf and 'validate_record' in cf and any('validate_record' in s['functions'] and re.search('검토|review',s['query_text'],re.I) for s in sources):flags.append('READING_VS_VALIDATION_RULE_CONFLATION')
        if {'retrieve_knowledge','retrieve_product'}&qf and {'diagnose_cause','forecast_quantity'}&cf:flags.append('RETRIEVAL_VS_ANALYSIS_DISTINCT_FUNCTIONS')
        if 'classify_record' in qf and 'validate_record' in cf:flags.append('CLASSIFICATION_VS_ASSESSMENT_DISTINCT_FUNCTIONS')
        if 'answer_question' in qf and re.search(r'\b(?:book|refund|repair|reconcile|unload|depalletize)\b|재발송|시스템 반영|CRM contacts',task,re.I):flags.append('ANSWER_VS_EXECUTION_DISTINCT_FUNCTIONS')
        if 'forecast_quantity' in qf and 'detect_anomaly' in cf:flags.append('FORECAST_VS_DETECTION_DISTINCT_FUNCTIONS')
        rank=next(r for r in rankings['COMB_'+condition] if r['qid']==q and r['repeat']==rep)['ranking'].index(cid)+1
        if flags:
            types.update(flags)
            records.append({'qid':q,'repeat':rep,'condition':condition,'case_id':cid,'original_text':text,'original_functions':sorted(qf),'task':task,'case_task_functions':sorted(cf),'case_context':cases[cid]['context'],'case_task_evidence':cp[cid]['task']['functions'],'branches':sources,'C_rank':rank,'old_scores':d,'types':flags,'status':'PARSER_CONFLATION_EVIDENCE' if 'READING_VS_VALIDATION_RULE_CONFLATION' in flags else 'DISTINCT_OPERATION_NOT_PROVEN_IRRELEVANT','label_basis':'Source functions and texts; not classified by Silver0'})
    write(out/'type_analysis.json',{'records':records,'type_event_counts':dict(types),'unit':'query-repeat-case over4backbones/conditions; overlapping; not unique errors','status_limit':'Parser collapse is evidence about functional categories, not human relevance Gold. Distinct tasks can be auxiliary or partial matches.'})
    write(out/'branch_promotions.json',{'records':promotion,'count':len(promotion),'labels_read':False})
    examples=[]
    for cid in ('AXV2H_0003_01','AXV2P2_0011_01'):
        examples.append(next(r for r in records if r['qid']=='V21D002' and r['case_id']==cid and r['condition']=='D_SINGLE' and r['repeat']==1))
    write(out/'mandatory_examples.json',{'records':examples,'selection':'User-specified before experiment','grade0_is_not_functional_proof':True})
    doc=['# 오탐/업무 차이 원인 분석(평가 전)','','확인한 것은 기존 구조화 Task와 프로필이다. 원 출판물 재검증이나 사람Gold가 아니다. 검토를 검증으로 합친 구현은 직접 추적했고, 다른 업무 유형은 별개 기능이라는 근거만으로 무관 정답을 만들지 않는다.','','|유형|관찰 근거|판정 범위|','|---|---|---|',
    '|읽기·요약 / 검증|Q2 핵심·후속조치 파악 관점의 검토가 보고서 검증/청구서 감사와 validate_record를 공유|실제 규칙의 기능 혼동. 원문에는 검증 요구가 없음|',
    '|조회·검색 / 분석|검색 기능 원질문과 원인분석/예측 Task를 전수 대조|다른 기능일 뿐 관련성은 별도 검토 필요|',
    '|분류 / 평가·승인|태깅 원질문과 심사·검증 Task 비교|검증을 승인 실행이라고 추정하지 않음|',
    '|안내·답변 / 실행|질문 응답과 예약/환불/회계처리 같은 명시 Task 비교|안내가 실제 시스템 실행을 했다는 근거 아님|',
    '|예측 / 탐지·모니터링|forecast_quantity와detect_anomaly 비교|예방정비를 돕더라도 현재 감지와 미래 예측을 동일 기능으로 취급하지 않음|',
    '', '## 대표 오류의 점수 기여','', '|사례|실제Task|원문규칙|관점최고규칙|원문의미|관점최고의미|C점수|C순위|','|---|---|---:|---:|---:|---:|---:|---:|']
    for x in examples:
        d=x['old_scores'];doc.append(f"|{x['case_id']}|{x['task']}|{d['whole_scores']['old_rule']}|{d['old_rule_strength']}|{d['whole_scores']['old_semantic']:.6f}|{max(v['old_semantic'] for v in d['branch_scores'].values()):.6f}|{d['combined_scores']['C0']:.6f}|{x['C_rank']}|")
    doc+=['','原문'.replace('原','원')+'을 관점에 덧붙이지 않는다. 원문 기능/관점 기능/사례 실제Task를 별도로 비교한다. 원질문은 읽기·요약·후속조치이며 관점 제목의 ‘검토’가 규칙 고득점을 만들었다. B는 기능 확률이 아닌 필드 cosine이다. C의 높은 규칙 성분0.5가 최종점수를 크게 올렸고 최고관점 규칙이 원문 저점수를 덮었다.','', '전수 기록은 type_analysis.json, 최고관점 승격은 branch_promotions.json, 원문/Task/각관점/점수 상세는 mandatory_examples.json에 있다.','', '추가로 Create CRM contacts from customer emails는 출력CRM연락처와 입력이메일이 다르지만 기존 generate_content는Create+emails를 같은 기능으로 묶는다. 이는 출력대상과 입력자료 역할을 혼동한 실제 문법 사례다. 이번 C1은 명시 from/using 기반 입력자료를 출력으로 인정하지 않는 보수적 처리를 검토한다.']
    (out/'README.md').write_text('\n'.join(doc)+'\n',encoding='utf-8',newline='\n')
    c0_reproduce(out)
    print(json.dumps({'type_counts':dict(types),'promoted_events':len(promotion),'labels_read':False},ensure_ascii=False))


if __name__=='__main__':main()
