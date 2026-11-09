"""Evidence-first pilot case suggestions, preserving selected perspective branches."""
import re

from ax_research.pilot_perspective_selector import select_perspectives


def _evidence(question, clauses, pattern):
    found = []
    for clause in clauses:
        for match in re.finditer(pattern, clause['quote'], re.I):
            start, end = clause['start'] + match.start(), clause['start'] + match.end()
            found.append({'quote': question[start:end], 'start': start, 'end': end, 'clause': clause['quote']})
    return found


def requirements(question, selection, profiles):
    active = [c for c in selection['clauses'] if c['role'] in ('requested', 'problem')]
    if not active:
        active = [c for c in selection['clauses'] if c['role'] == 'unspecified']
    result = {'objects': [], 'inputs': [], 'domains': [], 'fields': [], 'evidence': [],
              'same_domain_only': bool(_evidence(question, active, r'(?:같은|동일)\s*업종.{0,5}만') or _evidence(question, selection['constraints'], r'다른\s*업종.{0,8}제외')),
              'direct_only': bool(_evidence(question, active, r'직접.{0,5}(?:사례|일치).{0,5}만') or _evidence(question, selection['constraints'], r'응용.{0,5}제외')),
              'read_only_required': bool(_evidence(question, active, r'읽기\s*전용|read.only'))}
    for key, rule_name in [('objects', 'object_rules'), ('inputs', 'input_rules'), ('domains', 'domain_rules')]:
        for rule in profiles[rule_name]:
            evidence = _evidence(question, active, rule['pattern'])
            if evidence:
                result[key].append(rule['value'])
                result['evidence'].extend([{**e, 'kind': key, 'value': rule['value']} for e in evidence])
    if not result['objects']:
        for pattern, value in [(r'청구서|송장', 'billing_document'), (r'문의|상담', 'customer_inquiry'),
                               (r'문서|서류|자료|기록', 'document')]:
            evidence = _evidence(question, active, pattern)
            if evidence:
                result['objects'] = [value]
                result['evidence'].extend([{**e, 'kind': 'objects', 'value': value} for e in evidence])
                break
    for field in profiles['field_rules']:
        evidence = _evidence(question, active, re.escape(field))
        if evidence:
            result['fields'].append(field)
            result['evidence'].extend([{**e, 'kind': 'fields', 'value': field} for e in evidence])
    text = '\n'.join(c['quote'] for c in active)
    result['reference'] = ('agreed_rates' if re.search(r'계약|약정|요율', text) and re.search(r'금액|가격|요율|청구서|송장', text)
                           else 'required_fields' if re.search(r'필수|완전성|누락', text) else None)
    return result


def _key(record):
    return (0 if record['relationship'] == 'DIRECT_WORK_TYPE_CANDIDATE' else 1,
            -record.get('semantic_task_cosine', -1.), record['case_id'])


def allocate(routes, limit):
    """Late coverage-first display allocation, not RRF or relevance probability."""
    merged = {}
    for card, rows in routes.items():
        for row in rows:
            case = row['case_id']
            if case not in merged:
                merged[case] = {'case_id': case, 'routes': [], 'best': row}
            merged[case]['routes'].append(row)
            if _key(row) < _key(merged[case]['best']):
                merged[case]['best'] = row
    chosen = []
    branch_order = sorted((rows[0] for rows in routes.values() if rows), key=_key)
    for first in branch_order:
        if len(chosen) == limit:
            break
        if first['case_id'] not in chosen:
            chosen.append(first['case_id'])
    for item in sorted(merged.values(), key=lambda value: _key(value['best'])):
        if len(chosen) == limit:
            break
        if item['case_id'] not in chosen:
            chosen.append(item['case_id'])
    return [merged[case] for case in chosen]


