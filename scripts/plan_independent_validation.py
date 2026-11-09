"""Freeze sources and estimate independent-test size without new API calls."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import norm

from scripts.improvement_cycle import ROOT, read

OUT = ROOT / 'docs/independent-validation-20261108'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def required_pairs(deviation, effect, alpha=.05 / 6, power=.8):
    if deviation < 0 or effect <= 0 or not 0 < alpha < 1 or not 0 < power < 1:
        raise ValueError('Invalid planning parameters')
    return max(2, math.ceil(((norm.ppf(1 - alpha / 2) + norm.ppf(power)) * deviation / effect) ** 2))


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    artifact = read('docs/improvement-cycle10-20261108-results.json')
    rows = []
    for version, result in artifact['results'].items():
        for baseline in ('Dense', 'E', 'token_hybrid_single'):
            for metric, effect in [('F1@5', .05), ('nDCG@10', .03)]:
                differences = np.asarray([row['token_hybrid_multi'][metric] - row[baseline][metric]
                                          for row in result['per_query'].values() if row[baseline][metric] is not None])
                deviation = float(np.std(differences, ddof=1))
                rows.append({'label_version': version, 'baseline': baseline, 'metric': metric,
                             'pilot_queries': len(differences), 'paired_sd': deviation, 'observed_delta': float(differences.mean()),
                             'planning_effect': effect, 'eligible_queries_normal_approximation': required_pairs(deviation, effect),
                             'effect_sensitivity': {str(value): required_pairs(deviation, value) for value in (.01, .03, .05, .10)}})
    sources = ['src/ax_research/token_interaction.py', 'src/ax_research/action_aggregation.py',
               'src/ax_research/functional_mapping.py', 'src/ax_research/semantic_mapping.py',
               'configs/action_aggregation_20261102.json', 'configs/functional_mapping_20261028.json',
               'configs/semantic_mapping_20261028.json', 'scripts/core_preservation_prompts.py',
               'docs/dense-bm25-candidates-2026-10-27/case_registry.json',
               'docs/improvement-cycle10-20261108-results.json', 'docs/reusable-token-ranker-verification.json']
    required = max(row['eligible_queries_normal_approximation'] for row in rows)
    total = math.ceil(required / .8)
    output = {'state': 'PLANNING_ONLY_NOT_A_TEST_RESULT', 'alpha_family': .05, 'contrasts': 6,
              'alpha_each_two_sided': .05 / 6, 'power_per_contrast_assumption': .8,
              'power_is_not_joint_probability_of_passing_all_contrasts': True,
              'rows': rows, 'conservative_planning_envelope_eligible_queries': required,
              'positive_query_fraction_assumption': .8, 'total_queries_at_assumed_fraction': total,
              'case_pairs_at_assumed_total': total * 112,
              'limits': ['Normal approximation using SD estimates from16-18 repeatedly inspected queries',
                         'Not a guarantee of power; variance and positive fraction can change',
                         'No sample size has been represented as actual collected independent data',
                         'Power plan tests superiority over0 when true effects are5pp F1 and3pp nDCG; not lower CI above those effects'],
              'reference': 'https://itl.nist.gov/div898/handbook/prc/section2/prc222.htm'}
    freeze = {'state': 'CANDIDATE_AND_HISTORICAL_COMPARATOR_SOURCE_FREEZE',
              'sha256': {path: digest(ROOT / path) for path in sources},
              'model_hashes': read('docs/core-preserved-three-views-2026-11-07/preregistration.json')['environment']['model'],
              'runtime': 'Same frozen BGE-M3; Task-token candidate10; original E as historical comparator',
              'generation': 'Original frozen core_preservation_prompts/model policy required for new branches; no new calls authorized',
              'test15_accessed': False, 'new_test_queries_collected': 0, 'paid_calls': 0}
    OUT.mkdir()
    (OUT / 'sample_size_planning.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'source_freeze.json').write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'eligible_queries_envelope': required, 'total_queries_at_80pct_positive': total,
                      'case_pairs': total * 112, 'per_contrast_rows': rows}, ensure_ascii=True))


if __name__ == '__main__':
    main()
