"""Candidate-scoped unchanged functional/semantic composition using fresh frozen embeddings."""
import hashlib
import json
import sys
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

from ax_research.action_aggregation import compose, purpose_filter
from ax_research.functional_mapping import compare, extract
from scripts.autonomous_trial2_mapping_replay import handoff

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / '.work-new20-runtime'
OUT = ROOT / 'docs/autonomous-improvement-20261108'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def seal(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def infer():
    destination = OUT / '17_trial2_precision_predictions.json'
    assert not destination.exists()
    historical = read(ROOT / 'docs/validation-new20-20261107/measured/predictions_new20.json')
    fresh = read(RUN / 'predictions_new20.json')
    assert fresh == historical, 'Fresh original A/C/E must reproduce stored full112 rankings exactly'
    rules = read(ROOT / 'configs/functional_mapping_20261028.json')
    config = read(ROOT / 'configs/action_aggregation_20261102.json')
    cases = read(ROOT / 'docs/query-case-functional-mapping-2026-10-28/stage2/case_profiles.json')
    filtered = {case: {role: purpose_filter(profile, config) for role, profile in roles.items()}
                for case, roles in cases.items()}
    questions = {row['query_id']: row['text'] for row in
                 map(json.loads, (ROOT / 'docs/validation-new20-20261107/questions.jsonl').read_text(encoding='utf-8').splitlines())}
    whole = {(row['query_id'], row['case_id']): row for row in
             read(RUN / 'original/predictions/evidence.json')['records']}
    paths = [row for row in read(RUN / 'inference/paths.json')['paths'] if row['query_id'].startswith('E_')]
    branch = {(row['path_id'], row['case_id']): row for row in
              map(json.loads, (RUN / 'inference/branch_scores.jsonl').read_text(encoding='utf-8').splitlines())
              if row['path_id'].startswith('E_')}
    groups = defaultdict(list)
    for path in paths:
        groups[path['parent_query_id'], path['repeat'] - 6].append(path)
    assert len(groups) == 60
    source = read(ROOT / 'docs/validation-new20-20261107/diagnosis/raw_search_stage_rankings.json')
    raw_ranks = {name: {row['query_id']: row['ranking'] for row in rows} for name, rows in source['systems'].items()}
    ids = historical['case_ids']
    predictions = []
    reproduction = []
    for (query, repeat), views in sorted(groups.items()):
        assert len(views) == 3
        dense = sorted(ids, key=lambda case: (-whole[query, case]['dense'], case))
        sparse = sorted(ids, key=lambda case: (-whole[query, case]['bm25'], case))
        assert dense == raw_ranks['Dense'][query] and sparse == raw_ranks['BM25'][query]
        profile = purpose_filter(extract(questions[query], rules), config)
        profiles = {view['query_id']: purpose_filter(extract(view['text'], rules), config) for view in views}
        scores = {}
        old_ties = {}
        for case in ids:
            mappings = {path: compare(value, filtered[case]) for path, value in profiles.items()}
            for path, mapping in mappings.items():
                assert mapping == branch[path, case]['C1_rule']
            result = compose(compare(profile, filtered[case])['mapping_grade'],
                             {path: mapping['mapping_grade'] for path, mapping in mappings.items()},
                             whole[query, case]['semantic']['score'],
                             {path: branch[path, case]['semantic']['score'] for path in profiles})
            scores[case] = result
            old_ties[case] = sum((Fraction(branch[path, case]['hybrid_exact']) for path in profiles), Fraction()) / len(profiles)
        reproduced = sorted(ids, key=lambda case: (-scores[case]['score'], -old_ties[case], case))
        expected = next(row['ranking'] for row in historical['systems']['E'] if row['query_id'] == query and row['repeat'] == repeat)
        assert reproduced == expected, 'Recomputed original precision mapping differs'
        reproduction.append({'query_id': query, 'repeat': repeat, 'exact_E_reproduction': True})
        for policy, candidates in [('baseline', raw_ranks['Hybrid_RRF'][query][:20]),
                                   ('proposed', handoff(dense, sparse))]:
            details = {}
            branch_evidence = {}
            for case in candidates:
                mappings = {path: compare(value, filtered[case]) for path, value in profiles.items()}
                branch_evidence[case] = {path: {
                    'mapping': mapping,
                    'semantic': branch[path, case]['semantic'],
                    'dense_rank': branch[path, case]['dense_rank'],
                    'sparse_rank': branch[path, case]['bm25_rank']}
                    for path, mapping in mappings.items()}
                details[case] = compose(compare(profile, filtered[case])['mapping_grade'],
                                        {path: mapping['mapping_grade'] for path, mapping in mappings.items()},
                                        whole[query, case]['semantic']['score'],
                                        {path: branch[path, case]['semantic']['score'] for path in profiles})
                assert details[case] == scores[case]
            ranking = sorted(candidates, key=lambda case: (-details[case]['score'], case))
            predictions.append({'query_id': query, 'repeat': repeat, 'policy': policy,
                                'candidates': candidates, 'ranking': ranking, 'scores_and_branch_evidence': details,
                                'branch_mapping_evidence': branch_evidence,
                                'paths': [view['query_id'] for view in views]})
    files = [RUN / 'inference/branch_scores.jsonl', RUN / 'original/predictions/evidence.json',
             RUN / 'inference/paths.json', RUN / 'predictions_new20.json', Path(__file__)]
    result = {'state': 'FRESH_PRECISION_MAPPING_EXECUTED', 'records': predictions,
              'original_reproduction': reproduction, 'fresh_original_ACE_exact': True,
              'inputs': {str(path.relative_to(ROOT)): seal(path) for path in files},
              'protocol': 'Whole-query Dense/Sparse alternate20 vs historical Hybrid20 comparator; three E branches retained through unchanged compose; both arms same20 and same scorer.',
              'tie_policy': 'Both arms descending unchanged composition score then case_id; historical RRF ties used ONLY in exact historical baseline reproduction gate, never in proposed outputs.',
              'deviation': 'Neutral case_id ties in both controlled arms explicitly replace historical RRF ties. No score/weight/rule change. Equal20 is posthoc extension, not original unequal union endpoint.',
              'qrels_read_during_prediction': False, 'paid_api_usd': 0, 'sealed_test_opened': False}
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'state': result['state'], 'outputs': len(predictions), 'reproduction_gates': len(reproduction)}))


if __name__ == '__main__':
    infer()
