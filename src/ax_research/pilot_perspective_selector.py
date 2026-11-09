"""Conservative four-card work/object/condition selector with literal explanations."""
import re

REQUEST = r'싶|원합|원하|필요|주세요|주십시오|줘|어떻게|찾아|검색해|조회해|추출해|검증해|대조해|확인해|뽑아'
NEGATIVE = r'않|지\s*마|말고|말며|금지|제외|필요\s*없|안\s*(?:됩|되|돼|해|하)'
FAILURE = r'잘.{0,3}되지\s*않|찾지\s*못|처리.{0,4}못|응대.{0,4}못|기능.{0,4}안\s*돼'
PAST = r'과거에는|예전에는|이전에는|(?:과거|예전).{0,30}(?:했|사용했|수행했)|했던|했었'
APPROVAL = r'(?:사람|담당자|팀장|책임자).{0,20}승인|승인.{0,8}(?:후|필요|받)|승인을\s*거쳐'
BURDEN = r'시간.{0,12}(?:걸|오래|소요)|어려|지연|누락|부담|대기|반복|못|밀리|밀려|쏠리|공백|몰리|몰려'


def _spans(pattern, question, clauses, kind):
    result = []
    for clause in clauses:
        for match in re.finditer(pattern, clause['quote'], re.I):
            start = clause['start'] + match.start()
            end = clause['start'] + match.end()
            result.append({'kind': kind, 'quote': question[start:end], 'start': start, 'end': end,
                           'clause_quote': clause['quote'], 'clause_start': clause['start'], 'clause_end': clause['end'],
                           'clause_role': clause['role']})
    return result


def scope_clauses(question):
    pieces = []
    def add(start, end):
        while start < end and question[start].isspace():
            start += 1
        while end > start and question[end - 1].isspace():
            end -= 1
        text = question[start:end]
        if not text:
            return
        if re.search(NEGATIVE, text) and not re.search(FAILURE, text):
            role = 'excluded'
        elif re.search(PAST, text):
            role = 'historical'
        elif re.search(APPROVAL, text) and not re.search(REQUEST, text):
            role = 'human_approval'
        elif re.search(REQUEST, text):
            role = 'requested'
        elif re.search(BURDEN, text):
            role = 'problem'
        else:
            role = 'unspecified'
        pieces.append({'quote': text, 'start': start, 'end': end, 'role': role})
    for sentence in re.finditer(r'[^.!?;。；\n]+', question):
        text = sentence.group()
        cut = None
        for boundary in re.finditer(r'(?:말고|말며|않고|않으며|하지만|하되|들되|하고|이며|하며)\s*|,\s*', text):
            left, right = text[:boundary.end()], text[boundary.end():]
            neg_left = bool(re.search(NEGATIVE, left) and not re.search(FAILURE, left))
            neg_right = bool(re.search(NEGATIVE, right) and not re.search(FAILURE, right))
            if ((neg_left and re.search(r'말고|말며|않고|않으며', boundary.group()))
                or (neg_left and re.search(REQUEST, right))
                or (re.search(PAST, left) and re.search(REQUEST, right))
                or (not neg_left and (re.search(REQUEST, left) or '만' in left) and neg_right)):
                cut = sentence.start() + boundary.end()
                break
        if cut is None:
            add(sentence.start(), sentence.end())
        else:
            add(sentence.start(), cut)
            add(cut, sentence.end())
    return pieces