def recommend_cases(question, catalog, selector_rules, profiles, registry, scorer, *, max_results=5, max_candidates=20):
    if not isinstance(max_results, int) or not isinstance(max_candidates, int) or not 1 <= max_results <= max_candidates <= 20:
        raise ValueError('출력/후보 예산은 1 <= 출력 <= 후보 <= 20이어야 합니다.')
    selection = select_perspectives(question, catalog, selector_rules)
    req = requirements(question, selection, profiles)
    cards = {c['id']: c for c in catalog['cards']}
    routes, deferred, branch_requirements = {}, [], {}
    for selected in selection['selected']:
        card = cards[selected['id']]
        work_ranges = {(e['clause_start'], e['clause_end']) for e in selected['evidence'] if e['kind'] == 'work'}
        other_work_ranges = {(e['clause_start'], e['clause_end']) for other in selection['selected'] if other['id'] != selected['id']
                             for e in other['evidence'] if e['kind'] == 'work'}
        object_ranges = {(e['clause_start'], e['clause_end']) for e in selected['evidence'] if e['kind'] == 'object'}
        own_ranges = work_ranges | {r for r in object_ranges if r not in other_work_ranges}
        own_clauses = [c for c in selection['clauses'] if (c['start'], c['end']) in own_ranges]
        own_selection = {**selection, 'clauses': own_clauses}
        branch_req = requirements(question, own_selection, profiles)
        # Permissions explicitly requested for the whole question remain conservative global gates.
        branch_req['read_only_required'] = branch_req['read_only_required'] or req['read_only_required']
        branch_requirements[card['id']] = branch_req
        candidates = []
        for link in card['links']:
            if link['status'] != 'SUPPORTED_FOR_PILOT':
                continue
            case = link['case_id']
            data = profiles['cases'][case]
            source = registry[case]
            for span in link['evidence']:
                assert source[span['field']][span['start']:span['end']] == span['quote']
            missing = sorted(set(branch_req['inputs']) - set(data['input_conditions']))
            if branch_req['read_only_required']:
                missing.append('원문에 읽기 전용 구현이 명시됐는지 추가 확인')
            if branch_req['same_domain_only'] and (not branch_req['domains'] or not set(branch_req['domains']) & set(data['domains'])):
                missing.append('동일 업종 조건을 확인할 근거 부족')
            object_match = not branch_req['objects'] or bool(set(branch_req['objects']) & set(data['objects']))
            domain_diff = bool(branch_req['domains']) and not bool(set(branch_req['domains']) & set(data['domains']))
            reference_diff = card['id'] == 'P03' and branch_req['reference'] is not None and branch_req['reference'] not in data.get('references', [])
            direct = object_match and not domain_diff and not reference_diff
            if branch_req['direct_only'] and not direct:
                missing.append('직접 업무 유형 일치 조건의 근거 부족')
            relationship = 'DIRECT_WORK_TYPE_CANDIDATE' if direct else 'FUNCTIONAL_TRANSFER_CANDIDATE'
            unknown_fields = [field for field in branch_req['fields'] if field not in data['known_fields']]
            notes = []
            if not object_match:
                notes.append('수행 기능은 관련되지만 자료·대상이 달라 전이 가능성 검토가 필요합니다.')
            if domain_diff:
                notes.append('요청 업종과 사례 맥락이 달라 적용 조건을 확인해야 합니다.')
            if reference_diff:
                notes.append('질문의 대조 기준을 사례가 그대로 지원하는지는 확인되지 않았습니다.')
            if unknown_fields:
                notes.append('요청한 세부 항목의 지원이 명시되지 않음: ' + ', '.join(unknown_fields))
            notes += [link['condition_limit'], '정확한 출력 형식·정확도·새 환경의 적용 성공은 이 요약으로 보장하지 않습니다.']
            record = {'case_id': case, 'perspective_id': card['id'], 'relationship': relationship,
                'supported_work': link['supported_scope'], 'link_reason': link['reason'],
                'source': {'problem': source['problem'], 'task': source['task'], 'context': source['context']},
                'source_evidence': link['evidence'], 'query_evidence': selected['evidence'],
                'metadata_interpretation': data, 'required_input_unknown': missing, 'unverified_fields': unknown_fields,
                'conditions_to_confirm': notes, 'confirmed_query_answer': False,
                'source_metadata_is_independent_gold': False}
            if missing:
                record['status'] = 'CONDITION_CONFIRMATION_REQUIRED_NOT_RECOMMENDED'
                deferred.append(record)
            else:
                record['status'] = 'REFERENCE_CANDIDATE_WITH_LIMITS'
                candidates.append(record)
        if candidates:
            work_spans = [e for e in selected['evidence'] if e['kind'] == 'work']
            query_text = '\n'.join(dict.fromkeys(e['clause_quote'] for e in work_spans))
            values = scorer(card['id'], query_text or question, [r['case_id'] for r in candidates])
            if set(values) != {r['case_id'] for r in candidates}:
                raise ValueError('정렬 점수의 사례 집합이 후보와 다릅니다.')
            for record in candidates:
                value = float(values[record['case_id']])
                if not -1.00001 <= value <= 1.00001:
                    raise ValueError('정렬 보조 cosine 값이 유효하지 않습니다.')
                record['semantic_task_cosine'] = value
            candidates.sort(key=_key)
        routes[card['id']] = candidates
    bounded = allocate(routes, max_candidates)
    candidate_ids = {r['case_id'] for r in bounded}
    routes = {p: [r for r in rows if r['case_id'] in candidate_ids] for p, rows in routes.items()}
    chosen = allocate(routes, max_results)
    results = []
    for index, item in enumerate(chosen, 1):
        results.append({'display_order': index, 'case_id': item['case_id'], 'task': registry[item['case_id']]['task'],
                        'perspective_ids': [r['perspective_id'] for r in item['routes']],
                        'relationship': item['best']['relationship'], 'routes': item['routes']})
    represented = {p for r in results for p in r['perspective_ids']}
    missing_branches = [p for p in routes if p not in represented]
    if not selection['selected']:
        state = selection['state']
    elif not results:
        state = 'NO_SOURCE_SUPPORTED_CASE_FOR_REQUIRED_CONDITIONS'
    elif selection['state'] == 'PARTIAL_MATCH' or missing_branches:
        state = 'PARTIAL_REFERENCE_SUPPORT'
    else:
        state = 'REFERENCE_CANDIDATES_WITH_LIMITS'
    return {'question': question, 'version': 'pilot-case-recommender-v1.2-20261109', 'state': state,
            'perspective_selection': selection, 'requirements': req, 'recommendations': results,
            'requirements_by_perspective': branch_requirements,
            'branches': routes, 'condition_confirmation_queue': deferred, 'unrepresented_perspectives': missing_branches,
            'candidate_budget': max_candidates, 'output_budget': max_results,
            'unique_eligible_candidates': len(candidate_ids), 'paid_calls': 0,
            'automatic_execution_performed': False, 'relevance_accuracy_validated': False,
            'limits': 'Assistant-curated source conditions and fixed local Task cosine; no performance or application-success guarantee'}
