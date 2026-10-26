"""Mechanical expansion of Reviewer A's explicit semantic decisions; no scoring logic."""
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent
DOC = json.loads((AUDIT / 'blind_relevance_input.json').read_text(encoding='utf-8-sig'))
REVIEWER = 'independent_ai_reviewer_A'
JSON_HASH = hashlib.sha256(json.dumps(DOC, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
FIELDS = ['query_id', 'perspective_id', 'case_id', 'relevance_0_4', 'reviewer_id', 'rationale', 'input_sha256']
EVIDENCE = dict(line.split('\t', 1) for line in (HERE / 'cases.tsv').read_text(encoding='utf-8').splitlines())

def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def expand_query(number):
    query = DOC['queries'][number - 1]
    rows, seen = [], set()
    for line in (HERE / f'q{number:02d}.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        parts = line.split('|')
        n, scores = int(parts[0]), parts[1]
        assert n not in seen and 1 <= n <= 117
        seen.add(n)
        assert len(scores) == 3 and set(scores) <= set('01234')
        notes = parts[2:] if len(parts) > 2 else ['-', '-', '-']
        assert len(notes) == 3, (number, n, notes)
        case = DOC['cases'][n - 1]
        for i, (score, perspective) in enumerate(zip(scores, query['reference_perspectives'])):
            if score != '0':
                assert notes[i] and notes[i] != '-', (number, n, i)
                comparison = notes[i]
            else:
                comparison = f"이 사례의 중심 과제는 ‘{perspective['title']}’에 해당하는 쿼리 업무와 연결되지 않는다"
            rationale = EVIDENCE[str(n)] + '. ' + comparison + '.'
            rows.append(dict(zip(FIELDS, [query['query_id'], perspective['id'], case['case_id'], int(score), REVIEWER, rationale, JSON_HASH])))
    assert seen == set(range(1, 118)) and len(rows) == 351
    write_csv(HERE / f'q{number:02d}_progress.csv', FIELDS, rows)
    return rows

def factors():
    raw = (AUDIT / 'factor_blind_input.csv').read_bytes()
    factor_hash = hashlib.sha256(raw).hexdigest()
    source = list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    taxonomy_path = AUDIT.parent / 'v2_3' / 'root_cause_taxonomy_v2_3.csv'
    taxonomy = list(csv.DictReader(taxonomy_path.read_text(encoding='utf-8-sig').splitlines()))
    full_ids = {int(row['factor_id'][1:3]): row['factor_id'] for row in taxonomy}
    output, seen = [], set()
    for line in (HERE / 'factors.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        num, labels, reason = line.split('|', 2)
        n = int(num)
        assert n not in seen and 1 <= n <= 117
        seen.add(n)
        case = source[n - 1]
        assert case['case_id'] == DOC['cases'][n - 1]['case_id']
        ids = [full_ids[int(v)] for v in labels.split(',')] if labels != '-' else []
        assert len(ids) == len(set(ids))
        assert reason and '불확실성:' in reason
        output.append({'case_id': case['case_id'], 'factor_labels': '|'.join(ids), 'decision': 'LABEL' if ids else 'ABSTAIN', 'rationale': reason, 'reviewer_id': REVIEWER, 'input_sha256': factor_hash})
    assert len(output) == 117 and seen == set(range(1, 118))
    write_csv(AUDIT / 'factor_pass_1.csv', ['case_id', 'factor_labels', 'decision', 'rationale', 'reviewer_id', 'input_sha256'], output)
    return output, factor_hash

if __name__ == '__main__':
    if len(sys.argv) == 2:
        q = int(sys.argv[1])
        rows = expand_query(q)
        print(json.dumps({'query': q, 'count': len(rows), 'histogram': dict(sorted(Counter(r['relevance_0_4'] for r in rows).items()))}, ensure_ascii=False))
    else:
        rows = [row for n in range(1, 11) for row in expand_query(n)]
        keys = {(r['query_id'], r['perspective_id'], r['case_id']) for r in rows}
        expected = {(q['query_id'], p['id'], c['case_id']) for q in DOC['queries'] for p in q['reference_perspectives'] for c in DOC['cases']}
        assert len(rows) == len(keys) == 3510 and keys == expected
        assert all(r['rationale'].strip() and 0 <= r['relevance_0_4'] <= 4 for r in rows)
        write_csv(AUDIT / 'relevance_pass_1.csv', FIELDS, rows)
        factor_rows, factor_hash = factors()
        report = {'reviewer_id': REVIEWER, 'status': DOC['status'], 'relevance_count': len(rows), 'unique_pairs': len(keys), 'json_sha256': JSON_HASH, 'score_histogram': dict(sorted(Counter(r['relevance_0_4'] for r in rows).items())), 'positive_pairs': sum(r['relevance_0_4'] >= 3 for r in rows), 'factor_count': len(factor_rows), 'factor_sha256': factor_hash, 'factor_abstentions': sum(r['decision'] == 'ABSTAIN' for r in factor_rows), 'factor_label_counts': dict(Counter(v for r in factor_rows for v in r['factor_labels'].split('|') if v)), 'per_query': {q['query_id']: dict(sorted(Counter(r['relevance_0_4'] for r in rows if r['query_id'] == q['query_id']).items())) for q in DOC['queries']}}
        (HERE / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        # Read back the exact delivered files to check serialization and content.
        for path, count in [(AUDIT / 'relevance_pass_1.csv', 3510), (AUDIT / 'factor_pass_1.csv', 117)]:
            with path.open(encoding='utf-8', newline='') as f:
                reread = list(csv.DictReader(f))
            assert len(reread) == count and all(r['rationale'].strip() for r in reread)
        print(json.dumps(report, ensure_ascii=False, indent=2))
