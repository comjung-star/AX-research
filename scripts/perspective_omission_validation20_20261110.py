"""Prospective new-question validation only: immutable previous method,20 new questions."""
import argparse,json,random,zipfile
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from scripts import perspective_omission_openai_20261109 as trial

PREVIOUS=trial.OUT;ROOT=trial.ROOT;trial.guard()
OUT=ROOT/'docs/perspective-omission-validation20-20261110'
api=trial.api;api.OUT=OUT;api.BUDGET=25.
read=trial.read;save=trial.save;sha=trial.sha
trial.OUT=OUT
N=20

TOPICS=[
 '여러 지점의 고객답변이 다르고 부서 인계마다 같은 확인이 반복되는 고객지원 증상',
 '신규 직원이 업무지침을 찾기 어렵고 숙련자에게 질문이 몰리는 업무 인수인계 증상',
 '사업부 문서 승인 때 과거 검토근거를 찾느라 지연되고 같은 검토가 반복되는 증상',
 '협력사 자격 증빙과 검토 이력이 흩어져 보완요청과 재확인이 반복되는 증상',
 '보험 접수 첨부서류에서 필요한 내용을 다시 옮기다가 오류와 재작업이 생기는 증상',
 '대출 신청자료의 항목 오류와 누락이 뒤 단계에서 발견돼 접수가 되돌아오는 증상',
 '지원사업 예산과 제출증빙의 기준 적용이 담당자마다 달라 재검토하는 증상',
 '상품 공급업체별 표기 차이로 채널마다 제품정보가 달라 반복 수정하는 증상',
 '채용 지원자료와 증빙 확인이 오래 걸리고 처리상태 문의도 반복되는 증상',
 '운송비 청구 내역이 계약조건과 달라 분쟁 근거를 매번 찾는 증상',
 '무역 거래 서류의 불일치를 늦게 발견하고 과거 검토근거를 찾기 어려운 증상',
 '의료 의뢰정보가 불완전해 재확인과 예약안내 문의가 반복되는 운영 증상',
 '온라인 주문상태 확인, 반품 사유정리, 고객 답변작성의 복합업무를 명시',
 '설비 안전감사 관련 문서 정리와 기준 대조, 후속 조치 기록의 복합업무를 명시;물리 영상검사는 아님',
 '출장 경비 증빙 검토와 예외기준 설명, 직원 문의 대응의 복합업무를 명시',
 '기술지원 문의내용 분류와 제품지식 조회, 답변근거 공유의 복합업무를 명시',
 '문서검색/고객챗봇을 제외하고 물리 제품 영상에서 결함을 찾는 검사사례만 명시 요청',
 '문서검색/문의자동화를 제외하고 재고 수요예측과 발주량 결정의 실제사례만 명시 요청',
 '문서처리를 제외하고 실제 운송 경로 최적화/배차 계획 사례만 명시 요청',
 '문서검색/고객챗봇을 제외하고 보안 로그의 침입징후 탐지 사례만 명시 요청',
]

def now():return datetime.now(timezone.utc).isoformat()
def guard():
    f=read(OUT/'freeze.json')
    assert all(sha(ROOT/p)==h for p,h in f['sha256'].items()),'Frozen method changed'
    assert sha(OUT/'protocol.json')==f['protocol_sha256']
trial.guard=guard

