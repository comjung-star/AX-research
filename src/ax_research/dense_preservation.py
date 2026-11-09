"""Protect Dense head ranks and admit branch candidates using original-query evidence."""
from collections.abc import Mapping, Sequence

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


def preserve_dense_core(dense_scores, token_scores, core_scores, branch_rankings=None, *, budget=20, source_depth=None):
    initial = preserve_dense(dense_scores, token_scores, budget=budget)
    dense = sorted(dense_scores, key=lambda case: (-dense_scores[case], case))
    if set(core_scores) != set(dense):
        raise ValueError('Core evidence registry differs')
    scores = initial['original_scores']
    dense_positions = {case: position for position, case in enumerate(dense)}
    branches = branch_rankings or {}
    for ranking in branches.values():
        if len(ranking) != len(dense) or set(ranking) != set(dense) or len(set(ranking)) != len(dense):
            raise ValueError('Branch registry differs')
    def dominates(candidate, previous):
        candidate_core, previous_core = core_scores[candidate], core_scores[previous]
        return (all(candidate_core.get(field) is not None and previous_core.get(field) is not None for field in ('action', 'object'))
                and scores[candidate] > scores[previous] + 1e-12
                and all(candidate_core[field] > previous_core[field] + 1e-12 for field in ('action', 'object')))
    pool = dense[:budget]
    mandatory = set(dense[:max(5, budget // 2)])
    admissions = []
    if source_depth is not None and not 0 < source_depth <= len(dense):
        raise ValueError('Invalid source retrieval depth')
    for position in range(source_depth or len(dense)):
        for path in sorted(branches):
            candidate = branches[path][position]
            if candidate in pool:
                continue
            replaceable = sorted((case for case in pool if case not in mandatory), key=lambda case: (scores[case], case))
            previous = next((case for case in replaceable if dominates(candidate, case)), None)
            if previous is not None:
                pool[pool.index(previous)] = candidate
                admissions.append({'candidate': candidate, 'replaced': previous, 'path': path,
                                   'path_rank': position + 1, 'candidate_core': core_scores[candidate], 'previous_core': core_scores[previous]})
    selected = dense[:5]
    replacements = []
    for candidate in sorted(pool, key=lambda case: (-scores[case], case)):
        if candidate in selected:
            continue
        possible = sorted(selected[3:], key=lambda case: (scores[case], case))
        previous = next((case for case in possible if dominates(candidate, case)), None)
        if previous is not None:
            selected[selected.index(previous)] = candidate
            replacements.append({'candidate': candidate, 'replaced': previous, 'candidate_core': core_scores[candidate],
                                 'previous_core': core_scores[previous], 'candidate_hybrid': scores[candidate], 'previous_hybrid': scores[previous]})
    tail = sorted(set(pool) - set(selected), key=dense_positions.get)
    ranking = selected + tail + [case for case in dense if case not in pool]
    assert ranking[:3] == dense[:3] and len(pool) == budget and len(ranking) == len(set(ranking)) == len(dense)
    return {'ranking': ranking, 'candidates': pool, 'protected_ids': dense[:3], 'protected_candidate_ids': sorted(mandatory, key=dense_positions.get),
            'core_replacements': replacements, 'branch_candidates': {row['candidate']: row for row in admissions if row['candidate'] in pool},
            'candidate_admissions': admissions, 'original_scores': scores,
            'dense_original_top5': dense[:5], 'selected_new_top5': [case for case in selected if case not in dense[:5]],
            'lost_dense_top5': [case for case in dense[:5] if case not in selected],
            'candidate_budget': budget, 'output_budget': 5, 'labels_used': False}


def preserve_dense_candidates(dense_scores, token_scores, core_scores, source_rankings=None, *, budget=20):
    result = preserve_dense_core(dense_scores, token_scores, core_scores, source_rankings,
                                 budget=budget, source_depth=budget)
    dense = sorted(dense_scores, key=lambda case: (-dense_scores[case], case))
    pool = set(result['candidates'])
    ranking = [case for case in dense if case in pool] + [case for case in dense if case not in pool]
    assert ranking[:max(5, budget // 2)] == dense[:max(5, budget // 2)]
    return {**result, 'ranking': ranking, 'core_replacements': [], 'selected_new_top5': [], 'lost_dense_top5': [],
            'protected_output_count': max(5, budget // 2), 'method': 'CANDIDATE_COMPLEMENT_ONLY_NOT_FINAL_RERANKING'}
