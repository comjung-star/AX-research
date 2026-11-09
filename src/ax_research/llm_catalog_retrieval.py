"""Connect literal LLM perspective evidence to the unchanged pilot retrieval core."""
import copy
import re
from types import FunctionType

from ax_research.pilot_perspective_selector import scope_clauses
from ax_research.pilot_case_recommender import recommend_cases


def adapt_selection(question, normalized, catalog):
    if normalized['question'] != question:
        raise ValueError('LLM 선택과 검색 질문이 다릅니다.')
    cards = {c['id']: c for c in catalog['cards']}
    if {d['id'] for d in normalized['decisions']} != set(cards):
        raise ValueError('LLM 관점과 검토된 목록이 다릅니다.')
    clauses = scope_clauses(question)
    constraints = [c for c in clauses if c['role'] in ('excluded', 'human_approval')]
    selected, pending, rejected, problems = [], [], [], []
    kind_map = {'WORK': 'work', 'OBJECT': 'object', 'REFERENCE': 'reference', 'CAPACITY': 'capacity', 'EXCLUSION': 'excluded_work'}
    for decision in normalized['decisions']:
        evidence = []
        conflicts = []
        for e in decision['evidence']:
            if question[e['start']:e['end']] != e['quote']:
                raise ValueError('LLM 근거의 문자 위치가 바뀌었습니다.')
            for clause in clauses:
                start, end = max(e['start'], clause['start']), min(e['end'], clause['end'])
                if start >= end:
                    continue
                evidence.append({'kind': kind_map[e['kind']], 'quote': question[start:end], 'start': start, 'end': end,
                    'clause_start': clause['start'], 'clause_end': clause['end'], 'clause_quote': clause['quote'], 'clause_role': clause['role']})
                if e['kind'] == 'WORK' and clause['role'] in ('excluded', 'historical', 'human_approval'):
                    conflicts.append('LLM 작업 근거가 기존 문장 구분에서 제외·과거·승인 조건으로 분류됨')
        if decision['status'] == 'SELECTED' and not any(e['kind'] == 'work' for e in evidence):
            conflicts.append('작업 근거를 기존 검색 문장에 연결하지 못함')
        record = {'id': decision['id'], 'name': cards[decision['id']]['name'],
            'status': decision['status'], 'reasons': [decision['rationale']], 'evidence': evidence,
            'matched_work': decision['rationale'] if decision['status'] == 'SELECTED' else None,
            'missing_information': decision['missing_information'],
            'next_stage_conditions': cards[decision['id']]['query_conditions'], 'next_stage_unknowns': cards[decision['id']]['unknown']}
        if conflicts and decision['status'] == 'SELECTED':
            record['status'] = 'REVIEW_NEEDED'
            record['reasons'] += sorted(set(conflicts))
            problems.append({'id': decision['id'], 'reasons': sorted(set(conflicts))})
            pending.append(record)
        elif decision['status'] == 'SELECTED':
            selected.append(record)
        elif decision['status'] == 'PENDING':
            record['status'] = 'REVIEW_NEEDED'
            pending.append(record)
        else:
            rejected.append(record)
    # The existing downstream core scopes requirements by clauses. It cannot safely
    # distinguish unrelated PDF extraction and night service inside a shared clause.
    # Keep those ambiguous branches pending rather than spreading both conditions.
    if any(s['id'] == 'P04' for s in selected) and any(s['id'] != 'P04' for s in selected):
        work_ranges = {s['id']: {(e['clause_start'], e['clause_end']) for e in s['evidence'] if e['kind'] == 'work'} for s in selected}
        ambiguous = set()
        for other in selected:
            if other['id'] == 'P04':
                continue
            shared = work_ranges['P04'] & work_ranges[other['id']]
            for start, end in shared:
                text = question[start:end]
                if re.search(r'PDF|피디에프|문서|청구서|서류', text, re.I) and re.search(r'야간|주말|음성|문의|상담', text):
                    ambiguous.update(('P04', other['id']))
        if ambiguous:
            remain = []
            for s in selected:
                if s['id'] in ambiguous:
                    s['status'] = 'REVIEW_NEEDED'
                    s['reasons'].append('같은 절의 서로 다른 작업에 입력·시간 조건이 섞여 적용 범위 확인 필요')
                    pending.append(s)
                    problems.append({'id': s['id'], 'reasons': [s['reasons'][-1]]})
                else:
                    remain.append(s)
            selected = remain
    outside = [{'id': 'llm_outside_' + str(i), 'reason': r['reason'],
        'evidence': [{'kind': 'outside_work', 'quote': r['quote'], 'start': r['start'], 'end': r['end']}]}
        for i, r in enumerate(normalized['unsupported_work'])]
    state = ('PARTIAL_MATCH' if outside or pending else 'MATCHED') if selected else ('REVIEW_NEEDED' if pending else 'UNSUPPORTED_BY_PILOT' if outside else 'NO_SUPPORTED_MATCH')
    return {'question': question, 'selector_version': normalized['version'], 'catalog_version': catalog['version'],
        'state': state, 'selected': selected, 'review_needed': pending, 'not_selected': rejected,
        'outside_work': outside, 'clauses': clauses, 'constraints': constraints,
        'llm_constraints_for_audit': normalized['constraints'], 'adapter_review_required': problems,
        'case_recommendations_generated': False,
        'limits': 'LLM selection/evidence mapped into unchanged clause-level condition parser; ambiguous mappings stay pending'}


def recommend_from_selection(question, selection, catalog, rules, profiles, registry, scorer, *, max_results=5):
    """Same core bytecode and helpers; selector dependency supplied without global mutation."""
    if question != selection['question']:
        raise ValueError('선택 결과가 다른 질문에 속합니다.')
    namespace = {**recommend_cases.__globals__,
                 'select_perspectives': lambda q, c, r: copy.deepcopy(selection)}
    core = FunctionType(recommend_cases.__code__, namespace, recommend_cases.__name__, recommend_cases.__defaults__, recommend_cases.__closure__)
    core.__kwdefaults__ = recommend_cases.__kwdefaults__
    return core(question, catalog, rules, profiles, registry, scorer, max_results=max_results)


def recommend_llm(question, normalized, catalog, rules, profiles, registry, scorer, *, max_results=5):
    return recommend_from_selection(question, adapt_selection(question, normalized, catalog), catalog, rules, profiles, registry, scorer, max_results=max_results)
