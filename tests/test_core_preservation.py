import pytest
from scripts import core_preservation_run as run


def test_unknown_core_fields_have_no_evidence():
    data = {'core': {field: {'text': None, 'evidence': []} for field in run.prompts.FIELDS}}
    run.validate('X', 'CPD01', data)
    data['core']['workflow'] = None
    run.validate('X', 'CPD01', data)
    data['core']['input']['evidence'] = ['invented']
    with pytest.raises(AssertionError):
        run.validate('X', 'CPD01', data)


def test_all_conditions_same_generation_parameters():
    bodies = [run.body(kind, 'CPD01') for kind in ('B', 'C', 'X')]
    keys = set(bodies[0])-{'input', 'instructions'}
    assert all({k: b[k] for k in keys} == {k: bodies[0][k] for k in keys} for b in bodies)


def test_missing_view_has_no_fabricated_content():
    views = [{'id': slot, 'status': 'MISSING', 'title': '', 'description': '',
              'keywords': [], 'source_quote': ''} for slot in run.SLOTS]
    run.validate('E', 'CPD01', {'perspectives': views})
    views[0]['description'] = 'invented'
    with pytest.raises(AssertionError):
        run.validate('E', 'CPD01', {'perspectives': views})


def test_sealed_predictions_cover_all_candidates_and_repetitions():
    from ax_research.heldout import read, sha
    prediction = read(run.OUT/'predictions.json')
    for name, digest in read(run.OUT/'prediction_seal.json')['files'].items():
        assert sha(run.OUT/name) == digest
    candidates = set(prediction['case_ids'])
    assert len(candidates) == 112
    assert set(prediction['systems']) == set('ABCE')
    for condition, rows in prediction['systems'].items():
        assert len(rows) == len(prediction['query_ids']) * (1 if condition == 'A' else 3)
        for row in rows:
            assert len(row['ranking']) == 112
            assert set(row['ranking']) == candidates
    assert len(read(run.OUT/'slots.json')['records']) == 216


def test_frozen_research_inputs_unchanged():
    from ax_research.heldout import read, sha
    plan = read(run.OUT/'preregistration.json')
    for path, digest in plan['protected_sha256'].items():
        assert sha(run.ROOT/path) == digest
    for path, digest in plan['environment']['protected'].items():
        assert sha(run.ROOT/path) == digest


def test_abstention_and_zero_positive_are_not_fabricated_metrics():
    from scripts.core_preservation_evaluate import evaluate
    ids = [f'case{i}' for i in range(112)]
    predictions = {'query_ids': ['fixture'], 'case_ids': ids, 'systems': {
        c: [{'query_id': 'fixture', 'ranking': ids, 'repeat': r}
            for r in ((0,) if c == 'A' else (1, 2, 3))] for c in 'ABCE'}}
    labels = [{'query_id': 'fixture', 'case_id': c, 'grade': 0, 'status': 'JUDGED',
               'rationale': 'Synthetic fixture', 'label_source': 'AI-Silver'} for c in ids]
    rows, macro, _ = evaluate(predictions, labels)
    assert all(r['metrics']['F1@5'] is None for r in rows)
    assert all(r['mean'] is None for r in macro if r['metric'] == 'Recall@5')
    labels[0].update(grade=None, status='ABSTAIN')
    rows, macro, _ = evaluate(predictions, labels)
    assert all(r['metrics']['Precision@5'] is None for r in rows)
    assert all(r['metrics']['Recall@20'] is None for r in rows)
    assert all(r['n'] == 0 for r in macro)


def test_missing_label_difference_bounds_match_exhaustive_assignments():
    from itertools import product
    from scripts.core_preservation_evaluate import incomplete_f1_bounds
    ids = [f'case{i}' for i in range(112)]
    rankings = {'A': ids, 'B': ids, 'C': ids,
                'E': ids[2:7]+ids[:2]+ids[7:]}
    prediction = {'query_ids': ['fixture'], 'case_ids': ids, 'systems': {
        c: [{'query_id': 'fixture', 'ranking': rank, 'repeat': r}
            for r in ((0,) if c == 'A' else (1, 2, 3))] for c, rank in rankings.items()}}
    labels = [{'query_id': 'fixture', 'case_id': c,
               'grade': 3 if i == 0 else None if i in (1, 6) else 0}
              for i, c in enumerate(ids)]
    result = next(r for r in incomplete_f1_bounds(prediction, labels)
                  if r['baseline'] == 'C' and r['metric'] == 'F1@5')
    values = []
    for first, second in product((0, 1), repeat=2):
        positive = {ids[0]} | ({ids[1]} if first else set()) | ({ids[6]} if second else set())
        values.append(2*(len(set(rankings['E'][:5]) & positive)-
                         len(set(rankings['C'][:5]) & positive))/(5+len(positive)))
    assert result['lower'] == pytest.approx(min(values))
    assert result['upper'] == pytest.approx(max(values))


def test_missing_responses_remain_unjudged_and_literal_quotes_match_cases():
    import json
    from ax_research.heldout import read, sha
    labels = read(run.OUT/'labels.json')['records']
    missing = set()
    for audit_path in run.OUT.glob('judge_*_partial_response.json'):
        audit = read(audit_path)
        stem = audit_path.name.removesuffix('_partial_response.json')
        assert sha(run.OUT/'api'/(stem+'_response.json')) == audit['response_sha256']
        qid = stem.split('_')[1]
        missing.update((qid, c) for c in audit['missing_ids'])
        assert audit['paid_retry_count'] == 0
    assert {(r['query_id'], r['case_id']) for r in labels if r['status']=='UNJUDGED'} == missing
    assert all(r['grade'] is None for r in labels if r['status']=='UNJUDGED')
    for request_path in (run.OUT/'api').glob('judge_*_request.json'):
        request = read(request_path)['body']
        payload = json.loads(request['input'].removesuffix('\nReturn JSON.'))
        assert set(payload) == {'query_id', 'business_problem', 'cases'}
        cases = {c['case_id']: c for c in payload['cases']}
        judged = [r for r in labels if r['query_id']==payload['query_id'] and
                  r['case_id'] in cases and r['status']=='JUDGED']
        assert all(r['task_quote'] in cases[r['case_id']]['Task'] for r in judged)


def test_saved_metrics_reproduce_without_api_calls():
    from ax_research.heldout import read
    from scripts.core_preservation_evaluate import evaluate
    rows, macro, leave_one = evaluate(read(run.OUT/'predictions.json'),
                                     read(run.OUT/'labels.json')['records'])
    saved = read(run.OUT/'evaluation.json')
    assert rows == saved['per_query']
    assert macro == saved['macro']
    assert leave_one == saved['leave_one_out']
