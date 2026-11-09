"""Freeze policy and local examples, render perspective panels, replay with saved vectors."""
import argparse
from collections import Counter
import json
import socket
import sys
import zipfile

import numpy as np

from ax_research.perspective_panels import build_panels,query_text,request_body
from scripts.perspective_panels_pilot_20261109 import selections,FIXTURES,LEGACY
from scripts.improvement_cycle import ROOT,read
from scripts.pilot_case_recommendation import inputs,LocalTaskScorer,BANKS
from scripts.pilot_perspective_selection import CATALOG
from scripts.task_alignment_20261109 import sha

OUT=ROOT/'docs/perspective-panels-pilot-20261109'
SOURCES=['src/ax_research/perspective_panels.py','configs/perspective_panels_pilot_20261109.json',FIXTURES,LEGACY,
    'scripts/perspective_panels_pilot_20261109.py','scripts/export_perspective_panels_pilot_20261109.py',
    'tests/test_perspective_panels.py','docs/perspective-panels-pilot-20261109-protocol.md',CATALOG,
    'configs/pilot_case_profiles_20261109.json','docs/dense-bm25-candidates-2026-10-27/case_registry.json',
    'scripts/pilot_case_recommendation.py','docs/task-alignment-reference-20261109/config.json']
EXTRA_BANKS=['docs/llm-catalog-retrieval-comparison-20261109/vectors.npz','docs/catalog-refinement-20261109/vectors.npz']


def save(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def load(name):return json.loads((OUT/name).read_text(encoding='utf-8'))


def frozen():
    f=load('freeze.json')
    assert all(sha(ROOT/p)==h for p,h in f['source_sha256'].items())
    assert all(sha(ROOT/p)==h for p,h in f['bank_sha256'].items())
    assert f['snapshot_sha256']==sha(OUT/'source-snapshot.zip')
    return f


def render(examples):
    lines=['# 관점별 참고 사례 표시 예시','','수동 동작 예시와 이전 실제 LLM 응답을 구분한다. 새 기준으로 LLM을 호출하거나 검색 성능을 평가한 결과가 아니다.','']
    for key,result in examples.items():
        counts=result['counts']
        lines+=['## '+key,'','> '+result['question'],'',
            '**출처:** '+('수동으로 구성한 동작 예시' if key.startswith('manual_') else '이전 실제 LLM 선택 응답; 예전 업무형 기준'),
            '',f"**표시:** 관점 {counts['perspectives']}개 / 관점별 표시 합계 {counts['display_slots']}개 / 중복 제외 사례 {counts['unique_cases']}개",'']
        for p in result['panels']:
            relation='질문에 명시된 문제·업무' if p['relation']=='QUERY_EXPLICIT' else '다른 관점에서 검토할 가설'
            lines+=['### '+p['id']+' '+p['title'],'','**연결 유형:** '+relation,
                '', '**질문 근거:** “'+p['question_anchor']['quote']+'”','',p['why_this_view'],'']
            if p['assumptions']:lines+=['**확인하지 않은 가정:**','']+['- '+v for v in p['assumptions']]+['']
            lines+=['|순위|참고 사례|다른 연결 관점|','|---|---|---|']
            for r in p['cases']:
                lines.append('|'+str(r['rank'])+'|'+r['case_id']+' — '+r['task']+'|'+(', '.join(r['also_in_perspectives']) or '없음')+'|')
            lines+=['']
            for r in p['cases']:
                lines+=['**'+r['case_id']+'를 참고하는 이유:** '+r['why_reference'],'',
                    '**차이·확인할 조건:**','']+['- '+n for n in r['conditions_to_check']]+['']
        if not result['panels']:lines+=['선택된 관점이 없어 사례를 억지로 채우지 않았다.','']
        if result['legacy_unscoped_constraints']:
            lines+=['**이전 선택기에 기록된 조건 — 적용 관점 미지정:**','']+['- '+c['quote'] for c in result['legacy_unscoped_constraints']]+['']
        if result['unsupported_work']:
            lines+=['**목록 밖 요청:**','']+['- “'+r['quote']+'”: '+r['reason'] for r in result['unsupported_work']]+['']
        lines+=['### 중복을 합친 사례 상세 근거','']
        for c,d in result['case_details'].items():
            lines+=['**'+c+'**','', '> 실제 수행 업무: '+d['source']['task'],'']
            for l in d['links']:
                lines+=['- '+l['perspective_id']+' 연결 근거: '+l['link_reason']]
                lines+=['  - '+e['field']+': “'+e['quote']+'”' for e in l['source_evidence']]
            lines+=['']
    (OUT/'examples.ko.md').write_text('\n'.join(lines),encoding='utf-8')


def generate():
    if OUT.exists():raise FileExistsError('Prior output is preserved')
    # All old frozen sources remain intact; no replacing historical experiments.
    previous=read('docs/llm-catalog-selector-20261109/final-freeze.json')
    assert all(sha(ROOT/p)==h for p,h in previous['source_sha256'].items())
    OUT.mkdir()
    with zipfile.ZipFile(OUT/'source-snapshot.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in SOURCES:z.write(ROOT/p,arcname=p)
    save('freeze.json',{'state':'FIXED_BEFORE_LOCAL_PANEL_EXAMPLES','source_sha256':{p:sha(ROOT/p) for p in SOURCES},
        'bank_sha256':{p:sha(ROOT/p) for p in BANKS+EXTRA_BANKS},'snapshot_sha256':sha(OUT/'source-snapshot.zip'),
        'new_paid_calls':0,'new_LLM_problem_mapping_executed':False,'performance_comparison_performed':False,
        'full112_expansion':False,'test15_read':False})
    accesses=[]
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes)):
            p=str(args[0]).replace('\\','/').lower()
            if any(s in p for s in ('blind_review','qrels','labels_new20','fresh-labels','ai_consensus','.ax-heldout','heldout-final-resume')):
                raise RuntimeError('No relevance labels or final test in this functional prototype')
            if p.endswith(('.json','.npz')):accesses.append(str(args[0]))
    sys.addaudithook(audit)
    def blocked(*a,**k):raise RuntimeError('No network calls in local panel examples')
    socket.socket.connect=blocked;socket.create_connection=blocked
    catalog,_,profiles,registry=inputs();chosen=selections(catalog)
    save('selections.json',chosen)
    scorer=LocalTaskScorer(registry)
    for path in EXTRA_BANKS:
        with np.load(ROOT/path,allow_pickle=False) as z:scorer.bank.update(zip(z['texts'].tolist(),z['vectors']))
    texts={registry[l['case_id']]['task'] for c in catalog['cards'] for l in c['links'] if l['status']=='SUPPORTED_FOR_PILOT'}
    cards={c['id']:c for c in catalog['cards']}
    for s in chosen.values():texts.update(query_text(s['question'],cards[d['id']]) for d in s['decisions'] if d['status']=='SELECTED')
    print('LOCAL_ONLY_NEW_STRINGS',len(texts-set(scorer.bank)),flush=True);scorer.warm(texts)
    examples={k:build_panels(s,catalog,profiles,registry,scorer) for k,s in chosen.items()}
    alltext=sorted(texts);np.savez_compressed(OUT/'vectors.npz',texts=np.array(alltext),vectors=np.array([scorer.bank[t] for t in alltext],dtype=np.float32))
    save('examples.json',examples)
    sample=chosen['manual_alternative_for_one_problem']
    save('selector-request-draft.json',{'executed':False,'request':request_body(sample['question'],catalog)})
    render(examples)
    save('run.json',{'state':'STEPS1_TO3_LOCAL_FUNCTIONAL_EXAMPLES_COMPLETE','manual_examples':6,'legacy_saved_outputs':28,
        'new_encoded_strings':len(scorer.new_vectors),'new_paid_calls':0,'new_LLM_problem_mapping_executed':False,
        'performance_comparison_performed':False,'examples_sha256':sha(OUT/'examples.json'),
        'vectors_sha256':sha(OUT/'vectors.npz'),'selections_sha256':sha(OUT/'selections.json'),
        'opened_data_paths':sorted(set(accesses))})
    print('PANELS_GENERATED',len(examples),flush=True)


