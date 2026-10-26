import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWN = ROOT / 'reviewer_2'
REVIEWER = 'independent_ai_reviewer_B'
DOC = json.loads((ROOT / 'blind_relevance_input.json').read_text(encoding='utf-8-sig'))
R_HASH = hashlib.sha256(json.dumps(DOC, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
F_BYTES = (ROOT / 'factor_blind_input.csv').read_bytes()
F_HASH = hashlib.sha256(F_BYTES).hexdigest()
F_ROWS = list(csv.DictReader(io.StringIO(F_BYTES.decode('utf-8-sig'))))


def authored_rows(path):
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        rows.append(line.split('|', 2))
    assert len(rows) == 117, (path.name, len(rows))
    assert [int(r[0]) for r in rows] == list(range(1, 118)), path.name
    return rows


def relevance():
    output = []
    completed = []
    for q in DOC['queries']:
        path = OWN / (q['query_id'] + '.txt')
        if not path.exists():
            continue
        completed.append(q['query_id'])
        for index, scores, reasons in authored_rows(path):
            assert len(scores) == 3 and all(s in '01234' for s in scores), (path.name, index)
            parts = reasons.split('~')
            assert len(parts) in (1, 3) and all(p.strip() for p in parts), (path.name, index)
            case = DOC['cases'][int(index) - 1]
            for j, p in enumerate(q['reference_perspectives']):
                reason = parts[j] if len(parts) == 3 else parts[0]
                output.append(dict(query_id=q['query_id'], perspective_id=p['id'], case_id=case['case_id'], relevance_0_4=int(scores[j]), reviewer_id=REVIEWER, rationale=reason + ' (관점: ' + p['title'] + ')', input_sha256=R_HASH))
    assert len(output) == 351 * len(completed)
    assert len({(r['query_id'], r['perspective_id'], r['case_id']) for r in output}) == len(output)
    fields = ['query_id', 'perspective_id', 'case_id', 'relevance_0_4', 'reviewer_id', 'rationale', 'input_sha256']
    final = ROOT / 'relevance_pass_2.csv'
    partial = OWN / 'relevance.partial.csv'
    if len(completed) < 10 and final.exists():
        final.replace(partial)
    destination = OWN / 'relevance.publish.tmp.csv' if len(completed) == 10 else partial
    with destination.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(output)
    if len(completed) == 10:
        assert len(output) == 3510
        destination.replace(final)
    (OWN / 'progress.json').write_text(json.dumps({'status': 'COMPLETE_RELEVANCE_AI_ANNOTATION' if len(completed) == 10 else 'PARTIAL_NOT_COMPLETE', 'queries': completed, 'pairs': len(output)}, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'completed_queries': completed, 'count': len(output), 'histogram': dict(sorted(Counter(r['relevance_0_4'] for r in output).items())), 'positive': sum(r['relevance_0_4'] >= 3 for r in output)}


def factors():
    path = OWN / 'factor_decisions.txt'
    if not path.exists():
        return None
    taxonomy = list(csv.DictReader((ROOT.parent / 'v2_3' / 'root_cause_taxonomy_v2_3.csv').open(encoding='utf-8-sig', newline='')))
    lookup = {r['factor_id'][1:3]: r['factor_id'] for r in taxonomy}
    output = []
    for index, labels, rationale in authored_rows(path):
        nums = [] if labels == 'ABSTAIN' else labels.split(',')
        assert len(set(nums)) == len(nums) and all(n in lookup for n in nums)
        assert rationale.strip()
        output.append(dict(case_id=F_ROWS[int(index) - 1]['case_id'], factor_labels='|'.join(lookup[n] for n in nums), decision='LABEL' if nums else 'ABSTAIN', rationale=rationale, reviewer_id=REVIEWER, input_sha256=F_HASH))
    assert len(output) == len({r['case_id'] for r in output}) == 117
    destination = OWN / 'factor.publish.tmp.csv'
    with destination.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['case_id', 'factor_labels', 'decision', 'rationale', 'reviewer_id', 'input_sha256'])
        w.writeheader()
        w.writerows(output)
    destination.replace(ROOT / 'factor_pass_2.csv')
    return {'count': len(output), 'abstentions': sum(r['decision'] == 'ABSTAIN' for r in output), 'factor_histogram': dict(sorted(Counter(l for r in output for l in r['factor_labels'].split('|') if l).items()))}


if __name__ == '__main__':
    print(json.dumps({'relevance': None if '--factor-only' in sys.argv else relevance(), 'factor': factors(), 'relevance_input_sha256': R_HASH, 'factor_input_sha256': F_HASH}, ensure_ascii=False, indent=2))
