"""Documented semantic self-review of the draft; retain draft and all evidence."""
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

from scripts.build_perspective_catalog_pilot_20261109 import OUT, REGISTRY, build, validate, sha
from scripts.improvement_cycle import ROOT, read


def main():
    catalog = json.loads((OUT / 'catalog.json').read_text(encoding='utf-8'))
    cases = read(REGISTRY)['cases']
    assert catalog == build(cases)
    reviewed = deepcopy(catalog)
    link = next(l for c in reviewed['cards'] if c['id'] == 'P01' for l in c['links'] if l['case_id'] == 'AXV24_f27ca1e6fb82')
    assert link['status'] == 'SUPPORTED_FOR_PILOT'
    link['status'] = 'HOLD'
    link['reason'] = 'Task의 지식 통합 검색은 맞지만 Problem은 다수 연동 구축의 부담이다. 직원의 긴 문서 탐색 지연까지는 명시하지 않아 현재 P01의 직접 연결로 확정하지 않는다.'
    link['condition_limit'] = '시스템 간 정보 접근 문제로 범위를 넓힐지, 별도 연동 구축 부담 관점으로 나눌지 추가 근거가 필요하다. 현재 시범 연결에서는 사용하지 않는다.'
    reviewed['candidate_pool'].append({'id': 'P17', 'problem_candidate': '제품·조립 상태의 반복 육안 확인에서 검사 부담과 결함 누락 위험이 생김',
        'seed_cases': ['AXV2N_0117', 'AXV2N_0128', 'AXV2N_0135'], 'status': 'CANDIDATE_ONLY_NOT_FULLY_REVIEWED'})
    reviewed['version'] = 'case-grounded-perspective-catalog-pilot-v1-reviewed-20261109'
    reviewed['review_changes'] = [
        {'type': 'DEMOTE_TO_HOLD', 'card_id': 'P01', 'case_id': 'AXV24_f27ca1e6fb82',
         'reason': '기능의 유사성만으로 실제 문제의 동일성을 확정하지 않음'},
        {'type': 'ADD_UNREVIEWED_CANDIDATE', 'candidate_id': 'P17',
         'reason': '물리 제품의 영상 검사를 문서/등록데이터 대조 P03에 억지로 넣지 않고 별도 후보로 남김'}]
    checks = validate(reviewed, cases)
    counts = Counter(l['status'] for c in reviewed['cards'] for l in c['links'])
    unique = {l['case_id'] for c in reviewed['cards'] for l in c['links'] if l['status'] == 'SUPPORTED_FOR_PILOT'}
    assert dict(counts) == {'SUPPORTED_FOR_PILOT': 18, 'HOLD': 7, 'EXCLUDED_FROM_CARD': 6}
    assert len(unique) == 17 and checks == 93
    card_dir = OUT / 'cards'
    card_dir.mkdir(exist_ok=False)
    names = {'SUPPORTED_FOR_PILOT': '요약 근거로 시범 연결', 'HOLD': '연결 보류', 'EXCLUDED_FROM_CARD': '이번 관점에서 제외'}
    for card in reviewed['cards']:
        lines = ['# ' + card['id'] + ' — ' + card['name'], '', card['definition'], '', '## 포함 조건', '']
        lines += ['- ' + s for s in card['include_if']]
        for title, key in [('제외 조건', 'exclude_if'), ('사용자 질문에 적용할 조건', 'query_conditions'), ('아직 모르는 부분', 'unknown')]:
            lines += ['', '## ' + title, ''] + ['- ' + s for s in card[key]]
        lines += ['', '## 연결별 원문 검토', '', '아래는 저장된 요약에 대한 assistant의 내부 검토다. 새 사용자 질문의 정답 판정이나 독립 전문가 검증이 아니다.']
        for l in card['links']:
            lines += ['', '### ' + l['case_id'] + ' — ' + names[l['status']], '',
                      '**연결 판단:** ' + l['reason'], '', '**지원하는 부분:** ' + l['supported_scope'], '',
                      '**조건·확인할 경계:** ' + l['condition_limit'], '']
            for evidence in l['evidence']:
                lines += ['**' + evidence['field'] + ' 원문**', '', '> ' + evidence['quote'], '']
        with (card_dir / (card['id'] + '.ko.md')).open('x', encoding='utf-8') as target:
            target.write('\n'.join(lines).rstrip() + '\n')
    sources = [REGISTRY, 'scripts/build_perspective_catalog_pilot_20261109.py',
               'scripts/review_perspective_catalog_pilot_20261109.py', 'docs/perspective-catalog-pilot-20261109-protocol.md']
    verification = {'state': 'PASS_LITERAL_STRUCTURE_AND_DOCUMENTED_INTERNAL_REVIEW', 'candidate_count': 17, 'pilot_cards': 4,
        'reviewed_link_judgments': sum(counts.values()), 'link_status_counts': dict(counts), 'unique_supported_cases': len(unique),
        'literal_spans_checked': checks, 'pairwise_boundary_reviews': 6,
        'semantic_review_is_not_independent': True, 'recommendation_accuracy_evaluated': False,
        'source_sha256': {p: sha(ROOT / p) for p in sources}, 'draft_sha256': sha(OUT / 'catalog.json'),
        'case_cards_sha256': {p.relative_to(OUT).as_posix(): sha(p) for p in sorted(card_dir.glob('*.md'))},
        'paid_calls': 0, 'new_predictions': 0, 'all112_cases_assigned': False}
    for name, value in [('catalog-reviewed.json', reviewed), ('review-verification.json', verification)]:
        with (OUT / name).open('x', encoding='utf-8') as target:
            target.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    reread = json.loads((OUT / 'catalog-reviewed.json').read_text(encoding='utf-8'))
    assert validate(reread, cases) == 93 and reread == reviewed
    assert all(sha(ROOT / p) == h for p, h in verification['source_sha256'].items())
    print(json.dumps({k: verification[k] for k in ('candidate_count', 'pilot_cards', 'reviewed_link_judgments', 'link_status_counts', 'unique_supported_cases', 'literal_spans_checked')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
