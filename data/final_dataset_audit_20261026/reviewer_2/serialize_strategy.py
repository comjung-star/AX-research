import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWN = ROOT / 'reviewer_2'
SEALS = {
    'relevance_pass_2.csv': '99a8ed37bf7a9b23c06b4044a945894e2fda39aa2cd354d7575cee0b51e876cb',
    'test_relevance_pass_2.csv': 'f05740093edf0719390da326d04d7f7dea3292b4d989569c8d09c1880655510d',
    'factor_pass_2.csv': '9f46aee7ab22455096986f463af18099cbccdaf2194be6a48be957b91c3a8beb',
    'reviewer_2/dev_adjudication_proposals.csv': '434cdb8e571584323ca55205749c41f09e2c2a8b437be53e3f1618462771c51f',
    'reviewer_2/test_adjudication_proposals.csv': 'babe643d87c11e69d4c4ed74664845180645e080d371b9c36290e4a90e078bec',
}
for name, sha in SEALS.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name
data = (ROOT / 'strategy_blind_input.csv').read_bytes()
sha = hashlib.sha256(data).hexdigest()
assert sha == '229958e97bce7d9178173d4e824acab8cbd603c737c267afe152d3dd1a456aa6'
source = list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
assert len(source) == 117
taxonomy_path = ROOT.parent / 'v2_3' / 'strategy_taxonomy_v2_3.csv'
taxonomy = list(csv.DictReader(taxonomy_path.open(encoding='utf-8-sig', newline='')))
ids = {r['strategy_id'][1]: r['strategy_id'] for r in taxonomy}
rows = []
for number, line in enumerate((OWN / 'strategy_decisions.txt').read_text(encoding='utf-8').splitlines(), 1):
    index, labels, reason = line.split('|', 2)
    assert int(index) == number
    nums = [] if labels == 'ABSTAIN' else labels.split(',')
    assert len(set(nums)) == len(nums) and all(n in ids for n in nums)
    assert reason.strip() and '불확실성' in reason
    rows.append(dict(case_id=source[number-1]['case_id'], strategy_labels='|'.join(ids[n] for n in nums), decision='LABEL' if nums else 'ABSTAIN', rationale=reason, reviewer_id='independent_ai_reviewer_B', input_sha256=sha))
assert len({r['case_id'] for r in rows}) == len(rows)
full = len(rows) == 117
destination = OWN / ('strategy.publish.tmp.csv' if full else 'strategy.partial.csv')
with destination.open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['case_id', 'strategy_labels', 'decision', 'rationale', 'reviewer_id', 'input_sha256'])
    w.writeheader()
    w.writerows(rows)
if full:
    destination.replace(ROOT / 'strategy_pass_2.csv')
report = {'stage': 'INDEPENDENT_SOLUTION_ONLY_AI_ANNOTATION_NOT_HUMAN_GOLD', 'status': 'SEALED' if full else 'PARTIAL_NOT_COMPLETE', 'count': len(rows), 'abstentions': sum(r['decision'] == 'ABSTAIN' for r in rows), 'labels': dict(sorted(Counter(s for r in rows for s in r['strategy_labels'].split('|') if s).items())), 'input_raw_sha256': sha, 'taxonomy_raw_sha256': hashlib.sha256(taxonomy_path.read_bytes()).hexdigest(), 'sealed_prior_outputs': SEALS}
if full:
    report['output_raw_sha256'] = hashlib.sha256((ROOT / 'strategy_pass_2.csv').read_bytes()).hexdigest()
(OWN / 'strategy_progress.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
