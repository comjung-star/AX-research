"""Stages2/3 only: reads label-free frozen handover, never Silver."""
import argparse
import csv
import hashlib
import json
import socket
import subprocess
from collections import Counter
from pathlib import Path
from ax_research.functional_mapping import extract,case_profile,compare,ranking_key

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'configs/functional_mapping_20261028.json'
CFG=json.loads(CONFIG.read_text(encoding='utf-8-sig'))
OUT=ROOT/CFG['output'];IN=ROOT/CFG['inputs']
INPUTS=[IN/n for n in ('query_registry.json','case_registry.json','candidate_features.jsonl','mapping_candidate_pools.jsonl','mapping_schema.json','mapping_input_examples.json')]

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def jsonl(name,rows):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='\n') as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
def lines(name):
    with (OUT/name).open(encoding='utf-8') as f:return [json.loads(l) for l in f]
def block(*a,**k):raise RuntimeError('Network disabled in functional mapping')

def prepare():
    inputs=[]
    for p in INPUTS:
        rel=p.relative_to(ROOT).as_posix();raw=subprocess.check_output(['git','show',CFG['base_commit']+':'+rel],cwd=ROOT)
        assert p.read_bytes()==raw,'Frozen input changed: '+rel
        inputs.append({'path':rel,'sha256':sha(p)})
    d={'base_commit':CFG['base_commit'],'config_sha256':sha(CONFIG),'inputs':inputs,'config_commit':subprocess.check_output(['git','log','-1','--format=%H','--',str(CONFIG.relative_to(ROOT))],cwd=ROOT,text=True).strip(),'api_calls':0,'key_reads':0,'independent_test_access':False}
    p=OUT/'manifest.json'
    if p.exists():assert read(p)==d
    save('manifest.json',d)

