"""Fixed-budget metrics for partial-output catalog retrieval, without label fitting."""
import math
from statistics import mean

import numpy as np

SYSTEMS = ('A_Dense17', 'B_Task17', 'C_Catalog17', 'D_ViewsNoConditions17')
CONTRASTS = (('C_Catalog17', 'A_Dense17'), ('C_Catalog17', 'B_Task17'),
             ('D_ViewsNoConditions17', 'B_Task17'), ('C_Catalog17', 'D_ViewsNoConditions17'))


def metrics(ranking, candidates, grades, k=5):
    if len(ranking) != len(set(ranking)) or len(candidates) != len(set(candidates)):
        raise ValueError('Duplicate case in ranking/candidates')
    if not set(ranking) <= set(candidates) <= set(grades):
        raise ValueError('Ranking/candidates outside the judged corpus')
    output = ranking[:k]
    positive = {c for c, g in grades.items() if g >= 2}
    hits = sum(c in positive for c in output)
    gain = lambda g: 2 ** g - 1 if g >= 2 else 0
    dcg = sum(gain(grades[c]) / math.log2(i + 2) for i, c in enumerate(output))
    ideal = sum(gain(g) / math.log2(i + 2) for i, g in enumerate(sorted(grades.values(), reverse=True)[:k]))
    return {'P@5_slots': hits / k, 'emitted_precision': hits / len(output) if output else None,
            'Recall@5': hits / len(positive) if positive else None,
            'F1@5': 2 * hits / (len(output) + len(positive)) if positive else None,
            'nDCG@5': dcg / ideal if ideal else None,
            'Recall@20_candidates': len(set(candidates[:20]) & positive) / len(positive) if positive else None,
            'hits': hits, 'emitted': len(output), 'positives': len(positive),
            'positive_but_empty': bool(positive and not output),
            'zero_positive_but_emitted': bool(not positive and output)}


def paired_interval(differences):
    if not differences:
        return {'queries': 0, 'delta': None, 'interval95': None, 'interval_bonferroni8': None}
    values = np.asarray(differences, dtype=float)
    rng = np.random.default_rng(20261109)
    samples = values[rng.integers(len(values), size=(10000, len(values)))].mean(axis=1)
    return {'queries': len(values), 'delta': float(values.mean()),
            'interval95': np.quantile(samples, [.025, .975]).tolist(),
            'interval_bonferroni8': np.quantile(samples, [.05 / 16, 1 - .05 / 16]).tolist(),
            'improved': int(sum(values > 1e-12)), 'harmed': int(sum(values < -1e-12)),
            'unchanged': int(sum(abs(values) <= 1e-12)), 'resamples': 10000}


def summarize(rows, systems=SYSTEMS):
    result = {}
    for name in systems:
        values = [r[name] for r in rows.values()]
        result[name] = {}
        for metric in ('P@5_slots', 'emitted_precision', 'Recall@5', 'F1@5', 'nDCG@5', 'Recall@20_candidates'):
            eligible = [v[metric] for v in values if v[metric] is not None]
            result[name][metric] = {'queries': len(eligible), 'mean': mean(eligible) if eligible else None}
        result[name]['output'] = {'questions': len(values), 'emitted': sum(v['emitted'] for v in values),
            'hits': sum(v['hits'] for v in values), 'empty_questions': sum(v['emitted'] == 0 for v in values),
            'positive_but_empty': sum(v['positive_but_empty'] for v in values),
            'zero_positive_but_emitted': sum(v['zero_positive_but_emitted'] for v in values)}
        count = result[name]['output']['emitted']
        result[name]['micro_emitted_precision'] = result[name]['output']['hits'] / count if count else None
    return result


def assess(predictions, grades, corpus):
    """All queries retained; relevance metrics NA only when no positives exist."""
    rows, counts = {}, {}
    for q, prediction in predictions.items():
        judged = {c: grades[q][c] for c in corpus}
        rows[q] = {s: metrics(prediction['systems'][s]['ranking'], prediction['systems'][s]['candidates'], judged) for s in SYSTEMS}
        counts[q] = sum(g >= 2 for g in judged.values())
    contrasts = {}
    for method, baseline in CONTRASTS:
        contrasts[method + ':' + baseline] = {metric: paired_interval([
            r[method][metric] - r[baseline][metric] for r in rows.values() if r[method][metric] is not None])
            for metric in ('F1@5', 'nDCG@5')}
    return {'summary': summarize(rows), 'per_query': rows, 'positive_counts': counts,
            'positive_questions': sum(v > 0 for v in counts.values()), 'contrasts': contrasts}
