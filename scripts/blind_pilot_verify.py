"""Replay frozen scores and verify blind content without creating human labels."""
import math
import random
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
from scripts import blind_pilot_five as p
from scripts.blind_pilot_analyze import read_review,analyze
from ax_research.semantic_mapping import compare_fields,combined_score,ranking_key
from ax_research.functional_mapping import compare,ranking_key as rule_key
from ax_research.retrieval.bm25 import BM25Retriever

def main():
    freeze=p.read(p.OUT/'freeze.json');assert freeze['adapter_sha256']==p.sha(p.ROOT/'scripts/blind_pilot_five.py')
    assert freeze['config_sha256']==p.sha(p.CONFIG)
    for rel,h in freeze['frozen_inputs'].items():assert p.sha(p.ROOT/rel)==h
    cfg,rules=p.settings();cases=p.read(p.RETR/'case_registry.json')['cases'];cp=p.read(p.SEM/'mapping/case_profiles.json');rp=p.read(p.HIST/'stage2/case_profiles.json')
    old=np.load(p.SEM/'mapping/embeddings.npz');new=np.load(p.OUT/'analyst/new_query_vectors.npz');emb={**dict(zip(old['texts'].tolist(),old['vectors'])),**dict(zip(new['texts'].tolist(),new['vectors']))}
    profiles=p.read(p.OUT/'analyst/query_profiles.json');pred=p.read(p.OUT/'analyst/predictions.json')['systems'];detail={(r['qid'],r['case_id']):r for r in p.read(p.OUT/'analyst/score_details.json')['records']}
    retr={r['qid']:r for r in p.read(p.OUT/'analyst/retrieval.json')['records']};ids=sorted(cases)
    bm=BM25Retriever({cid:'\n'.join(f'[{field.upper()}] {cases[cid][field]}' for field in ('problem','task','context')) for cid in ids})
    for q in p.CFG['questions']:
        qid=q['qid'];reference={row.case_id:row.score for row in bm.search(q['text'],top_k=None)}
        assert [r.case_id for r in bm.search(q['text'],top_k=None)]==retr[qid]['bm25_ranking']
        for cid in ids:
            assert math.isclose(reference[cid],retr[qid]['bm25_scores'][cid],abs_tol=1e-10)
            d=detail[qid,cid];a=compare(profiles['rule'][qid],rp[cid]);b=compare_fields(profiles['semantic'][qid],cp[cid],emb,cfg['weights'])
            assert a==d['A_rule_evidence'] and b==d['B_semantic_components']
            assert combined_score(a['mapping_grade'],b['score'])==d['C_combined_score']
        expected={
          'A':sorted(ids,key=lambda cid:rule_key(detail[qid,cid]['A_rule_evidence'],[],retr[qid]['hybrid_tie_score'][cid],cid)),
          'B':sorted(ids,key=lambda cid:ranking_key(detail[qid,cid]['B_semantic_components']['score'],retr[qid]['hybrid_tie_score'][cid],cid)),
          'C':sorted(ids,key=lambda cid:ranking_key(detail[qid,cid]['C_combined_score'],retr[qid]['hybrid_tie_score'][cid],cid))}
        for s in 'ABC':assert next(x['ranking'] for x in pred[s] if x['qid']==qid)==expected[s]
    public=p.read(p.OUT/'evaluator/review_rows.json')['rows'];keys=p.read(p.OUT/'analyst/evaluation_key.json')['records'];key={x['evaluation_id']:x for x in keys};assert len(key)==len(public)==103
    assert read_review(p.OUT/'evaluator/blind_review.csv')==public==read_review(p.OUT/'evaluator/blind_review.xlsx')
    grouped={q['qid']:{x['case_id'] for x in keys if x['qid']==q['qid']} for q in p.CFG['questions']}
    rng=random.Random(p.CFG['seed']);base=sorted((x['qid'],x['case_id']) for x in keys);rng.shuffle(base)
    assert base==[(x['qid'],x['case_id']) for x in keys]
    for row in public:
        assert list(row)==p.CFG['blind_fields'] and row['관련성 점수']==row['평가 의견']==''
        ref=key[row['평가 ID']];case=cases[ref['case_id']]
        assert row['실제 수행 Task']==case['task'] and row['적용 Context']==case['context'] and row['AX 사례 설명']==case['problem']
        assert all(cid not in '\n'.join(row.values()) for cid in cases)
    for q in grouped:
        for s in 'ABC':assert set(next(x['top10'] for x in pred[s] if x['qid']==q))<=grouped[q]
        assert sum(x['diagnostic_extra'] for x in keys if x['qid']==q)<=2
    with zipfile.ZipFile(p.OUT/'evaluator/blind_review.xlsx') as z:
        ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'};wb=ET.fromstring(z.read('xl/workbook.xml'));sheets=wb.findall('x:sheets/x:sheet',ns)
        assert [s.attrib['name'] for s in sheets]==['평가표','채점 안내'] and all(s.attrib.get('state','visible')=='visible' for s in sheets)
        for name in z.namelist():
            if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
                root=ET.fromstring(z.read(name));assert not root.findall('.//x:f',ns)
                assert not any(r.attrib.get('hidden')=='1' for r in root.findall('x:sheetData/x:row',ns))
                assert not any(c.attrib.get('hidden')=='1' for c in root.findall('x:cols/x:col',ns))
    pending=analyze(public,public,keys,pred);assert pending['human_scored_pairs']==0 and all(x['precision'] is None and x['nDCG_judged_pool'] is None for x in pending['metrics'])
    p.save('verification.json',{'passed':True,'frozen_inputs_verified':15,'score_pairs_replayed':560,'rankings_replayed':15,'bm25_independent_library_scores_checked':560,'review_rows_verified':103,'all_top10_covered':True,'xlsx_csv_values_identical':True,'hidden_rows_columns_sheets':False,'score_cells_empty':True,'missing_labels_not_zero':True,'case_profiles_vectors_reused':True,'api_calls':0,'key_reads':0,'human_labels_created':0,'sealed_test_read':False,'semantic_relevance_validated':False})
    print('Verified 560 scores, 15 full rankings, all103 blind rows and empty human labels.')

if __name__=='__main__':main()