def stage2():
    prepare();queries=read(IN/'query_registry.json')['paths'];cases=read(IN/'case_registry.json')['cases']
    assert len(queries)==118 and len(cases)==112
    pools=[json.loads(l) for l in (IN/'mapping_candidate_pools.jsonl').open(encoding='utf-8')]
    assert len(pools)==80 and all(len(p['candidate_ids_ranked_all112'])==112 and set(p['candidate_ids_ranked_all112'])==set(cases) for p in pools)
    # Validate handover join keys and branch-origin quotations before semantic processing.
    features=0
    for l in (IN/'candidate_features.jsonl').open(encoding='utf-8'):
        row=json.loads(l);assert row['path_id'] in queries and row['case_id'] in cases;features+=1
    assert features==26432
    for p in queries.values():
        if p['scope']=='dynamic':assert p['perspective']['source_quote'] in p['original_query']
    qp={p:extract(x['query_text'],CFG) for p,x in queries.items()};cp={cid:case_profile(x,CFG) for cid,x in cases.items()}
    save('stage2/query_profiles.json',qp);save('stage2/case_profiles.json',cp)
    rows=[]
    for pid,q in qp.items():
        meta=queries[pid]
        for cid,case in cp.items():
            rows.append({'path_id':pid,'qid':meta['qid'],'repeat':meta['repeat'],'scope':meta['scope'],'perspective_id':meta['perspective_id'],'case_id':cid,**compare(q,case),'evidence_links':{'query_profile':'query_profiles.json#'+pid,'case_profile':'case_profiles.json#'+cid,'query_text_source':CFG['inputs']+'/query_registry.json','case_ptc_source':CFG['inputs']+'/case_registry.json','evidence_ids':cases[cid]['evidence_ids']}})
    jsonl('stage2/mappings.jsonl',rows)
    lookup={(r['path_id'],r['case_id']):r for r in rows};pathrank=[]
    pathfeatures={}
    for line in (IN/'candidate_features.jsonl').open(encoding='utf-8'):
        f=json.loads(line);pathfeatures.setdefault((f['path_id'],f['backbone']),{})[f['case_id']]=f
    for (pid,backbone),feat in pathfeatures.items():
        ranked=sorted(cases,key=lambda cid:(-lookup[pid,cid]['mapping_grade'],-feat[cid]['hybrid_rrf_score'],cid))
        pathrank.append({'path_id':pid,'backbone':backbone,'ranking':ranked,'mapping_grade':{cid:lookup[pid,cid]['mapping_grade'] for cid in ranked},'dense_rank':{cid:feat[cid]['dense_rank'] for cid in ranked},'bm25_rank':{cid:feat[cid]['bm25_rank'] for cid in ranked},'hybrid_rank':{cid:feat[cid]['hybrid_rank_within_path'] for cid in ranked},'role':'Branch diagnostic; final recommender separately combines whole and branch evidence.'})
    save('stage2/branch_rankings.json',{'paths':pathrank,'candidate_count':112})
    unknown=[{'case_id':cid,'task':cases[cid]['task'],'status':v['task']['status'],'held_clauses':v['task']['held_clauses']} for cid,v in cp.items() if not v['task']['function_ids'] or v['task']['held_clauses']]
    q_unknown=[{'path_id':pid,'query_text':queries[pid]['query_text'],'status':p['status']} for pid,p in qp.items() if not p['function_ids']]
    save('stage2/unresolved.json',{'cases':unknown,'queries':q_unknown,'note':'Grammar coverage/negation limits; not proven irrelevant. Task/Context not independently source-audited.'})
    save('stage2/status.json',{'stage':'stage2_functional_mapping','complete':True,'mapping_rows':len(rows),'paths':len(qp),'cases':len(cp),'task_recognized':sum(bool(x['task']['function_ids']) for x in cp.values()),'query_paths_recognized':sum(bool(x['function_ids']) for x in qp.values()),'grade_distribution':dict(Counter(x['mapping_grade'] for x in rows)),'status_distribution':dict(Counter(x['status'] for x in rows)),'api_calls':0,'silver_input':False,'training':False,'semantic_accuracy_established':False})
    targets=['AXV2N_0121','AXV2N_0124','AXV2C_0093_01']
    save('stage2/mandatory_cases.json',{'records':[{'case_id':cid,'ptc':{k:cases[cid][k] for k in ('problem','task','context')},'whole_mapping':lookup['o_V21D001',cid],'perspectives':[r for r in rows if r['qid']=='V21D001' and r['scope']=='dynamic' and r['case_id']==cid]} for cid in targets],'selected_by_user_before_experiment':True,'labels_used':False})
    (OUT/'stage2/README.md').write_text('''# Stage2: 원문 기능 매핑 실험

원질문10개와 기존108관점을 각각112사례에 비교해13,216행을 만들었다. 행동+대상을 같은 Task 구절에서 확인하는18종 문법이며, 단순 검색점수의 이름을 바꾼 것이 아니다. Task 원문 위치와 기능 생산규칙이 점수의 근거다. 산출물은 작업 동사에서 정한 유형이며 실제 산출물 원문을 별도로 확인한 것은 아니다. 점수는 규칙 근거 강도이지 Silver 관련도나 확률이 아니다.

매핑 점수3 이상은 같은 기능 유형,4는 Task 대상 영역과 추가 Problem/Context 기능 근거도 공유한 경우다.2는 행동만 부분적으로 겹친 경우,1은 대상 영역만 겹친 경우다.0이나UNKNOWN을 실제 무관 정답으로 사용하지 않는다. 원질문에서 인식한 기능 중 미일치 목록을 별도로 남긴다.

118경로 중71경로,112사례 중79사례의Task에서 기능을 인식했다. 미인식33사례·47경로는 후보에서 제외하지 않았다. 전체7,607행은 한쪽 이상의 기능을 못 읽어UNKNOWN이다. 출력 파일이 완성됐다는 것과 실제 의미 정확도가 검증됐다는 것은 다르다.

고객문의 Q1에 대해 도움말센터/HR규정 질의응답 모두3점, 제조 불량 원인분석0점이다. 이는 사용자가 사전에 지정한 진단 사례이며 독립 시험이 아니다. 각 관점의 점수는 mandatory_cases.json에서 구분한다. 답변 품질 같은 표현에 행동·대상 조합이 없으면 임의로 원질문 기능을 복제하지 않는다.

Task에 없는 기능을 Problem이나Context만 보고 인정하지 않는다. 이는 추측을 줄이지만 짧은Task가 실제 기능을 충분히 적지 않은 경우 놓칠 수 있다. 문법은 의미 관계를 완벽하게 이해하지 못하며 수식 범위·대상 연결을 오인할 수 있다. 예를 들어 상품데이터 연결이라는 표현은 데이터통합으로도 읽힐 수 있다. 원질문Q5는 기능을 인식하지 못했다. 임계값이나 사전을 성능을 보고 수정하지 않는다.

query_profiles.json/case_profiles.json에 실제 텍스트와 인용 위치, mappings.jsonl에 전 조합의6개 기준·부분 기능·근거 링크, branch_rankings.json에236개 관점/구조별112순위와 기존검색순위를 보존했다. unresolved.json에 보류 목록, status.json에 실행 통계를 남겼다. 예전 evidence_ids는 출처 식별자이며 이번에 원 출판물의 사실성을 재검증했다는 뜻은 아니다.

모델 학습·API·키읽기·Silver입력·독립Test접근0. 새 함수가 모든 업무 의미를 신뢰성 있게 판별한다는 결론은 내리지 않는다. Stage3는 이 제한을 가진 비학습 실험의 최종 후보를 생성한다.
''',encoding='utf-8')
    print(read(OUT/'stage2/status.json'))