def freeze():
    assert not (OUT/'freeze.json').exists()
    old=read(PREVIOUS/'freeze.json');assert all(sha(ROOT/p)==h for p,h in old['sha256'].items())
    protocol={
      'purpose':'Question-generalization validation of unchanged omission-review method, not new-case-dataset generalization.',
      'client_date':'2026-11-10 Asia/Seoul','n_fresh_questions':20,'previous_experiment':str(PREVIOUS.relative_to(ROOT)),
      'method':'Exactly unchanged previous selector prompt/schema/normalizer,49record53link catalog,112record corpus,basePTC and Task branch scorers,top5preservation and perview5.',
      'conditions':read(PREVIOUS/'protocol.json')['conditions'],
      'equal_counts':'For each question,U=union(basic5,MAINbranches,ADDITIONALbranches). A baselineTopU;B base5+MAIN thenfillbaseline toU;C preserved union. No globalcut.',
      'question_authoring':'4 independent source-blind API requests,5 questions each. No corpus/cards/old questions/labels/ranks/scores transmitted. Settings chosen before any new text/results. All20retained; no favorable rewrites.',
      'author_topics':TOPICS,'strata':'12 symptoms,4 explicit multiwork,4 explicit targets. Author-specified categories are not human Gold. Target tasks may be outside catalog or corpus.',
      'model':'gpt-5.4','effort':'medium','selector_cap':6144,'judge_cap':12288,'workers':4,
      'author_cap':4096,'judge':'Unchanged prompt and schema; all112 cases/question,random28-case batches;one common label set forA/B/C. No ranks/roles/selected cases sent to evaluator.',
      'random_seed':'20261109+question numeric suffix; previous method unchanged','relevant_threshold':2,
      'primary':'C_REVIEW vs B_MAIN macroF1; secondary CvsA. Also precision,recall,view coverage,question wins/ties/losses,useful gains/losses,source group counts.',
      'empty_gold':'All cases still judged and all20 questions retained. F1/Recall undefined if no grade>=2; report those questions and returned irrelevant counts separately; never count as wins.',
      'uncertainty':'Question pairedbootstrap10000 seed20261109. Leave-one-out descriptive sensitivity for primary effect; same-model synthetic labels, no final human-grounded proof.',
      'decision_policy':{
        'default_C_preliminary':'Primary mean>0,95%bootstrap lower>0,useful gains>losses,atleast3 improving questions,wins>losses,and CmeanF1>=A. Evidence remains preliminary.',
        'optional_C':'Positive primary mean or mixed local gains but stability criteria not met; no claim of consistent added benefit.',
        'default_B_if_no_added_evidence':'Primarymean<=0; do not claim review benefit. If Bmean<A, prefer A among measured defaults rather than recommend a worse result.',
        'diversity':'Report independently judged coverage even when it declines; never infer diversity gain from number of generated roles.'},
      'stop':'One frozen20-question run; no prompt/ranker/threshold/model edits after outcomes, no regrading valid responses to match, no question exclusion after outcomes. Atmostone identical technical recovery,credit error stops new groups.',
      'not_final_test':'This20-set is validation to decide default/optional behavior. Do not reuse it as an untouched final test after model selection. Existing Test15 stays sealed.',
      'budget_usd':25,'only_provider':'openai','source_limits':'Same corpus112IDs/83sourcegroups,49linkedcases53links,source summaries not publisher re-audit. No training or original Gold labels imported.',
    }
    save(OUT/'protocol.json',protocol)
    paths={p for p in old['sha256']}|{str(Path(__file__).relative_to(ROOT)),str((PREVIOUS/'freeze.json').relative_to(ROOT)),str((PREVIOUS/'protocol.json').relative_to(ROOT))}
    save(OUT/'freeze.json',{'at':now(),'sha256':{p:sha(ROOT/p) for p in sorted(paths)},'protocol_sha256':sha(OUT/'protocol.json'),'fresh_questions_existed':False})
    with zipfile.ZipFile(OUT/'frozen-source-snapshot.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(paths):z.write(ROOT/p,p)
        z.write(OUT/'protocol.json','protocol.json');z.write(OUT/'freeze.json','freeze.json')
    print('FROZEN_UNCHANGED_METHOD_BEFORE20QUESTION_AUTHORING',flush=True)

def author():
    guard();jobs=[];allids=[f'VQ{i:03}' for i in range(1,N+1)]
    system='한국어 기업 운영문제 질문 작성자입니다. 실제 자료·관점목록·기존질문·답·실험방법·점수는 받지 않습니다. 각 주제에 대해2~3문장의 자연스러운 기업 AX 참고 사례 요청을 작성하세요. 증상형 주제는 AI해결책·수단을 미리 정하지 않고 실제 업무 어려움을 설명하세요. 명시 업무형은 주어진 업무만 분명히 요청하세요. 사례의 실제성과·기업명·수치를 만들지 말고 정답·관점ID를 쓰지 마세요. 지정된5개ID순서대로 질문5개만 반환하세요.'
    for i in range(0,N,5):
        ids=allids[i:i+5]
        sch=api.obj({'questions':{'type':'array','items':api.obj({'id':{'type':'string','enum':ids},'question':api.STR})}})
        payload={'ids':ids,'settings':TOPICS[i:i+5]};jobs.append((f'author_{i//5:02}',system,payload,sch,4096))
    trial.execute(jobs,'author');qs=[]
    for ident,*_ in jobs:
        r=read(OUT/f'api/openai_{ident}.json');assert r['status']=='VALID_JSON';rows=r['parsed']['questions'];assert len(rows)==5;qs+=rows
    assert len(qs)==N and [q['id'] for q in qs]==allids
    save(OUT/'fresh-questions.json',{'questions':qs,'author_saw_case_corpus':False})
    older=[]
    for path in [PREVIOUS/'fresh-questions.json',trial.PREVIOUS/'fresh-questions.json']:
        older += [q['question'].strip() for q in read(path)['questions']]
    save(OUT/'question-authorship-audit.json',{'count':N,'distinct_exact_texts':len({q['question'].strip() for q in qs}),
        'exact_overlap_known16':[q['id'] for q in qs if q['question'].strip() in older],
        'no_rewrite_or_replacement':True,'question_family_overlap_possible':True,'unbiased_real_user_sample':False})
    print('AUTHORED20_ALL_RETAINED',flush=True)

def select():guard();trial.select_questions(read(OUT/'fresh-questions.json')['questions'],'fresh')
def rank():guard();trial.rank_questions(read(OUT/'fresh-questions.json')['questions'],read(OUT/'fresh-selections.json'))

def verify():
    guard();ranks=read(OUT/'rankings.json');f=read(OUT/'rank-freeze.json');assert len(ranks)==N
    assert sha(OUT/'rankings.json')==f['rankings_sha256'] and sha(OUT/'vectors.npz')==f['vectors_sha256']
    cat,reg,profiles=trial.sources();ss=read(OUT/'fresh-selections.json')
    with np.load(OUT/'vectors.npz',allow_pickle=False) as a:bank=dict(zip(a['texts'].tolist(),a['vectors']))
    def score(p,t,ids):return {c:float(np.clip(bank[t]@bank[reg[c]['task']],-1,1)) for c in ids}
    for q,row in ranks.items():
        question=row['question'];scores={c:float(np.mean([bank[question]@bank[r[f]] for f in ('problem','task','context')])) for c,r in reg.items()};order=sorted(reg,key=lambda c:(-scores[c],c));assert order==row['base_order']
        replay=trial.build_variants(ss[q],cat,profiles,reg,score,order);replay.update({'question':question,'base_order':order,'base_scores':scores});assert replay==row
        assert len({len(set(v)) for v in row['sets'].values()})==1
        for v in row['sets'].values():assert set(row['base5'])<=set(v)
        assert set(row['main_cases'])<=set(row['sets']['B_MAIN'])&set(row['sets']['C_REVIEW'])
    before=read(OUT/'metrics.json');trial.evaluate();assert read(OUT/'metrics.json')==before
    save(OUT/'verification.json',{'status':'PASS_ALL20_REPLAYS_EQUAL_UNIQUE_COUNTS_BASE5_MAIN_AND_METRIC_RECOMPUTATION','questions':N,'verification_api_calls':0,'Test15_opened':False});print('VERIFIED20',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','author','select','rank','judge','collect','evaluate','verify']);a=p.parse_args()
    {'freeze':freeze,'author':author,'select':select,'rank':rank,'judge':trial.judge,'collect':trial.collect,'evaluate':trial.evaluate,'verify':verify}[a.action]()
