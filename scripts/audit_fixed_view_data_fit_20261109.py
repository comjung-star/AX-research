"""Source-only fixed-slot applicability inventory; no scoring, labels or model calls."""
from collections import Counter
import json

from scripts.improvement_cycle import ROOT, read
from scripts.task_alignment_20261109 import sha

OUT = ROOT / 'docs/fixed-view-data-fit-20261109'
PILOT = ROOT / 'docs/independent-validation-20261108/ai_pilot'
SLOTS = ('BUSINESS', 'OPERATIONS', 'TECHNICAL')


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    cases_path = 'docs/dense-bm25-candidates-2026-10-27/case_registry.json'
    cases = read(cases_path)['cases']
    questions = {r['query_id']: r['text'] for r in map(json.loads, (PILOT / 'questions.jsonl').read_text(encoding='utf-8').splitlines())}
    assert len(cases) == 112 and len(questions) == 40
    presence = {f: sum(bool(str(row.get(f, '')).strip()) and str(row[f]).strip().upper() not in ('UNKNOWN', 'NONE', 'N/A', 'NULL') for row in cases.values()) for f in ('problem', 'task', 'context')}
    counts = {s: Counter() for s in SLOTS}
    query_rows, hashes = [], {}
    for q, text in sorted(questions.items()):
        rows = []
        for repeat in (1, 2, 3):
            path = PILOT / 'runtime/api/results' / f'E_{q}_r{repeat}.json'
            values = json.loads(path.read_text(encoding='utf-8'))['data']['perspectives']
            assert tuple(r['id'] for r in values) == SLOTS
            hashes[path.relative_to(ROOT).as_posix()] = sha(path)
            for row in values:
                counts[row['id']][row['status']] += 1
                rows.append({'repeat': repeat, 'id': row['id'], 'status': row['status'],
                             'title': row['title'], 'description': row['description'], 'source_quote': row['source_quote']})
        query_rows.append({'query_id': q, 'source_text': text, 'slots': rows,
            'missing': [{'repeat': r['repeat'], 'id': r['id']} for r in rows if r['status'] == 'MISSING'],
            'always_missing_slots': [s for s in SLOTS if all(r['status'] == 'MISSING' for r in rows if r['id'] == s)],
            'varying_presence_slots': [s for s in SLOTS if len({r['status'] for r in rows if r['id'] == s}) > 1]})
    source_paths = [cases_path, 'docs/independent-validation-20261108/ai_pilot/questions.jsonl',
                    'scripts/fixed_three_views.py', 'scripts/fixed_three_corrected.py',
                    'scripts/core_preservation_prompts.py', 'scripts/audit_fixed_view_data_fit_20261109.py']
    hashes.update({p: sha(ROOT / p) for p in source_paths})
    summary = {'cases': len(cases), 'case_nonempty_fields': presence, 'queries': len(questions),
               'query_repeats': 120, 'slot_status_counts': {s: dict(c) for s, c in counts.items()},
               'queries_with_any_missing': [r['query_id'] for r in query_rows if r['missing']],
               'queries_with_always_missing_slot': [r['query_id'] for r in query_rows if r['always_missing_slots']],
               'queries_with_repeat_dependent_missing': [r['query_id'] for r in query_rows if r['varying_presence_slots']]}
    assert presence == {'problem': 112, 'task': 112, 'context': 112}
    assert counts['BUSINESS']['PRESENT'] == counts['TECHNICAL']['PRESENT'] == 120
    assert counts['OPERATIONS']['PRESENT'] == 110 and counts['OPERATIONS']['MISSING'] == 10
    assert len(summary['queries_with_any_missing']) == 7 and not summary['queries_with_always_missing_slot']
    OUT.mkdir()
    with (OUT / 'audit.json').open('x', encoding='utf-8') as target:
        target.write(json.dumps({'state': 'SOURCE_ONLY_FIXED_SLOT_APPLICABILITY_AUDIT', 'summary': summary,
            'case_source_inventory': [{'case_id': c, 'problem': r['problem'], 'task': r['task'], 'context': r['context']} for c, r in sorted(cases.items())],
            'query_rows': query_rows, 'source_sha256': hashes, 'paid_calls': 0, 'new_predictions': 0,
            'relevance_labels_read': False, 'human_slot_gold': False,
            'limits': ['Nonempty fields are structural evidence, not independent semantic validity certification',
                       'Stored model PRESENT/MISSING is output behavior, not ground truth about slot applicability',
                       'Case Problem/Task/Context are not the same categories as query BUSINESS/OPERATIONS/TECHNICAL',
                       'Case summaries, not a new audit of original publications',
                       'No causal performance experiment']}, ensure_ascii=False, indent=2) + '\n')
    saved = json.loads((OUT / 'audit.json').read_text(encoding='utf-8'))
    assert saved['summary'] == summary and all(sha(ROOT / p) == value for p, value in hashes.items())
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