def select_perspectives(question, catalog, rules):
    if not isinstance(question, str) or not question.strip():
        raise ValueError('질문을 입력해야 합니다.')
    if catalog['version'] != rules['catalog_version']:
        raise ValueError('관점 목록 버전이 선택 규칙과 다릅니다.')
    cards = {c['id']: c for c in catalog['cards']}
    if set(cards) != set(rules['cards']):
        raise ValueError('선택 규칙과 시범 카드가 일치하지 않습니다.')
    clauses = scope_clauses(question)
    requests = [c for c in clauses if c['role'] == 'requested']
    problems = [c for c in clauses if c['role'] == 'problem']
    active = requests + problems
    # Bare keyword queries are allowed, but historical/excluded material is never reused.
    if not active:
        active = [c for c in clauses if c['role'] == 'unspecified']
    excluded = [c for c in clauses if c['role'] == 'excluded']
    constraints = excluded + [c for c in clauses if c['role'] == 'human_approval']
    constraints += _spans(APPROVAL, question, clauses, 'approval_condition')
    outside = []
    for rule in rules['outside_work']:
        matches = _spans(rule['pattern'], question, requests if requests else active, 'outside_work')
        if matches:
            outside.append({'id': rule['id'], 'reason': rule['reason'], 'evidence': matches})
    any_known_work = any(_spans(r['work'], question, requests if requests else active, 'work')
                         and _spans(r['object'], question, active, 'object') for r in rules['cards'].values())
    selected, review, rejected = [], [], []
    for card_id, definition in rules['cards'].items():
        card = cards[card_id]
        obj = _spans(definition['object'], question, active, 'object')
        work = _spans(definition['work'], question, active, 'work')
        requested_work = _spans(definition['work'], question, requests, 'work') if requests else work
        prohibition = _spans(definition['work'], question, excluded, 'excluded_work')
        refs = _spans(definition.get('reference', r'(?!)'), question, active, 'reference')
        capacity = _spans(definition.get('capacity', r'(?!)'), question, active, 'capacity')
        physical = _spans(definition.get('physical', r'(?!)'), question, active, 'outside_physical_scope')
        reasons = []
        status = 'NOT_SELECTED'
        if prohibition and not requested_work:
            status = 'EXCLUDED_BY_QUERY'
            reasons.append('이 관점의 작업은 질문에서 제외돼 있습니다.')
        elif prohibition and requested_work:
            status = 'REVIEW_NEEDED'
            reasons.append('같은 작업에 긍정과 제외 지시가 있어 대상 범위를 확인해야 합니다.')
        elif obj and work:
            if requests and not requested_work:
                reasons.append('문제의 서술은 있지만 이번에 명시적으로 요청한 작업과 일치하지 않습니다.')
            elif card_id == 'P01' and all(s['quote'].startswith('찾') for s in work) and not _spans(definition['find_context'], question, active, 'find_context'):
                status = 'REVIEW_NEEDED'
                reasons.append('문서 탐색인지 누락·오류 찾기인지 구분할 근거가 부족합니다.')
            elif card_id == 'P03' and physical:
                reasons.append('물리 제품·영상 검사 근거가 있어 문서 대조 관점으로 선택하지 않습니다.')
            elif card_id == 'P03' and not refs:
                status = 'REVIEW_NEEDED'
                reasons.append('확인 대상은 있으나 대조 기준·다른 자료의 근거가 부족합니다.')
            elif card_id == 'P04' and not capacity:
                status = 'REVIEW_NEEDED' if not outside else 'NOT_SELECTED'
                reasons.append('문의 응대와 별도로 용량·대기·시간대 문제의 근거가 필요합니다.')
            else:
                status = 'SELECTED'
                reasons.append('질문의 작업·대상' + ('·대조 기준' if card_id == 'P03' else '·응대 문제' if card_id == 'P04' else '') + '가 시범 카드의 적용 범위에 맞습니다.')
        elif obj and not any_known_work and not outside:
            status = 'REVIEW_NEEDED'
            reasons.append(definition['need'])
        elif work and not obj and not outside and not any_known_work and not (card_id == 'P04' and all(e['quote'] == '처리' for e in work)):
            status = 'REVIEW_NEEDED'
            reasons.append('작업 표현은 있으나 이 관점에 맞는 대상의 근거가 부족합니다.')
        else:
            reasons.append('이 관점을 선택할 작업·대상 근거가 함께 확인되지 않았습니다.')
        evidence = obj + work + refs + capacity + physical + prohibition
        record = {'id': card_id, 'name': card['name'], 'status': status, 'reasons': reasons, 'evidence': evidence,
                  'matched_work': definition['task_name'] if status == 'SELECTED' else None,
                  'problem_burden_explicit': bool(_spans(BURDEN, question, active, 'problem_burden')),
                  'do_not_infer_problem_burden_from_card_title': True,
                  'next_stage_conditions': list(card['query_conditions']), 'next_stage_unknowns': list(card['unknown'])}
        if status == 'SELECTED':
            support = [l for l in card['links'] if l['status'] == 'SUPPORTED_FOR_PILOT']
            if not support:
                record['status'] = 'REVIEW_NEEDED'
                record['reasons'] = ['카드에 사용 가능한 시범 근거 연결이 없습니다.']
                review.append(record)
            else:
                record['supporting_link_count'] = len(support)
                selected.append(record)
        elif status == 'REVIEW_NEEDED':
            review.append(record)
        else:
            rejected.append(record)
    if selected:
        state = 'PARTIAL_MATCH' if outside or review else 'MATCHED'
    elif review:
        state = 'REVIEW_NEEDED'
    elif outside:
        state = 'UNSUPPORTED_BY_PILOT'
    elif requests and not any_known_work:
        state = 'REVIEW_NEEDED'
    else:
        state = 'NO_SUPPORTED_MATCH'
    return {'question': question, 'selector_version': rules['version'], 'catalog_version': catalog['version'],
            'state': state, 'selected': selected, 'review_needed': review, 'not_selected': rejected,
            'outside_work': outside, 'constraints': constraints, 'clauses': clauses,
            'clarification': '요청한 작업과 대상 또는 조건을 더 구체적으로 확인해야 합니다.' if state == 'REVIEW_NEEDED' else None,
            'case_recommendations_generated': False, 'paid_calls': 0,
            'limits': 'Four-card literal-rule prototype; synthetic contract validation is not general semantic accuracy'}
