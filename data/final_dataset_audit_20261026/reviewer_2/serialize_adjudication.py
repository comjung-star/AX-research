import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWN = ROOT / 'reviewer_2'
MODE = sys.argv[1]
assert MODE in ('dev', 'test')
SEALS = {'relevance_pass_2.csv': '99a8ed37bf7a9b23c06b4044a945894e2fda39aa2cd354d7575cee0b51e876cb', 'test_relevance_pass_2.csv': 'f05740093edf0719390da326d04d7f7dea3292b4d989569c8d09c1880655510d', 'factor_pass_2.csv': '9f46aee7ab22455096986f463af18099cbccdaf2194be6a48be957b91c3a8beb'}
for name, expected in SEALS.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
doc = json.loads((ROOT / ('blind_relevance_input.json' if MODE == 'dev' else 'blind_test_relevance_input.json')).read_text(encoding='utf-8-sig'))
cases = {c['case_id']: i for i, c in enumerate(doc['cases'], 1)}
source = ROOT / ('relevance_disagreements.csv' if MODE == 'dev' else 'test_relevance_disagreements.csv')
rows = [r for r in csv.DictReader(source.open(encoding='utf-8-sig', newline='')) if int(r['query_id'][-3:]) % 2 == 0]
queries = {q['query_id']: q for q in doc['queries']}
decisions = {}
done = []
for qid in sorted({r['query_id'] for r in rows}):
    path = OWN / (MODE + '_adjudication_' + qid + '.txt')
    if not path.exists():
        continue
    done.append(qid)
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        index, vector, reason = line.split('|', 2)
        assert len(vector) == len(queries[qid]['reference_perspectives'])
        parts = reason.split('~')
        assert len(parts) in (1, len(vector)) and all(p.strip() for p in parts)
        for j, s in enumerate(vector):
            if s == '-':
                continue
            assert s in '01234'
            pid = queries[qid]['reference_perspectives'][j]['id']
            key = (qid, pid, int(index))
            assert key not in decisions
            decisions[key] = (int(s), parts[j] if len(parts) > 1 else reason)
out = []
for r in rows:
    if r['query_id'] not in done:
        continue
    key = (r['query_id'], r['perspective_id'], cases[r['case_id']])
    assert key in decisions, ('MISSING', key)
    score, reason = decisions.pop(key)
    out.append(dict(query_id=r['query_id'], perspective_id=r['perspective_id'], case_id=r['case_id'], relevance_0_4=score, rationale='독립판정 ' + r['grade_a'] + '/' + r['grade_b'] + ' 충돌 조정: ' + reason + ' (관점: ' + r['reference'] + ')', reviewer_id='independent_ai_reviewer_B_post_independent_adjudication', input_sha256=r['input_sha256']))
assert not decisions, ('EXTRA', list(decisions)[:10])
assert len(out) == len({(r['query_id'], r['perspective_id'], r['case_id']) for r in out})
full = len(out) == len(rows)
destination = OWN / (MODE + '_adjudication.publish.tmp.csv' if full else MODE + '_adjudication.partial.csv')
with destination.open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['query_id', 'perspective_id', 'case_id', 'relevance_0_4', 'rationale', 'reviewer_id', 'input_sha256'])
    w.writeheader()
    w.writerows(out)
if full:
    destination.replace(OWN / (MODE + '_adjudication_proposals.csv'))
report = {'stage': 'POST_INDEPENDENT_AI_ADJUDICATION_NOT_HUMAN_GOLD', 'status': 'COMPLETE_PROPOSALS_FOR_PARENT_REVIEW' if full else 'PARTIAL_NOT_COMPLETE', 'queries': done, 'count': len(out), 'expected_owned': len(rows), 'histogram': dict(sorted(Counter(r['relevance_0_4'] for r in out).items())), 'source_raw_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'sealed_originals': SEALS}
(OWN / (MODE + '_adjudication_progress.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
