"""Label-free late token/Dense interaction candidate, separate from production E."""
from collections.abc import Mapping

import numpy as np
import torch


def normalize_scores(values):
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError('Expected a nonempty finite score vector')
    spread = values.max() - values.min()
    return (values - values.min()) / spread if spread > 0 else np.zeros_like(values)


def token_tensor(values):
    array = np.asarray(values, dtype=np.float32)
    if array.ndim != 2 or not all(array.shape) or not np.isfinite(array).all():
        raise ValueError('Token outputs must be a nonempty finite matrix')
    return torch.from_numpy(array)


class TokenInteractionRanker:
    """Frozen candidate10: Task-token MaxSim, CLS Dense and late branch fusion."""

    def __init__(self, case_task_tokens: Mapping[str, np.ndarray]):
        if not case_task_tokens:
            raise ValueError('Case registry is empty')
        self.case_ids = tuple(sorted(case_task_tokens))
        tensors = [token_tensor(case_task_tokens[case]) for case in self.case_ids]
        self.dimensions = tensors[0].shape[1]
        if any(values.shape[1] != self.dimensions for values in tensors):
            raise ValueError('Case token dimensions differ')
        self.center = torch.cat(tensors).mean(dim=0)
        self.lengths = [len(values) for values in tensors]
        self.case_matrix = torch.cat([torch.nn.functional.normalize(values - self.center, dim=1) for values in tensors])

    def token_scores(self, query_tokens):
        values = token_tensor(query_tokens)
        if values.shape[1] != self.dimensions:
            raise ValueError('Query and case token dimensions differ')
        normalized = torch.nn.functional.normalize(values - self.center, dim=1)
        with torch.inference_mode():
            similarities = normalized @ self.case_matrix.T
            return np.asarray([float(part.max(dim=1).values.mean()) for part in similarities.split(self.lengths, dim=1)])

    def hybrid_scores(self, query_tokens, dense_scores):
        if set(dense_scores) != set(self.case_ids):
            raise ValueError('Dense scores must cover exactly the case registry')
        dense = [dense_scores[case] for case in self.case_ids]
        token = self.token_scores(query_tokens)
        return .5 * normalize_scores(dense) + .5 * normalize_scores(token)

    def rank(self, query_tokens, dense_scores, branches=None):
        original = self.hybrid_scores(query_tokens, dense_scores)
        branches = branches or {}
        branch_ids = tuple(branches)
        branch_scores = {}
        if branch_ids:
            similarity = np.asarray([branches[path]['query_cosine'] for path in branch_ids], dtype=np.float64)
            if not np.isfinite(similarity).all():
                raise ValueError('Branch fidelity must be finite')
            logits = similarity / .1
            weights = np.exp(logits - logits.max())
            weights /= weights.sum()
            for path in branch_ids:
                branch_scores[path] = self.hybrid_scores(branches[path]['tokens'], branches[path]['dense_scores'])
            final = .5 * original + .5 * sum(weight * branch_scores[path] for weight, path in zip(weights, branch_ids))
        else:
            weights = np.asarray([])
            final = original
        scores = dict(zip(self.case_ids, map(float, final)))
        return {'ranking': sorted(self.case_ids, key=lambda case: (-scores[case], case)), 'scores': scores,
                'original_hybrid': dict(zip(self.case_ids, map(float, original))),
                'branch_scores': {path: dict(zip(self.case_ids, map(float, values))) for path, values in branch_scores.items()},
                'branch_weights': dict(zip(branch_ids, map(float, weights))), 'method': 'FROZEN_CANDIDATE10',
                'trained_on_labels': False}
