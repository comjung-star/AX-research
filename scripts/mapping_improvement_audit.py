"""Corpus/Dev text-only diagnosis; no relevance labels or ranking inputs."""
import argparse
from collections import Counter
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))

# Analyst interpretations, not human Gold. Action/Object are literal Task spans.
NOTES={
'AXALL_US_OMB_2025_01377':('Prioritization','actionable survey comments','OUTSIDE18','의견 우선순위화는18기능에 없다. 분류나 요약으로 바꾸지 않는다.'),
'AXV24_1e31f41769aa':('재발송','송장','OUTSIDE18','기존 송장 재발송은 검색·생성·문서검증과 다른 업무다.'),
'AXV24_523997b7101f':('번역·현지화','뉴스 기사','OUTSIDE18','번역·현지화 기능이 없다. 요약과 구분해야 한다.'),
'AXV24_625513e68743':('기획','CRM 판촉 캠페인','UNDERSPECIFIED_ACTION','문안이라는 명사는 있으나 실제 작성 동작은 Task에 명시되지 않았다. 일정 처리의 세부 동작도 부족하다.'),
'AXV24_8ece01418f6d':('확인','가맹점 점포 사진','OUTSIDE18','사진 기반 등록 확인은 시각 검증이다. 문서 검증과 같은 기능으로 자동 승격하지 않는다.'),
'AXV24_918f26607568':('확인','반품 상품 사진','OUTSIDE18','사진 확인과 환불 요청 처리는 문서 검증·응답만으로 표현되지 않는다.'),
'AXV24_ec6533f5c076':('안내','고객','UNDERSPECIFIED_ACTION','여행 상황 기반 안내다. 질문 응답인지 신규 문안 작성인지 Task만으로 확정하기 어렵다.'),
'AXV24_f6f7a1e65ea7':('접수','직원 결근·지각 연락','OUTSIDE18','연락 접수·시스템 반영은 단순 질의응답이나 시스템 통합과 다르다.'),
'AXV2C_0016_01':('troubleshooting','computer','OUTSIDE18','컴퓨터 문제 해결은 품질 불량 원인 분석용 기존 문법 범위와 다르다.'),
'AXV2C_0050_02':('Discount','near-expiry food','OUTSIDE18','가격 할인은 추천이나 수량 예측이 아니다.'),
'AXV2C_0068_01':('Repair','incomplete payment instructions','OUTSIDE18','지급지시 보완은 검증 이후의 수정 작업이다. 확인과 수정 구분 필요.'),
'AXV2C_0074_02':('Review','merchant websites','LEXICAL_OBJECT','검토 동사는 기존에 있으나 웹사이트라는 문서 대상을 문법이 포함하지 않는다.'),
'AXV2H_0021_01':('예지보전','제조 로봇','COMPOUND_INSUFFICIENT_DETAIL','압축된 전문 복합어다. 어떤 데이터를 사용해 무엇을 예측하는지 별도 행동·대상 근거가 없다.'),
'AXV2H_0078_01':('조회','사내 관리데이터','LEXICAL_OBJECT','조회 동사는 있지만 데이터가 지식 검색의 대상 표현에서 빠져 있다.'),
'AXV2N_0103':('Reconcile','bank transactions','LEXICAL_OBJECT','대조 동사는 있으나 거래 기록 표현이 대상에서 빠져 있다.'),
'AXV2N_0105':('Assist','store associates','UNDERSPECIFIED_ACTION','질문 관련 직원 지원만 명시. 실제 답변·검색·조치를 무엇으로 수행하는지는 확정하기 어렵다.'),
'AXV2N_0106':('Advise','online customers','OUTSIDE18','프로젝트 조언을 질문 응답과 동일하다고 단정할 수 없다.'),
'AXV2N_0107':('Give','home-improvement project advice','OUTSIDE18','조언 제공이다. 구체적인 질의응답 동작까지 원문에서 보장하지 않는다.'),
'AXV2N_0109':('Explain','personalized job invitations','OUTSIDE18','초대 이유 설명은 기존18기능과 직접 대응되지 않는다.'),
'AXV2N_0115':('Produce','approved lifestyle images','LEXICAL_ACTION','이미지는 기존 생성 대상이지만 produce 동의어가 생성 동사에서 빠져 있다.'),
'AXV2N_0118':('Unload','cartons','OUTSIDE18','물리적 하역 기능은18개 정보업무 규칙에 없다.'),
'AXV2N_0120':('Apply','herbicide','OUTSIDE18','잡초 감지 조건에 따른 제초제 살포는 물리적 적용 작업이다. 감지를 Task의 주 동작으로만 바꾸면 안 된다.'),
'AXV2N_0128':('Check','warning-triangle placement','OUTSIDE18','물체 위치 검사는 문서 검증 대상이 아니다.'),
'AXV2N_0130':('Automate','routine support-case administration','UNDERSPECIFIED_ACTION','행정 자동화의 구체적 수행 기능이 없다. 문의 답변을 수행했다고 추정하면 안 된다.'),
'AXV2N_0132':('Document','medical-care conversations','OUTSIDE18','대화를 기록하는 업무다. 요약·전사·새 문안 생성 중 무엇인지 미확정이다.'),
'AXV2N_0133':('Investigate','escalated claim-processing questions','OUTSIDE18','보험처리 질문 조사는 제조 불량 원인 분석과 다른 대상·목적이다.'),
'AXV2P2_0019_01':('Prepare and submit','journal entries','OUTSIDE18','회계분개 작성·제출 기능이 없다. 승인 조건은 검증 수행의 증거가 아니다.'),
'AXV2P2_0020_01':('Coordinate','property insurance claim resolution','OUTSIDE18','보험 청구 해결 조정 기능이 없다.'),
'AXV2P2_0035_01':('Use AI as one reader','breast screening','OUTSIDE18','영상 판독 기능이 없다. screening을 일반 서류심사로 오인하지 않아야 한다.'),
'AXV2P2_0089_01':('Book','employee annual leave','OUTSIDE18','연차 예약·등록 업무다. 직원이라는 대상 공통점만으로 지식검색과 일치시킬 수 없다.'),
'AXV2P2_0097_01':('Depalletize','boxes','OUTSIDE18','물리적 상자 분리 기능이 없다.'),
'AXV2P2_0099_01':('Automate','steel marking','OUTSIDE18','강재 마킹 기능이 없다. 정보 생성과 물리적 표기는 구분한다.'),
'AXV2P2_0100_01':('Screen and assess','applicant self-introductions','LEXICAL_OBJECT','심사 동사가 있으나 자기소개서 표현은 기존 문서 대상에 포함되지 않았다. applicant만으로 모든 채용을 심사로 매칭하지 않는다.'),
}


