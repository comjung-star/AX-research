"""Protect Dense head ranks and admit branch candidates using original-query evidence."""
from collections.abc import Mapping, Sequence

import numpy as np

from ax_research.token_interaction import normalize_scores


def preserve_dense(dense_scores: Mapping[str, float], token_scores: Mapping[str, float],
                   branch_rankings: Mapping[str, Sequence[str]] | None = None, *, budget=20, protected=3):
    ids = tuple(sorted(dense_scores))
    if set(token_scores) != set(ids) or not 5 <= budget <= len(ids) or not 0 <= protected < 5:
        raise ValueError('Invalid registries, candidate budget or protected count')
    dense_values = normalize_scores([dense_scores[case] for case in ids])
    token_values = normalize_scores([token_scores[case] for case in ids])
    semantic = dict(zip(ids, map(float, token_values)))
    scores = dict(zip(ids, map(float, .5 * dense_values + .5 * token_values)))
    dense = sorted(ids, key=lambda case: (-dense_scores[case], case))
    original_free = dense[protected:5]
    score_floor = min(scores[case] for case in original_free)
    token_floor = min(semantic[case] for case in original_free)
    eligible = {case for case in ids if scores[case] > score_floor + 1e-12 and semantic[case] > token_floor + 1e-12}
    branches = branch_rankings or {}
    for ranking in branches.values():
        if len(ranking) != len(ids) or len(set(ranking)) != len(ids) or set(ranking) != set(ids):
            raise ValueError('Branch ranking registry differs from Dense')
    provenance = {}
    if branches:
        pool = list(dense[:max(5, budget // 2)])
        for position in range(len(ids)):
            for path in sorted(branches):
                case = branches[path][position]
                if case not in pool and case in eligible and len(pool) < budget:
                    pool.append(case)
                    provenance[case] = {'first_path': path, 'path_rank': position + 1,
                                        'original_hybrid': scores[case], 'original_token_normalized': semantic[case]}
            if len(pool) == budget:
                break
        for case in dense:
            if len(pool) == budget:
                break
            if case not in pool:
                pool.append(case)
    else:
        pool = list(dense[:budget])
    allowed = [case for case in pool if case in eligible or case in original_free]
    ordered = sorted(allowed, key=lambda case: (-scores[case], case))
    head = dense[:protected]
    free = [case for case in ordered if case not in head][:5 - protected]
    assert len(free) == 5 - protected
    chosen = head + free
    tail = sorted(set(pool) - set(chosen), key=lambda case: (-scores[case], case))
    ranking = chosen + tail + [case for case in dense if case not in pool]
    assert len(pool) == budget and ranking[:protected] == dense[:protected]
    assert len(ranking) == len(set(ranking)) == len(ids)
    return {'ranking': ranking, 'candidates': pool, 'protected_ids': head,
            'branch_candidates': provenance, 'original_scores': scores,
            'admission_score_floor': score_floor, 'admission_token_floor': token_floor,
            'dense_original_top5': dense[:5], 'selected_new_top5': [case for case in chosen if case not in dense[:5]],
            'lost_dense_top5': [case for case in dense[:5] if case not in chosen],
            'candidate_budget': budget, 'output_budget': 5, 'labels_used': False}
