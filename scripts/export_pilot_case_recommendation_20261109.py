"""Run local stage-five examples, save sources/vectors and replay frozen results."""
import argparse
from collections import Counter
import hashlib
import json
import zipfile

import numpy as np

from ax_research.pilot_case_recommender import recommend_cases
from scripts.pilot_case_recommendation import inputs, LocalTaskScorer, PROFILES, REGISTRY, BANKS
from scripts.pilot_perspective_selection import CATALOG, RULES
from scripts.improvement_cycle import ROOT, read
from scripts.task_alignment_20261109 import sha

OUT = ROOT / 'docs/pilot-case-recommendation-20261109-v1_2'
QUESTIONS = [
    ('policy_search', '사내 규정에서 필요한 근거와 조치 절차를 검색해주세요.'),
    ('insurance_pdf', '보험 청구서 PDF에서 가입자 정보를 추출해주세요.'),
    ('freight_check', '운송 청구서 금액을 계약 요율과 대조해주세요.'),
    ('completeness', '의뢰 자료의 필수 항목이 누락됐는지 기준과 대조해주세요.'),
    ('two_perspectives', '청구서에서 금액을 뽑고 계약 금액과 비교해주세요.'),
    ('shared_case', '의뢰 자료의 자유서술 항목을 구조화하고 필수 항목의 누락을 확인해주세요.'),
    ('night', '야간 문의가 누락돼 고객 문의에 응대하고 싶습니다.'),
    ('night_voice', '야간 음성 문의가 누락돼 고객 문의에 응대하고 싶습니다.'),
    ('voice', '고객 음성 문의가 몰려 대기가 깁니다. 문의에 응답하고 싶습니다.'),
    ('outside', '다음 달 상품 수요를 예측해주세요.'),
    ('ambiguous', '문서 처리를 잘하고 싶습니다.'),
    ('auto_modify', '청구서 금액을 계약과 대조하고 자동 수정해주세요.'),
    ('readonly', '읽기 전용으로 청구서 금액을 계약과 대조해주세요.'),
    ('separate_conditions', '보험 청구서 PDF에서 정보를 추출해주세요. 야간 문의가 누락돼 고객 문의에 응대하고 싶습니다.')
]
SOURCES = [CATALOG, RULES, PROFILES, REGISTRY,
    'src/ax_research/pilot_perspective_selector.py', 'src/ax_research/pilot_case_recommender.py',
    'scripts/pilot_case_recommendation.py', 'scripts/export_pilot_case_recommendation_20261109.py',
    'tests/test_pilot_case_recommender.py', 'docs/pilot-case-recommendation-20261109-protocol.md']


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as target:
        target.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def generate():
    if OUT.exists():
        raise FileExistsError(OUT)
    # Confirm stage-four source/catalog stability before extending it.
    prior = read('docs/perspective-selector-pilot-20261109-v1_1/freeze.json')
    assert all(sha(ROOT / p) == h for p, h in prior['source_sha256'].items())
    catalog, rules, profiles, registry = inputs()
    OUT.mkdir()
    write('freeze.json', {'version': 'pilot-case-recommender-v1.2-20261109',
        'source_sha256': {p: sha(ROOT / p) for p in SOURCES}, 'bank_sha256': {p: sha(ROOT / p) for p in BANKS},
        'model_sha256': read('docs/task-alignment-reference-20261109/config.json')['model_sha256'],
        'questions': [{'id': k, 'text': q} for k, q in QUESTIONS],
        'method': 'source-condition gate, direct/transfer candidate tier, local Task cosine, coverage-first budget',
        'new_training': False, 'paid_calls': 0, 'accuracy_evaluation': False})
    evidence = {}
    for case, interpretation in profiles['cases'].items():
        source = registry[case]
        evidence[case] = {'interpretation': interpretation, 'source_evidence': [
            {'field': f, 'quote': source[f], 'start': 0, 'end': len(source[f])} for f in ('problem', 'task', 'context')],
            'status': 'ASSISTANT_INTERPRETATION_NOT_INDEPENDENT_GOLD',
            'known_fields_meaning': 'Mentioned target/information family, not a guaranteed output schema',
            'input_conditions_meaning': 'Mentioned source input/context; not a universal implementation-performance guarantee'}
    write('case-profile-evidence.json', evidence)
    scorer = LocalTaskScorer(registry)
    # Batch new question strings only; existing case Task vectors are reused.
    from ax_research.pilot_perspective_selector import select_perspectives
    texts = []
    for _, question in QUESTIONS:
        selected = select_perspectives(question, catalog, rules)
        for card in selected['selected']:
            texts.append('\n'.join(dict.fromkeys(e['clause_quote'] for e in card['evidence'] if e['kind'] == 'work')) or question)
    texts += [registry[c]['task'] for c in profiles['cases']]
    print('LOCAL_TASK_COSINE_FOR_EXAMPLES', len(QUESTIONS), flush=True)
    scorer.warm(texts)
    results = {key: recommend_cases(q, catalog, rules, profiles, registry, scorer) for key, q in QUESTIONS}
    write('examples.json', results)
    all_texts = sorted(set(texts))
    vectors = np.array([scorer.bank[text] for text in all_texts], dtype=np.float32)
    np.savez_compressed(OUT / 'vectors.npz', texts=np.array(all_texts), vectors=vectors)
    names = {'DIRECT_WORK_TYPE_CANDIDATE': '같은 유형의 작업 후보', 'FUNCTIONAL_TRANSFER_CANDIDATE': '다른 대상·맥락의 응용 검토 후보'}
    lines = ['# 사례 추천 시범 실행 예시', '', '합성 기능검사용 질문이다. 제시된 후보는 원문 조건을 확인할 참고 사례이며 정답 확정·실무 적용 보장이 아니다.', '']
    for key, result in results.items():
        lines += ['## ' + key, '', '> ' + result['question'], '', '**상태:** ' + result['state'], '']
        if not result['recommendations']:
            lines += ['추천 사례 없음. 질문의 미지원 범위·보류 조건 또는 원문 근거가 없는 필수조건을 확인해야 한다.', '']
        for r in result['recommendations']:
            lines += ['### ' + str(r['display_order']) + '. ' + r['case_id'] + ' — ' + r['task'], '',
                '- 유형: ' + names[r['relationship']], '- 연결 관점: ' + ', '.join(r['perspective_ids'])]
            for route in r['routes']:
                lines += ['- ' + route['perspective_id'] + ' 지원 작업: ' + route['supported_work'],
                          '- 확인할 조건: ' + ' / '.join(route['conditions_to_confirm']), '',
                          '**Task 원문:**', '', '> ' + route['source']['task'], '']
        if result['condition_confirmation_queue']:
            lines += ['**필수조건 근거가 부족해 추천하지 않은 조합:**', '']
            lines += ['- ' + r['perspective_id'] + '/' + r['case_id'] + ': ' + ', '.join(r['required_input_unknown'])
                      for r in result['condition_confirmation_queue']]
            lines += ['']
    with (OUT / 'examples.ko.md').open('x', encoding='utf-8') as target:
        target.write('\n'.join(lines).rstrip() + '\n')
    with (OUT / 'question.txt').open('x', encoding='utf-8') as target:
        target.write(QUESTIONS[2][1] + '\n')
    with zipfile.ZipFile(OUT / 'source-snapshot.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in SOURCES:
            archive.write(ROOT / path, arcname=path)
    write('run.json', {'state': 'STAGE5_LOCAL_EXAMPLES_COMPLETE', 'example_count': len(results),
        'new_field_vectors': len(scorer.new_vectors), 'vectors_sha256': sha(OUT / 'vectors.npz'),
        'examples_sha256': sha(OUT / 'examples.json'), 'profile_evidence_sha256': sha(OUT / 'case-profile-evidence.json'),
        'snapshot_sha256': sha(OUT / 'source-snapshot.zip'), 'paid_calls': 0, 'new_training': False,
        'existing_qrels_read': False, 'performance_comparison_performed': False})
    print('GENERATED', {k: len(r['recommendations']) for k, r in results.items()}, flush=True)


def verify():
    load = lambda name: json.loads((OUT / name).read_text(encoding='utf-8'))
    freeze, run, examples = map(load, ('freeze.json', 'run.json', 'examples.json'))
    assert all(sha(ROOT / p) == h for p, h in freeze['source_sha256'].items())
    assert all(sha(ROOT / p) == h for p, h in freeze['bank_sha256'].items())
    for name, key in [('vectors.npz', 'vectors_sha256'), ('examples.json', 'examples_sha256'),
                      ('case-profile-evidence.json', 'profile_evidence_sha256'), ('source-snapshot.zip', 'snapshot_sha256')]:
        assert sha(OUT / name) == run[key]
    with zipfile.ZipFile(OUT / 'source-snapshot.zip') as archive:
        assert set(archive.namelist()) == set(freeze['source_sha256'])
        for path, h in freeze['source_sha256'].items():
            assert hashlib.sha256(archive.read(path)).hexdigest() == h
    with np.load(OUT / 'vectors.npz', allow_pickle=False) as archive:
        bank = dict(zip(archive['texts'].tolist(), archive['vectors']))
    catalog, rules, profiles, registry = inputs()
    def scores(perspective, query, ids):
        return {c: float(np.clip(bank[query] @ bank[registry[c]['task']], -1, 1)) for c in ids}
    for key, question in QUESTIONS:
        result = recommend_cases(question, catalog, rules, profiles, registry, scores)
        assert result == examples[key]
        assert len(result['recommendations']) <= 5 and result['unique_eligible_candidates'] <= 20
        assert len({r['case_id'] for r in result['recommendations']}) == len(result['recommendations'])
        for r in result['recommendations']:
            for route in r['routes']:
                assert any(l['case_id'] == r['case_id'] and l['status'] == 'SUPPORTED_FOR_PILOT'
                           for c in catalog['cards'] if c['id'] == route['perspective_id'] for l in c['links'])
                for e in route['source_evidence']:
                    assert registry[r['case_id']][e['field']][e['start']:e['end']] == e['quote']
                for e in route['query_evidence']:
                    assert question[e['start']:e['end']] == e['quote']
        for e in result['requirements']['evidence']:
            assert question[e['start']:e['end']] == e['quote']
        for branch_req in result['requirements_by_perspective'].values():
            for e in branch_req['evidence']:
                assert question[e['start']:e['end']] == e['quote']
    for case, record in load('case-profile-evidence.json').items():
        assert record['interpretation'] == profiles['cases'][case]
        for e in record['source_evidence']:
            assert registry[case][e['field']][e['start']:e['end']] == e['quote']
    result = {'state': 'PASS_SOURCE_VECTOR_AND_EXAMPLE_REPLAY', 'examples_reproduced': len(examples),
        'profile_sources_checked': len(profiles['cases']), 'eligible_supported_links_only': True,
        'query_and_case_literal_evidence_checked': True, 'budgets_deduplication_and_provenance_checked': True,
        'no_case_for_night_voice': not bool(examples['night_voice']['recommendations']),
        'source_metadata_independently_validated': False, 'paid_calls': 0, 'new_training': False,
        'performance_comparison_performed': False}
    path = OUT / 'verification.json'
    if path.exists():
        assert load('verification.json') == result
    else:
        write('verification.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['generate', 'verify'])
    globals()[parser.parse_args().phase]()
