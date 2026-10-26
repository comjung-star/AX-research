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
EVIDENCE = dict(line.split('\t', 1) for line in (HERE / 'cases.tsv').read_text(encoding='utf-8').splitlines())
FIELDS = ['query_id', 'perspective_id', 'case_id', 'relevance_0_4', 'reviewer_id', 'rationale', 'input_sha256']

def write(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

def expand(number):
    query = DOC['queries'][number - 1]
    count = len(query['reference_perspectives'])
    rows, seen = [], set()
    for line in (HERE / f't{number:02d}.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        parts = line.split('|')
        n, scores = int(parts[0]), parts[1]
        assert n not in seen and 1 <= n <= 117
        seen.add(n)
        assert len(scores) == count and set(scores) <= set('01234')
        notes = parts[2:] if len(parts) > 2 else ['-'] * count
        assert len(notes) == count, (number, n)
        for i, p in enumerate(query['reference_perspectives']):
            score = int(scores[i])
            comparison = notes[i] if score else f"이 사례의 중심 과제는 ‘{p['title']}’에 해당하는 질문 업무와 연결되지 않는다"
            assert comparison and comparison != '-', (number, n, i)
            values = [query['query_id'], p['id'], DOC['cases'][n - 1]['case_id'], score, 'independent_ai_reviewer_A', EVIDENCE[str(n)] + '. ' + comparison + '.', FINGERPRINT]
            rows.append(dict(zip(FIELDS, values)))
    assert seen == set(range(1, 118)) and len(rows) == count * 117
    write(HERE / f't{number:02d}_progress.csv', rows)
    return rows

if __name__ == '__main__':
    if len(sys.argv) == 2:
        n = int(sys.argv[1])
        rows = expand(n)
        print(json.dumps({'query': n, 'pairs': len(rows), 'histogram': dict(sorted(Counter(r['relevance_0_4'] for r in rows).items()))}))
    else:
        rows = [r for n in range(1, 13) for r in expand(n)]
        keys = {(r['query_id'], r['perspective_id'], r['case_id']) for r in rows}
        expected = {(q['query_id'], p['id'], c['case_id']) for q in DOC['queries'] for p in q['reference_perspectives'] for c in DOC['cases']}
        assert len(rows) == len(keys) == 3510 and keys == expected
        path = AUDIT / 'test_relevance_pass_1.csv'
        write(path, rows)
        with path.open(encoding='utf-8', newline='') as f:
            reread = list(csv.DictReader(f))
        assert len(reread) == 3510 and all(r['rationale'].strip() and r['relevance_0_4'] in '01234' for r in reread)
        report = {'stage': 'TEST_RELEVANCE_SEALED_BEFORE_FACTOR_AUTHORING', 'count': len(rows), 'unique_pairs': len(keys), 'input_sha256': FINGERPRINT, 'histogram': dict(sorted(Counter(r['relevance_0_4'] for r in rows).items())), 'positive_pairs': sum(r['relevance_0_4'] >= 3 for r in rows), 'output_raw_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        (HERE / 'test_seal.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=2))
