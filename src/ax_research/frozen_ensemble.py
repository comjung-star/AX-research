"""Apply saved fold models with a fixed arithmetic score mean; never train."""
import numpy as np

from ax_research.pairwise_ridge import score


def mean_fold_scores(features, models):
    features = np.asarray(features, dtype=float)
    if features.ndim != 2 or not np.isfinite(features).all() or len(models) != 5:
        raise ValueError('Expected finite features and five fixed models')
    predictions = []
    for model in models:
        weights = np.asarray(model['weights'], dtype=float)
        if weights.shape != (features.shape[1],) or not np.isfinite(weights).all():
            raise ValueError('Frozen weight dimensions differ')
        predictions.append(score(features, weights, model['learned_share']))
    return np.mean(predictions, axis=0)