def diagnostics(text,rules,executed=False):
    acts=[];objs=[];pairs=[];too_far=[];held=[]
    for clause in re.finditer(r'[^.;。；\n]+',text):
        raw=clause.group()
        if executed and re.search(rules['negation_guard'],raw,re.I):held.append(raw)
        for f in rules['functions']:
            am=list(re.finditer(f['action'],raw,re.I));om=list(re.finditer(f['object'],raw,re.I))
            if am:acts.append({'function':f['id'],'quotes':[x.group() for x in am]})
            if om:objs.append({'function':f['id'],'quotes':[x.group() for x in om]})
            for a in am:
                for o in om:
                    (pairs if max(a.end(),o.end())-min(a.start(),o.start())<=rules['max_action_object_span'] else too_far).append(f['id'])
    return {'action_hits':acts,'object_hits':objs,'joint_functions':sorted(set(pairs)),'too_far_functions':sorted(set(too_far)),'held_clauses':held,'chars':len(text),'clause_count':len(re.findall(r'[^.;。；\n]+',text))}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    base=ROOT/'docs/query-case-functional-mapping-2026-10-28';sem=ROOT/'docs/query-case-semantic-mapping-2026-10-28'
    rules=read(ROOT/'configs/functional_mapping_20261028.json');cases=read(ROOT/'docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    cp=read(base/'stage2/case_profiles.json');sp=read(sem/'mapping/case_profiles.json');qs=read(base/'stage2/query_profiles.json');reg=read(ROOT/'docs/dense-bm25-candidates-2026-10-27/query_registry.json')['paths']
    ids=[c for c,v in cp.items() if not v['task']['function_ids']];assert set(ids)==set(NOTES) and len(ids)==33
    rows=[]
    for cid in ids:
        action,obj,cause,note=NOTES[cid];c=cases[cid];text=c['task'];assert action in text and obj in text
        row={'case_id':cid,'task':text,'action':{'quote':action,'start':text.index(action),'end':text.index(action)+len(action)},'object':{'quote':obj,'start':text.index(obj),'end':text.index(obj)+len(obj)},'output':{'quote':'approved lifestyle images','status':'LITERAL_PRODUCED_OBJECT'} if cid=='AXV2N_0115' else {'quote':None,'status':'NO_SEPARATELY_EXPLICIT_OUTPUT_IN_TASK'},'context':c['context'],'primary_cause':cause,'reason':note,'diagnostics':diagnostics(text,rules,True),'B_comparable':bool(sp[cid]['fields']['task']),'B_fields':sp[cid]['fields'],'evidence_ids':c['evidence_ids'],'analysis_source':'AI analyst text interpretation; not human-Gold; structured source not original publication reverified','fix_scope':'existing18 lexical coverage candidate' if cause.startswith('LEXICAL') else 'retain UNKNOWN; outside18 or insufficient explicit functional detail'}
        rows.append(row)
    qrows=[]
    for pid,v in qs.items():
        if v['function_ids']:continue
        d=diagnostics(reg[pid]['query_text'],rules)
        qrows.append({'path_id':pid,'qid':reg[pid]['qid'],'repeat':reg[pid]['repeat'],'text':reg[pid]['query_text'],'scope':reg[pid]['scope'],'diagnostics':d,'cause':'ACTION_OBJECT_NOT_JOINT' if d['action_hits'] else 'NO_SUPPORTED_OPERATION_ACTION','interpretation':'문제·상황·목적 관점은 실행 동사를 포함하지 않을 수 있음. 미인식을 부적합·관점생성 오류로 간주하지 않음. 분산만으로 통합 수행을 추정하지 않음.'})
    assert len(qrows)==47
    summary={'cases':33,'query_paths':47,'case_cause_counts':dict(Counter(r['primary_cause'] for r in rows)),'path_cause_counts':dict(Counter(r['cause'] for r in qrows)),'B_nonempty_task':sum(r['B_comparable'] for r in rows),'negation_held_in_unknown33':sum(bool(r['diagnostics']['held_clauses']) for r in rows),'span_limit_failure_in_unknown33':sum(bool(r['diagnostics']['too_far_functions']) for r in rows),'max_unknown_task_chars':max(r['diagnostics']['chars'] for r in rows),'not_relevance_labels':True,'labels_or_rankings_read':False}
    for name,value in [('cases33.json',rows),('paths47.json',qrows),('summary.json',summary)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    doc=['# 미인식33개 전수 분석','', 'AI 분석이며 사람 정답이 아니다. 원 출판물 대신 기존 Task/Context 구조화 원문을 확인했다. 미인식은 추천 부적합을 의미하지 않는다. B의 비교 가능은 점수 산출 가능이지 정확성 보장이 아니다.','', '|사례|실제Task|행동 / 대상(원문)|Output|Context|원인 / 처리|B비교|','|---|---|---|---|---|---|---|']
    for r in rows:
        clean=lambda s:str(s).replace('|','/').replace('\n',' ')
        doc.append('|'+ '|'.join(clean(x) for x in [r['case_id'],r['task'],r['action']['quote']+' / '+r['object']['quote'],r['output']['quote'] or '명시없음; 추정하지 않음',r['context'],r['primary_cause']+': '+r['reason'],r['B_comparable']])+'|')
    (out/'cases33.md').write_text('\n'.join(doc)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()
