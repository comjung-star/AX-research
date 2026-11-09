"""Small query-balanced pairwise scorer; IDs and held-out labels are not features."""
import numpy as np


def unit(values):
    values = np.asarray(values, dtype=float)
    if not np.isfinite(values).all():
        raise ValueError('Nonfinite features')
    spread = np.ptp(values)
    return (values - values.min()) / spread if spread > 1e-12 else np.zeros_like(values)


def fit_pairwise(features, labels, queries, regularization):
    """Every informative training query contributes total pair weight one."""
    queries = tuple(queries)
    if not queries or regularization <= 0:
        raise ValueError('Need training queries and positive regularization')
    size = next(iter(features.values())).shape[1]
    gram, target = np.zeros((size, size)), np.zeros(size)
    informative = 0
    for query in queries:
        x, y = np.asarray(features[query]), np.asarray(labels[query], dtype=bool)
        if len(x) != len(y):
            raise ValueError('Label/feature registry differs')
        if not y.any() or y.all():
            continue
        differences = (x[y, None, :] - x[None, ~y, :]).reshape(-1, size)
        gram += differences.T @ differences / len(differences)
        target += differences.mean(axis=0)
        informative += 1
    if informative:
        gram /= informative
        target /= informative
    weights = np.linalg.solve(gram + regularization * np.eye(size), target)
    return weights


def score(features, weights, learned_share):
    if not 0 <= learned_share <= 1:
        raise ValueError('Invalid mixing weight')
    return (1 - learned_share) * features[:, 0] + learned_share * unit(features @ weights)


def rank_pool(ids, scores, pool, dense_order):
    if len(set(pool)) != 20 or not set(pool) <= set(ids):
        raise ValueError('Need exactly 20 unique registered candidates')
    values = dict(zip(ids, map(float, scores)))
    positions = {case: index for index, case in enumerate(dense_order)}
    chosen = sorted(pool, key=lambda case: (-values[case], positions[case]))
    return chosen + [case for case in dense_order if case not in set(pool)]
