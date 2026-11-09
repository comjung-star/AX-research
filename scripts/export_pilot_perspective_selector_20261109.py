"""Save/replay the four-card selector's functional evidence; no case recommendation."""
import argparse
from collections import Counter
import hashlib
import json
import zipfile

from scripts.improvement_cycle import ROOT, read
from scripts.pilot_perspective_selection import CATALOG, RULES, CONTRACTS, check_contracts, select

OUT = ROOT / 'docs/perspective-selector-pilot-20261109-v1_1'
SOURCES = [CATALOG, RULES, CONTRACTS, 'src/ax_research/pilot_perspective_selector.py',
           'scripts/pilot_perspective_selection.py', 'scripts/export_pilot_perspective_selector_20261109.py',
           'tests/test_pilot_perspective_selector.py', 'docs/perspective-selector-pilot-20261109-protocol.md']
EXAMPLES = ['extract_and_compare', 'search_please', 'service_night', 'forecast_outside', 'vague_document_work',
            'missing_reference', 'forbid_extract', 'partial_write', 'historical_not_current', 'same_industry_not_same_work',
            'human_approval_preserved']
STATES = {'MATCHED': '선택 근거 확인', 'PARTIAL_MATCH': '일부만 지원', 'REVIEW_NEEDED': '판단 보류',
          'UNSUPPORTED_BY_PILOT': '네 시범 관점의 지원 범위 밖', 'NO_SUPPORTED_MATCH': '지원 근거 미확인'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as target:
        target.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def export():
    if OUT.exists():
        raise FileExistsError(OUT)
    report = check_contracts()
    assert report['passed']
    OUT.mkdir()
    write('functional-checks.json', report)
    lookup = {r['id']: r for r in report['rows']}
    examples = {key: lookup[key]['result'] for key in EXAMPLES}
    write('examples.json', examples)
    lines = ['# 관점 선택기 실행 예시', '', '기능 검사용 합성 질문의 실제 출력이다. 실제 사용자 평가나 추천 정확도는 아니다. 사례 추천은 생성하지 않는다.', '']
    for key, result in examples.items():
        lines += ['## ' + key, '', '> ' + result['question'], '', '**판정:** ' + STATES[result['state']], '',
                  '**선택:** ' + (', '.join(r['id'] + ' ' + r['name'] for r in result['selected']) or '없음'), '']
        for chosen in result['selected']:
            clauses = list(dict.fromkeys(e['clause_quote'] for e in chosen['evidence'] if e['kind'] in ('work', 'object', 'reference', 'capacity')))
            lines += ['- ' + chosen['id'] + ' 원문 근거: ' + ' / '.join(clauses)]
        for pending in result['review_needed']:
            lines += ['- 보류 ' + pending['id'] + ': ' + ' '.join(pending['reasons'])]
        for unsupported in result['outside_work']:
            lines += ['- 미지원 요구: ' + unsupported['reason']]
        if result['constraints']:
            lines += ['- 보존한 제약: ' + ' / '.join(dict.fromkeys(r['quote'] for r in result['constraints']))]
        lines += ['']
    with (OUT / 'examples.ko.md').open('x', encoding='utf-8') as target:
        target.write('\n'.join(lines).rstrip() + '\n')
    with (OUT / 'question.txt').open('x', encoding='utf-8') as target:
        target.write('청구서에서 금액을 뽑고, 계약 금액과 다른 항목을 찾아주세요.\n')
    snapshot = OUT / 'source-snapshot.zip'
    with zipfile.ZipFile(snapshot, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in SOURCES:
            archive.write(ROOT / path, arcname=path)
    write('freeze.json', {'version': read(RULES)['version'], 'catalog_version': read(CATALOG)['version'],
        'source_sha256': {p: sha(ROOT / p) for p in SOURCES}, 'snapshot_sha256': sha(snapshot),
        'functional_checks_sha256': sha(OUT / 'functional-checks.json'), 'examples_sha256': sha(OUT / 'examples.json'),
        'case_recommendation_stage_implemented': False, 'paid_calls': 0, 'synthetic_development_cases': report['cases'],
        'paraphrase_groups': report['paraphrase_groups'], 'independent_accuracy_validation': False,
        'revision_note': 'Suppress work-only warnings without an object when another card already has explicit work-and-object support; enforce MATCHED for fully covered positive contracts. Earlier draft snapshot retained separately.'})
    print('EXPORTED', report['cases'], 'contracts,', len(examples), 'examples')


def verify():
    load = lambda name: json.loads((OUT / name).read_text(encoding='utf-8'))
    freeze, checks, examples = map(load, ('freeze.json', 'functional-checks.json', 'examples.json'))
    assert all(sha(ROOT / path) == h for path, h in freeze['source_sha256'].items())
    assert sha(OUT / 'source-snapshot.zip') == freeze['snapshot_sha256']
    assert sha(OUT / 'functional-checks.json') == freeze['functional_checks_sha256']
    assert sha(OUT / 'examples.json') == freeze['examples_sha256']
    with zipfile.ZipFile(OUT / 'source-snapshot.zip') as archive:
        assert set(archive.namelist()) == set(freeze['source_sha256'])
        for path, h in freeze['source_sha256'].items():
            assert hashlib.sha256(archive.read(path)).hexdigest() == h
    assert checks == check_contracts() and checks['passed']
    for result in examples.values():
        assert select(result['question']) == result
        assert not result['case_recommendations_generated'] and result['paid_calls'] == 0
    counts = Counter(r['result']['state'] for r in checks['rows'])
    result = {'state': 'PASS_SOURCE_AND_FUNCTIONAL_REPLAY', 'contract_cases_reproduced': checks['cases'],
              'paraphrase_groups': checks['paraphrase_groups'], 'paraphrase_selection_stable': checks['paraphrase_selection_stable'],
              'examples_reproduced': len(examples), 'state_counts': dict(counts), 'all_evidence_spans_literal': True,
              'case_recommendations_generated': False, 'paid_calls': 0, 'independent_semantic_accuracy_claim': False,
              'catalog_sha256': sha(ROOT / CATALOG)}
    path = OUT / 'verification.json'
    if path.exists():
        assert load('verification.json') == result
    else:
        write('verification.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['export', 'verify'])
    globals()[parser.parse_args().phase]()
