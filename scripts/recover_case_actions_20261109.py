"""Audit all 112 profiles, recover 24 omissions, export evidence; no query/label reads."""
import hashlib
import json
from pathlib import Path

from ax_research.literal_action_recovery import recover_action_profile
from ax_research.semantic_mapping import field_profile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs/literal-action-recovery-20261109'
SOURCES = ['docs/dense-bm25-candidates-2026-10-27/case_registry.json',
           'docs/query-case-semantic-mapping-2026-10-28/mapping/case_profiles.json',
           'configs/semantic_mapping_20261028.json', 'configs/functional_mapping_20261028.json',
           'configs/literal_action_recovery_20261109.json', 'src/ax_research/semantic_mapping.py',
           'src/ax_research/literal_action_recovery.py', 'scripts/recover_case_actions_20261109.py']


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def build():
    old = read(SOURCES[1])
    cases = read(SOURCES[0])['cases']
    config, grammar, recovery = map(read, SOURCES[2:5])
    before, profiles, audit = [], {}, []
    for case, row in sorted(cases.items()):
        baseline = field_profile(row['task'], config, grammar['negation_guard'], executed=True, context=row['context'])
        assert baseline == old[case], ('Baseline drift', case)
        result = recover_action_profile(row['task'], config, grammar['negation_guard'], recovery,
                                        executed=True, context=row['context'])
        profiles[case] = result
        for field, spans in result['spans'].items():
            source = row['context'] if field == 'context' else row['task']
            for span in spans:
                assert source[span['start']:span['end']] == span['quote'], (case, field, span)
        if baseline['fields']['action']:
            assert all(result[k] == baseline[k] for k in baseline), ('Existing extraction changed', case)
        else:
            before.append(case)
            audit.append({'case_id': case, 'source_task': row['task'],
                          'old_action': baseline['fields']['action'], 'new_action': result['fields']['action'],
                          'old_object': baseline['fields']['object'], 'new_object': result['fields']['object'],
                          'evidence': result['action_recovery']['added_evidence'],
                          'cause': 'No old action-pattern match in supported Task clauses',
                          'status': result['action_recovery']['status']})
    assert len(before) == 24 and len(profiles) == 112
    missing_after = [c for c, p in profiles.items() if not p['fields']['action']]
    assert not missing_after, missing_after
    summary = {'state': 'EXTRACTION_REPAIR_ONLY_NOT_RETRIEVAL_EVALUATION', 'case_count': len(profiles),
               'missing_action_before': len(before), 'missing_action_after': len(missing_after),
               'existing_nonempty_profiles_unchanged': len(profiles) - len(before),
               'recovered_case_count': len(audit), 'literal_span_checks_passed': True,
               'paid_calls': 0, 'qrels_read': False, 'queries_read': False, 'test15_read': False,
               'new40_read': False, 'embeddings_recomputed': False, 'rankings_changed': False,
               'original_publication_reaudited': False,
               'source_sha256': {p: digest(p) for p in SOURCES},
               'limits': ['Development-corpus-informed lexical coverage repair',
                          'Source is stored Task summary, not reverified publication',
                          'Literal coverage is not semantic correctness or relevance accuracy',
                          'Residual object remains shallow; outcomes are not inferred',
                          'Old embeddings and 480 missing action cosines remain unchanged']}
    return profiles, audit, summary


def main():
    profiles, audit, summary = build()
    DEST.mkdir(exist_ok=False)
    for name, value in [('case_profiles.json', profiles), ('missing24-audit.json', audit), ('verification.json', summary)]:
        with (DEST / name).open('x', encoding='utf-8') as target:
            target.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'source_sha256'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