def verify():
    frozen();catalog,_,profiles,registry=inputs();selected=load('selections.json');saved=load('examples.json');run=load('run.json')
    assert all(run[name+'_sha256']==sha(OUT/(name+'.json')) for name in ('examples','selections'))
    assert run['vectors_sha256']==sha(OUT/'vectors.npz')
    assert selections(catalog)==selected
    with np.load(OUT/'vectors.npz',allow_pickle=False) as z:bank=dict(zip(z['texts'].tolist(),z['vectors']))
    def scorer(p,q,ids):return {c:float(np.clip(bank[q]@bank[registry[c]['task']],-1,1)) for c in ids}
    for key,s in selected.items():
        r=build_panels(s,catalog,profiles,registry,scorer);assert r==saved[key],key
        assert r['counts']['display_slots']==sum(len(p['cases']) for p in r['panels'])
        assert r['counts']['unique_cases']==len(r['case_details'])
        assert all(len(p['cases'])<=5 for p in r['panels'])
        assert r['future_baseline_comparison']['top_k_unique']==len(r['case_details'])
    manual=saved['manual_alternative_for_one_problem']
    assert manual['counts']['display_slots']==7 and manual['counts']['unique_cases']==7
    assert next(p for p in manual['panels'] if p['id']=='P01')['assumptions']
    four=saved['manual_four_views_no_global_five'];assert four['counts']['display_slots']==17
    report={'state':'PASS_SOURCES_PANEL_COUNTS_AND_34_LOCAL_REPLAYS','examples_replayed':len(saved),
        'manual_fixtures':6,'old_LLM_outputs':28,'per_view5_verified':True,'no_global_top5':True,
        'old_inputs_unchanged':True,'new_paid_calls':0,'new_LLM_problem_mapping_executed':False,
        'performance_comparison_performed':False,'semantic_accuracy_certified':False,
        'example_sha256':sha(OUT/'examples.json')}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['generate','verify']);globals()[p.parse_args().phase]()
