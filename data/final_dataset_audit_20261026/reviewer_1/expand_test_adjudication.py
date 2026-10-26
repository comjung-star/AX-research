"""Mechanical expansion of explicit post-independent Test adjudications."""
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent
DOC = json.loads((AUDIT / 'blind_test_relevance_input.json').read_text(encoding='utf-8-sig'))
FINGERPRINT = hashlib.sha256(json.dumps(DOC, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
assert FINGERPRINT == 'fd8bbb3aab58a30d8e8b37ef95ad6e78da2c3513a3a707a2a5bbb459b65aeef9'
CASES = {i + 1: c['case_id'] for i, c in enumerate(DOC['cases'])}
EVIDENCE = dict(line.split('\t', 1) for line in (HERE / 'cases.tsv').read_text(encoding='utf-8').splitlines())
CODES = json.loads((HERE / 'test_adjudication_codes.json').read_text(encoding='utf-8'))
OWNED = [1, 3, 5, 7, 9, 11]
REVIEWER = 'independent_ai_reviewer_A_post_independent_adjudication'
FIELDS = ['query_id', 'perspective_id', 'case_id', 'relevance_0_4', 'rationale', 'reviewer_id', 'input_sha256']
with (AUDIT / 'test_relevance_disagreements.csv').open(encoding='utf-8-sig', newline='') as f:
    SOURCE = [r for r in csv.DictReader(f) if r['query_id'] in {f'AXT{n:03d}' for n in OWNED}]
LOOKUP = {(r['query_id'], r['perspective_id'], r['case_id']): r for r in SOURCE}
assert len(SOURCE) == len(LOOKUP)

def preserve_seals():
    for seal_name, csv_name in [('dev_seal.json', 'relevance_pass_1.csv'), ('test_seal.json', 'test_relevance_pass_1.csv'), ('factor_seal.json', 'factor_pass_1.csv')]:
        seal = json.loads((HERE / seal_name).read_text(encoding='utf-8'))
        assert seal['output_raw_sha256'] == hashlib.sha256((AUDIT / csv_name).read_bytes()).hexdigest(), csv_name

def write(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

def expand(number):
    query = DOC['queries'][number - 1]
    rows, seen = [], set()
    for line in (HERE / f'at{number:02d}.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        ns, ps, ss, code = line.split('|')
        n, p, score = int(ns), int(ps), int(ss)
        assert 1 <= n <= 117 and 1 <= p <= len(query['reference_perspectives']) and 0 <= score <= 4
        perspective = query['reference_perspectives'][p - 1]
        key = (query['query_id'], perspective['id'], CASES[n])
        assert key in LOOKUP and key not in seen, key
        seen.add(key)
        source = LOOKUP[key]
        assert source['input_sha256'] == FINGERPRINT and source['grade_a'] != source['grade_b']
        rationale = f"{EVIDENCE[str(n)]}. {perspective['title']}: A={source['grade_a']}·B={source['grade_b']} 차이를 검토했다. {CODES[code]}."
        rows.append(dict(zip(FIELDS, [key[0], key[1], key[2], score, rationale, REVIEWER, source['input_sha256']])))
    expected = {k for k in LOOKUP if k[0] == query['query_id']}
    assert seen == expected, {'missing': sorted(expected - seen), 'extra': sorted(seen - expected)}
    write(HERE / f'at{number:02d}_progress.csv', rows)
    return rows

if __name__ == '__main__':
    preserve_seals()
    if len(sys.argv) == 2:
        n = int(sys.argv[1])
        rows = expand(n)
        print(json.dumps({'query': n, 'disagreements_adjudicated': len(rows), 'histogram': dict(sorted(Counter(r['relevance_0_4'] for r in rows).items()))}))
    else:
        rows = [r for n in OWNED for r in expand(n)]
        keys = {(r['query_id'], r['perspective_id'], r['case_id']) for r in rows}
        assert len(rows) == len(keys) == len(SOURCE) == 262 and keys == set(LOOKUP)
        path = HERE / 'test_adjudication_proposals.csv'
        write(path, rows)
        with path.open(encoding='utf-8', newline='') as f:
            delivered = list(csv.DictReader(f))
        assert len(delivered) == 262 and all(r['rationale'].strip() for r in delivered)
        threshold = {'flip_vs_a': 0, 'flip_vs_b': 0, 'flip_vs_either': 0}
        for r in rows:
            s = LOOKUP[(r['query_id'], r['perspective_id'], r['case_id'])]
            a, b, decision = int(s['grade_a']) >= 3, int(s['grade_b']) >= 3, r['relevance_0_4'] >= 3
            threshold['flip_vs_a'] += a != decision
            threshold['flip_vs_b'] += b != decision
            threshold['flip_vs_either'] += a != decision or b != decision
        report = {'stage': 'POST_INDEPENDENT_TEST_AI_ADJUDICATION_PROPOSALS_NOT_ADOPTED_NOT_HUMAN_GOLD', 'rows': len(rows), 'unique_pairs': len(keys), 'owned_queries': dict(Counter(r['query_id'] for r in rows)), 'histogram': dict(sorted(Counter(r['relevance_0_4'] for r in rows).items())), 'threshold_review': threshold, 'input_sha256_values': sorted({r['input_sha256'] for r in rows}), 'original_independent_files_unchanged': True}
        (HERE / 'test_adjudication_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        preserve_seals()
        print(json.dumps(report, ensure_ascii=False, indent=2))