def stage3():
    prepare();queries=read(IN/'query_registry.json')['paths'];cases=read(IN/'case_registry.json')['cases']
    mappings={(r['path_id'],r['case_id']):r for r in lines('stage2/mappings.jsonl')}
    feature={(r['path_id'],r['backbone'],r['case_id']):r for r in [json.loads(l) for l in (IN/'candidate_features.jsonl').open(encoding='utf-8')]}
    pools=[json.loads(l) for l in (IN/'mapping_candidate_pools.jsonl').open(encoding='utf-8')]
    names={'C':'M_O_SINGLE','F':'M_D_SINGLE','S_C3':'M_O_THREE','S_F3':'M_D_THREE'}
    systems={name:[] for name in names.values()};recommendations=[]
    for pool in pools:
        cond=names[pool['condition']];qid=pool['qid'];rep=pool['repeat'];ids=pool['candidate_ids_ranked_all112'];op='o_'+qid
        def pair(cid):
            branches=[mappings[p,cid] for p in pool['path_ids'] if queries[p]['scope']=='dynamic']
            return mappings[op,cid],branches
        ranking=sorted(ids,key=lambda cid:ranking_key(*pair(cid),pool['final_retrieval_score'][cid],cid))
        best={cid:max((x['mapping_grade'] for x in pair(cid)[1]),default=0) for cid in ids}
        row={'qid':qid,'repeat':rep,'ranking':ranking,'top_k':{str(k):ranking[:k] for k in CFG['K']},'path_ids':pool['path_ids'],'whole_path_id':op,'retrieval_reference':pool['condition'],'whole_grades':{cid:pair(cid)[0]['mapping_grade'] for cid in ids},'best_perspective_grades':best,'candidate_count':112}
        systems[cond].append(row)
        for i,cid in enumerate(ranking,1):
            whole,branches=pair(cid);maxgrade=best[cid];winning=[x for x in branches if x['mapping_grade']==maxgrade and x['shared_functions']]
            pathfacts=[feature[p,pool['backbone'],cid] for p in pool['path_ids']]
            supported=sorted(set(whole['shared_functions'])|{f for b in winning for f in b['shared_functions']})
            reason=('실제 Task에서 '+', '.join(supported)+' 기능의 규칙 근거를 찾았습니다.' if supported else '기능 일치 근거가 충분하지 않아 추천 적합성을 확정할 수 없습니다.')
            if whole['query_uncovered_functions']:reason+=' 원질문에서 인식한 일부 기능은 이 사례로 확인되지 않았습니다.'
            recommendations.append({'condition':cond,'qid':qid,'repeat':rep,'rank':i,'case_id':cid,'case_name':cases[cid]['task'],'actual_task':cases[cid]['task'],'original_query':queries[op]['query_text'],'reason':reason,'caution':'규칙 기반 후보 순위이며 검증된 적합성/효과/보안 보장이 아님. 산출물은 기능 유형이며 별도 실제 산출물 원문 검증 없음.','whole_mapping':whole,'winning_perspective_mapping_ids':[x['path_id'] for x in winning],'winning_perspective_grades':maxgrade,'grade_used':max(whole['mapping_grade'],maxgrade),'existing_hybrid_rank':ids.index(cid)+1,'hybrid_rank_change':ids.index(cid)+1-i,'retrieval_paths':pathfacts,'evidence_ids':cases[cid]['evidence_ids'],'low_support_padding':max(whole['mapping_grade'],maxgrade)<3})
    save('stage3/rankings.json',{'systems':systems,'labels_read':False,'primary_condition':'M_D_SINGLE','recommendation_is_experimental':True})
    jsonl('stage3/recommendations.jsonl',recommendations)
    jsonl('stage3/top20_explanations.jsonl',[r for r in recommendations if r['rank']<=20])
    table=[{'condition':r['condition'],'qid':r['qid'],'repeat':r['repeat'],'rank':r['rank'],'case_id':r['case_id'],'actual_task':r['actual_task'],'whole_grade':r['whole_mapping']['mapping_grade'],'best_perspective_grade':r['winning_perspective_grades'],'related_paths':','.join(r['winning_perspective_mapping_ids']),'old_hybrid_rank':r['existing_hybrid_rank'],'reason':r['reason'],'caution':r['caution']} for r in recommendations if r['rank']<=20]
    with (OUT/'stage3/top20_explanations.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(table[0]));writer.writeheader();writer.writerows(table)
    doc=['# Stage3: 기능 근거 기반 최종 후보','',
        '주 조건 M_D_SINGLE은 원질문과 각 관점의 기능 매핑을 함께 사용한다. 관점점수를 합산하지 않고 최고 근거를 사용한다. 원질문 근거도 정렬에 남긴다. 같은 매핑 근거끼리는 기존 하이브리드 검색점수로 정렬한다. 원질문만 사용하는 조건과 3View 조건도 별도 보존했다.','',
        '전체80개 질문/회차 순위와112후보 설명을 먼저 저장했다. Silver는 아직 읽지 않았다. Top5/10/20을 동일 순위에서 자르고 ID중복을 제거했다. 기능 근거가 낮은 항목으로 채운 경우 low_support_padding=true이며 적합한 추천이라고 보증하지 않는다.','',
        '아래는 주 조건의 첫 생성 회차 Top5 예시다. 모든3회×질문×Top20의 실제Task·전체/관점근거·기존검색순위·주의사항은 top20_explanations.csv/jsonl에 있다. 상세원문 인용은 Stage2 프로필과 연결된다.','']
    for qid in sorted({r['qid'] for r in recommendations}):
        doc.extend(['## '+qid,'','|순위|사례|실제 Task|전체/관점 근거 점수|','|---:|---|---|---|'])
        for r in recommendations:
            if r['condition']=='M_D_SINGLE' and r['qid']==qid and r['repeat']==1 and r['rank']<=5:
                doc.append(f"|{r['rank']}|{r['case_id']}|{r['actual_task'].replace('|','/')}|{r['whole_mapping']['mapping_grade']}/{r['winning_perspective_grades']}|")
        doc.append('')
    (OUT/'stage3/README.md').write_text('\n'.join(doc)+'\n',encoding='utf-8')
    save('stage3/status.json',{'complete':True,'query_runs':sum(map(len,systems.values())),'systems':4,'all_candidates_explained':len(recommendations),'top20_explanation_rows':sum(r['rank']<=20 for r in recommendations),'api_calls':0,'labels_read':False,'padding_disclosed':True,'new_embeddings':0,'independent_test_access':False})
    print(read(OUT/'stage3/status.json'))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','stage2','stage3']);args=parser.parse_args()
    socket.socket.connect=block;socket.create_connection=block
    {'prepare':prepare,'stage2':stage2,'stage3':stage3}[args.stage]()
