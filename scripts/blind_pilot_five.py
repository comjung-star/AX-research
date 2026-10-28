"""New-question adapter for FROZEN A/B/C. No API, labels or tuning."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import random
import socket
import subprocess
from fractions import Fraction
from pathlib import Path
import numpy as np
from ax_research.functional_mapping import extract,compare,case_profile,ranking_key as rule_key
from ax_research.semantic_mapping import field_profile,compare_fields,combined_score,ranking_key
from ax_research.retrieval.bm25 import KiwiTokenizer

ROOT=Path(__file__).resolve().parents[1];CONFIG=ROOT/'configs/blind_pilot_five_20261028.json'
CFG=json.loads(CONFIG.read_text(encoding='utf-8-sig'));OUT=ROOT/CFG['output']
SEM=ROOT/'docs/query-case-semantic-mapping-2026-10-28';HIST=ROOT/'docs/query-case-functional-mapping-2026-10-28';RETR=ROOT/'docs/dense-bm25-candidates-2026-10-27'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as s:
        for block in iter(lambda:s.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
def save(name,obj):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def csvsave(name,rows):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8-sig',newline='') as s:
        w=csv.DictWriter(s,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def blocked(*a,**k):raise RuntimeError('Pilot network disabled; no remote model/API access')
def settings():return read(ROOT/'configs/semantic_mapping_20261028.json'),read(ROOT/'configs/functional_mapping_20261028.json')
def protected():
    return [ROOT/p for p in ['configs/semantic_mapping_20261028.json','configs/functional_mapping_20261028.json','src/ax_research/semantic_mapping.py','src/ax_research/functional_mapping.py','src/ax_research/retrieval/bm25.py','data/v2_5/research/evidence_catalog.jsonl','data/v2_5/research/dev_queries.json','docs/stage123-openai-triplicate-2026-10-27/embeddings.npz']]+[SEM/p for p in ['preregistration.json','mapping/case_profiles.json','mapping/embeddings.npz','mapping/unknown33.json']]+[HIST/'stage2/case_profiles.json',RETR/'case_registry.json',RETR/'bm25_corpus_statistics.json']

def freeze():
    config,rules=settings();inputs={}
    for p in protected():
        rel=p.relative_to(ROOT).as_posix();old=subprocess.check_output(['git','show',CFG['base_commit']+':'+rel],cwd=ROOT)
        raw=p.read_bytes();assert raw.replace(b'\r\n',b'\n')==old.replace(b'\r\n',b'\n'),rel
        inputs[rel]=sha(p)
    model=(ROOT/config['model_path']).resolve();old=read(SEM/'preregistration.json')
    model_hashes={n:sha(model/n) for n in old['model_sha256']};assert model_hashes==old['model_sha256']
    versions={n:importlib.metadata.version(n) for n in old['packages']};assert versions==old['packages']
    state={'config_sha256':sha(CONFIG),'adapter_sha256':sha(Path(__file__)),'frozen_inputs':inputs,'model_hashes':model_hashes,'packages':versions,'base_commit':CFG['base_commit'],'question_freeze_commit':subprocess.check_output(['git','log','-1','--format=%H','--',str(CONFIG.relative_to(ROOT))],cwd=ROOT,text=True).strip(),'api_calls':0,'key_reads':0,'human_grades_created':0,'sealed_test_access':False}
    if (OUT/'freeze.json').exists():assert read(OUT/'freeze.json')==state,'Frozen adapter/input drift'
    save('freeze.json',state);save('questions.json',{'questions':CFG['questions'],'locked':True,'purpose_sample_not_final_test':True})
    cases=read(RETR/'case_registry.json')['cases'];oldqueries=read(ROOT/'data/v2_5/research/dev_queries.json')['queries']
    save('question_overlap.json',{'exact_old_query_matches':[(q['qid'],o['query_id']) for q in CFG['questions'] for o in oldqueries if q['text']==o['query']],'verbatim_task_substrings':[(q['qid'],cid) for q in CFG['questions'] for cid,c in cases.items() if c['task'] in q['text']],'semantic_overlap_review':'See protocol.md preregistered qualitative comparisons. Q14 notably overlaps old Q8/Q10; other queries share contexts/partial functions. Not randomized independent generalization.','authorship':'User-supplied intentional probe questions; no claim of provenance-independent question design.'})
    print('Freeze verified',len(inputs),'inputs; 5 exact user questions.',flush=True)

def run():
    freeze();config,rules=settings();cases=read(RETR/'case_registry.json')['cases'];ids=sorted(cases)
    cp=read(SEM/'mapping/case_profiles.json');rp=read(HIST/'stage2/case_profiles.json')
    assert len(ids)==112 and all(field_profile(c['task'],config,rules['negation_guard'],executed=True,context=c['context'])==cp[cid] for cid,c in cases.items())
    assert all(case_profile(c,rules)==rp[cid] for cid,c in cases.items())
    qp={q['qid']:field_profile(q['text'],config,rules['negation_guard']) for q in CFG['questions']}
    rq={q['qid']:extract(q['text'],rules) for q in CFG['questions']}
    z=np.load(SEM/'mapping/embeddings.npz');emb=dict(zip(z['texts'].tolist(),z['vectors']))
    texts=sorted(({q['text'] for q in CFG['questions']}|{v for p in qp.values() for v in p['fields'].values() if v})-set(emb))
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
    import torch
    from sentence_transformers import SentenceTransformer
    torch.manual_seed(config['seed']);np.random.seed(config['seed']);torch.set_num_threads(config['threads']);torch.use_deterministic_algorithms(True)
    model=SentenceTransformer(str((ROOT/config['model_path']).resolve()),device=config['device'],local_files_only=True);model.max_seq_length=config['max_tokens']
    lengths=[len(model.tokenizer.encode(t)) for t in texts];assert max(lengths)<=config['max_tokens']
    print('Encoding new texts only:',len(texts),'max_tokens',max(lengths),flush=True)
    vectors=model.encode(texts,batch_size=config['batch_size'],normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=True).astype(np.float32)
    assert vectors.shape==(len(texts),1024) and np.isfinite(vectors).all() and np.allclose(np.linalg.norm(vectors,axis=1),1,atol=1e-5)
    (OUT/'analyst').mkdir(parents=True,exist_ok=True);np.savez_compressed(OUT/'analyst/new_query_vectors.npz',texts=np.array(texts),vectors=vectors)
    emb.update(zip(texts,vectors));dense=np.load(ROOT/'docs/stage123-openai-triplicate-2026-10-27/embeddings.npz');matrix=dict(zip(dense['case_ids'].tolist(),dense['single']))
    corpus=read(RETR/'bm25_corpus_statistics.json');tokenizer=KiwiTokenizer();systems={s:[] for s in 'ABC'};details=[];retrieval=[]
    for q in CFG['questions']:
        qid=q['qid'];dv={cid:float(np.dot(matrix[cid],emb[q['text']])) for cid in ids};tokens=tokenizer.tokenize(q['text']);bv={}
        for cid in ids:
            tf=corpus['document_frequencies_by_case'][cid];length=corpus['document_lengths_by_case'][cid];k1=corpus['k1'];b=corpus['b'];avg=corpus['average_document_length']
            bv[cid]=sum(corpus['idf'].get(t,0)*tf.get(t,0)*(k1+1)/(tf.get(t,0)+k1*(1-b+b*length/avg)) for t in tokens)
        dr=sorted(ids,key=lambda c:(-dv[c],c));br=sorted(ids,key=lambda c:(-bv[c],c));tie={cid:float((Fraction(1,60+dr.index(cid)+1)+Fraction(1,60+br.index(cid)+1))/2) for cid in ids}
        maps={cid:compare(rq[qid],rp[cid]) for cid in ids};sem={cid:compare_fields(qp[qid],cp[cid],emb,config['weights']) for cid in ids}
        comb={cid:combined_score(maps[cid]['mapping_grade'],sem[cid]['score']) for cid in ids}
        rankings={'A':sorted(ids,key=lambda c:rule_key(maps[c],[],tie[c],c)),'B':sorted(ids,key=lambda c:ranking_key(sem[c]['score'],tie[c],c)),'C':sorted(ids,key=lambda c:ranking_key(comb[c],tie[c],c))}
        retrieval.append({'qid':qid,'tokens':tokens,'dense_scores':dv,'bm25_scores':bv,'dense_ranking':dr,'bm25_ranking':br,'hybrid_tie_score':tie})
        for s,ranking in rankings.items():systems[s].append({'qid':qid,'ranking':ranking,'top5':ranking[:5],'top10':ranking[:10]})
        for cid in ids:details.append({'qid':qid,'case_id':cid,'actual_task':cases[cid]['task'],'rule_case_recognized':bool(rp[cid]['task']['function_ids']),'rule_query_recognized':bool(rq[qid]['function_ids']),'A_rule_evidence':maps[cid],'B_semantic_components':sem[cid],'C_combined_score':comb[cid],'search_tie_score':tie[cid],'reason':'Frozen rule evidence / literal same-field cosine / fixed50:50 mixture; not a human relevance judgment.','context':cases[cid]['context'],'evidence_ids':cases[cid]['evidence_ids']})
    save('analyst/predictions.json',{'systems':systems,'scope':'original_only_O_SINGLE','human_labels_read':False})
    save('analyst/query_profiles.json',{'semantic':qp,'rule':rq});save('analyst/score_details.json',{'records':details});save('analyst/retrieval.json',{'records':retrieval})
    save('inference_receipt.json',{'local_cpu_only':True,'new_query_texts_encoded':len(texts),'case_texts_reencoded':0,'max_observed_tokens':max(lengths),'truncation':0,'candidate_count':112,'query_count':5,'ranking_count':15,'api_calls':0,'key_reads':0,'cost_usd':'0.00','sealed_test_access':False,'paid_dynamic_generation':'NOT_RUN','human_evaluation':'PENDING','frozen_input_hashes_after':{p.relative_to(ROOT).as_posix():sha(p) for p in protected()},'algorithm_modified':False})

def bundle():
    pred=read(OUT/'analyst/predictions.json')['systems'];cases=read(RETR/'case_registry.json')['cases'];unknown=set(read(SEM/'mapping/unknown33.json')['case_ids']);assert len(unknown)==33
    queries={q['qid']:q for q in CFG['questions']};qrows={s:{r['qid']:r for r in rows} for s,rows in pred.items()};pool=[];counts={}
    for q in queries:
        union=set().union(*(set(qrows[s][q]['top10']) for s in 'ABC'))
        extra=[cid for cid in qrows['B'][q]['ranking'] if cid in unknown and cid not in union][:2]
        counts[q]={'top10_union':len(union),'additional_unknown':len(extra),'total':len(union)+len(extra)}
        for cid in sorted(union|set(extra)):pool.append({'qid':q,'case_id':cid,'diagnostic_extra':cid in extra})
    rng=random.Random(CFG['seed']);rng.shuffle(pool);used=set();cross=[];public=[]
    # Existing source metadata only, restricted to the known112 case IDs. No Test queries or labels.
    catalog={}
    for line in (ROOT/'data/v2_5/research/evidence_catalog.jsonl').open(encoding='utf-8-sig'):
        item=json.loads(line)
        if item['case_id'] in cases:catalog.setdefault(item['case_id'],[]).append(item)
    for p in pool:
        eid='E-'+format(rng.getrandbits(48),'012X');assert eid not in used;used.add(eid);cid=p['case_id'];q=p['qid'];case=cases[cid]
        urls=sorted({x.get('source_url','') for x in catalog.get(cid,[]) if x.get('source_url')})
        source='\n'.join(urls) if urls else '기존 자료에 출처 URL이 없습니다.'
        source+='\n기존 연구의 구조화 요약입니다. 원 출판물은 이번에 재검증하지 않았습니다.'
        public.append(dict(zip(CFG['blind_fields'],[eid,q+' — '+queries[q]['text'],case['problem'],case['task'],case['context'],source,'',''])))
        cross.append({'evaluation_id':eid,**p,'ranks':{s:qrows[s][q]['ranking'].index(cid)+1 for s in 'ABC'},'unknown33':cid in unknown})
    csvsave('evaluator/blind_review.csv',public);save('evaluator/review_rows.json',{'headers':CFG['blind_fields'],'rows':public,'human_scores_prefilled':False})
    save('analyst/evaluation_key.json',{'records':cross,'seed':CFG['seed'],'diagnostic_selection':'Unknown33 outsideTop10union, best B rank up to2; never a label.','do_not_give_to_reviewer_before_scoring':True})
    save('pool_counts.json',{'questions':counts,'total_pairs':len(public),'top10_coverage_complete':True,'human_scored_pairs':0})
    guide='''# 사람 평가 안내

먼저 blind_review.xlsx 또는 blind_review.csv 중 하나만 사용하세요. 두 파일의 평가 ID와 내용은 같습니다. 채점하기 전에는 analyst 폴더, 추천 결과 보고서, 연결표를 열지 마세요. 같은 저장소에 있어도 별도 파일로 분리했을 뿐 접근을 차단한 것은 아닙니다.

평가표에는 질문과 기존 사례의 문제·Task·Context·출처만 있습니다. 사례 설명은 원래 자료의 문제 상황이며 질문과 관련된다는 추천 문구가 아닙니다. 출처 원문을 이번에 재검증한 것은 아닙니다.

관련성 점수 열(G)에 숫자0/1/2/3 또는 ‘판단 보류’를 입력하세요. 평가 의견 열(H)에 판단 이유나 부족한 정보를 적어 주세요. 다른 열과 평가 ID는 바꾸지 마세요. 공란은 아직 미평가, 판단 보류는 검토했으나 결정할 수 없다는 뜻입니다. 둘 다0점이 아닙니다.

- 3점: 동일하거나 직접 적용 가능한 업무 기능
- 2점: 기능이 유사해 다른 환경에도 응용 가능
- 1점: 일부 관련되지만 실제 적용 차이가 큼
- 0점: 관련 없는 업무
- 판단 보류: 기능 설명이 부족하거나 판단하기 어려움

일반 예시: 문서 번역을 원하는 질문에 문서 번역 사례는3점, 다른 형식이지만 번역 기능을 응용할 수 있으면2점, 번역 대신 요약만 하면1점, 상자 운반처럼 관계가 없으면0점으로 생각할 수 있습니다. 이 예시는 평가표의 특정 사례에 대한 정답이 아닙니다. 업종이 같다는 이유나 수작업이 줄어든다는 이유만으로 높은 점수를 주지 마세요.

Task에 실제 적힌 기능을 보세요. Problem에 필요한 작업이 적혀 있어도 실제 구현됐다는 뜻은 아닙니다. 업종이 달라도 실제 기능이 맞으면 인정할 수 있습니다. 원문에 없는 효과·보안·기능을 추측하지 마세요.

완료한 파일을 이 대화에 첨부해 주세요. 원본은 보존하고 다른 이름으로 저장해도 됩니다. 사람 채점 전에는 모델 성능이나 관련 정답을 확정하지 않습니다.
'''
    (OUT/'evaluator/채점안내.md').write_bytes(guide.encode('utf-8'))
    print('Blind review pool',counts,'total',len(public),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['freeze','run','bundle']);args=parser.parse_args()
    socket.socket.connect=blocked;socket.create_connection=blocked
    {'freeze':freeze,'run':run,'bundle':bundle}[args.stage]()
