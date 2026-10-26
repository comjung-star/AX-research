import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWN = ROOT / 'reviewer_2'
REVIEWER = 'independent_ai_reviewer_B'
ADJUDICATOR = REVIEWER + '_post_independent_adjudication'
R_FIELDS = ['query_id', 'perspective_id', 'case_id', 'relevance_0_4', 'reviewer_id', 'rationale', 'input_sha256']
A_FIELDS = ['query_id', 'perspective_id', 'case_id', 'relevance_0_4', 'rationale', 'reviewer_id', 'input_sha256']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path, fields=None):
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if fields:
            assert reader.fieldnames == fields, path.name
        return list(reader)


def canonical(path):
    doc = json.loads(path.read_text(encoding='utf-8-sig'))
    sha = hashlib.sha256(json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return doc, sha


def pair_key(row):
    return row['query_id'], row['perspective_id'], row['case_id']


report = {'status': 'ALL_ASSIGNED_REVIEWER_B_ANNOTATIONS_AND_PROPOSALS_SEALED', 'human_gold': False, 'researcher_or_experiment_approval': False, 'outputs': {}, 'inputs': {}, 'limitations': ['AI semantic annotations, not human Gold or independently established causal truth.', 'Only whitelisted summaries were used; omissions in these summaries limit conclusions.', 'DEV and synthetic Test are distinct; Test uses the same case corpus.', 'Post-independent proposals inspect both grades and are not a third independent pass.', 'Strategy annotations use only implementation/outcome evidence, with no retroactive changes to blind judgments.', 'No independent verification of supplier outcome claims or full source texts was performed.']}
for mode, in_name, out_name, expected_sha in [
    ('dev', 'blind_relevance_input.json', 'relevance_pass_2.csv', '758a3ef1622218ef4232a328af8df2492cb5b1c14df82c68aa12a8c757dfdf0c'),
    ('test', 'blind_test_relevance_input.json', 'test_relevance_pass_2.csv', 'fd8bbb3aab58a30d8e8b37ef95ad6e78da2c3513a3a707a2a5bbb459b65aeef9'),
]:
    doc, sha = canonical(ROOT / in_name)
    assert sha == expected_sha
    report['inputs'][in_name] = {'sha256': sha, 'fingerprint_method': 'canonical JSON UTF-8 ensure_ascii=False sort_keys=True separators=(comma,colon)'}
    rows = read_csv(ROOT / out_name, R_FIELDS)
    expected = {(q['query_id'], p['id'], c['case_id']) for q in doc['queries'] for p in q['reference_perspectives'] for c in doc['cases']}
    assert len(rows) == len({pair_key(r) for r in rows}) == len(expected) == 3510
    assert {pair_key(r) for r in rows} == expected
    assert all(r['reviewer_id'] == REVIEWER and r['input_sha256'] == sha and r['rationale'].strip() and r['relevance_0_4'] in ('0', '1', '2', '3', '4') for r in rows)
    report['outputs'][out_name] = {'path': str(ROOT / out_name), 'rows': len(rows), 'unique_pairs': len(expected), 'score_histogram': dict(sorted(Counter(int(r['relevance_0_4']) for r in rows).items())), 'positive_at_3': sum(int(r['relevance_0_4']) >= 3 for r in rows), 'raw_sha256': digest(ROOT / out_name)}
    disagreements = ROOT / ('relevance_disagreements.csv' if mode == 'dev' else 'test_relevance_disagreements.csv')
    owned = [r for r in read_csv(disagreements) if int(r['query_id'][-3:]) % 2 == 0]
    proposals_path = OWN / (mode + '_adjudication_proposals.csv')
    proposals = read_csv(proposals_path, A_FIELDS)
    assert len(proposals) == len({pair_key(r) for r in proposals}) == len(owned)
    assert {pair_key(r) for r in proposals} == {pair_key(r) for r in owned}
    source = {pair_key(r): r for r in owned}
    assert all(r['reviewer_id'] == ADJUDICATOR and r['input_sha256'] == source[pair_key(r)]['input_sha256'] == sha and r['rationale'].strip() and r['relevance_0_4'] in ('0', '1', '2', '3', '4') for r in proposals)
    report['outputs']['reviewer_2/' + proposals_path.name] = {'path': str(proposals_path), 'rows': len(proposals), 'complete_owned_disagreement_coverage': True, 'score_histogram': dict(sorted(Counter(int(r['relevance_0_4']) for r in proposals).items())), 'owned_original_threshold_disagreements': sum((int(r['grade_a']) >= 3) != (int(r['grade_b']) >= 3) for r in owned), 'raw_sha256': digest(proposals_path), 'purpose': 'POST_INDEPENDENT_PROPOSALS_FOR_PARENT_REVIEW'}

for kind, taxonomy_name, id_field, label_field, expected_sha in [
    ('factor', 'root_cause_taxonomy_v2_3.csv', 'factor_id', 'factor_labels', 'fd61a890e0d972071d591de34fbedb7ef916baf1aa42b66958faf2c53a855919'),
    ('strategy', 'strategy_taxonomy_v2_3.csv', 'strategy_id', 'strategy_labels', '229958e97bce7d9178173d4e824acab8cbd603c737c267afe152d3dd1a456aa6'),
]:
    input_path = ROOT / (kind + '_blind_input.csv')
    output_path = ROOT / (kind + '_pass_2.csv')
    assert digest(input_path) == expected_sha
    inputs = read_csv(input_path)
    rows = read_csv(output_path, ['case_id', label_field, 'decision', 'rationale', 'reviewer_id', 'input_sha256'])
    allowed = {r[id_field] for r in read_csv(ROOT.parent / 'v2_3' / taxonomy_name)}
    assert len(rows) == len({r['case_id'] for r in rows}) == len(inputs) == 117
    assert {r['case_id'] for r in rows} == {r['case_id'] for r in inputs}
    for r in rows:
        labels = r[label_field].split('|') if r[label_field] else []
        assert len(labels) == len(set(labels)) and set(labels) <= allowed
        assert (r['decision'] == 'ABSTAIN' and not labels) or (r['decision'] == 'LABEL' and labels)
        assert r['reviewer_id'] == REVIEWER and r['input_sha256'] == expected_sha
        assert r['rationale'].strip() and '불확실성' in r['rationale']
    report['inputs'][input_path.name] = {'sha256': expected_sha, 'fingerprint_method': 'raw bytes'}
    report['outputs'][output_path.name] = {'path': str(output_path), 'rows': len(rows), 'labeled': sum(r['decision'] == 'LABEL' for r in rows), 'abstentions': sum(r['decision'] == 'ABSTAIN' for r in rows), 'abstention_case_ids': [r['case_id'] for r in rows if r['decision'] == 'ABSTAIN'], 'label_histogram': dict(sorted(Counter(label for r in rows for label in r[label_field].split('|') if label).items())), 'raw_sha256': digest(output_path)}

expected_seals = {
    'relevance_pass_2.csv': '99a8ed37bf7a9b23c06b4044a945894e2fda39aa2cd354d7575cee0b51e876cb',
    'test_relevance_pass_2.csv': 'f05740093edf0719390da326d04d7f7dea3292b4d989569c8d09c1880655510d',
    'factor_pass_2.csv': '9f46aee7ab22455096986f463af18099cbccdaf2194be6a48be957b91c3a8beb',
    'reviewer_2/dev_adjudication_proposals.csv': '434cdb8e571584323ca55205749c41f09e2c2a8b437be53e3f1618462771c51f',
    'reviewer_2/test_adjudication_proposals.csv': 'babe643d87c11e69d4c4ed74664845180645e080d371b9c36290e4a90e078bec',
    'strategy_pass_2.csv': '5b9260cbdbec454f589a7e3a49d9428340abde747fbd3953076bcb1c55eb0194',
}
assert all(report['outputs'][name]['raw_sha256'] == sha for name, sha in expected_seals.items())
report['prior_seals_unchanged'] = True
(OWN / 'verification_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
