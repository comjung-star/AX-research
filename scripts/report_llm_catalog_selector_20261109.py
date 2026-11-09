"""Post-run Korean artifacts; no LLM requests, retrieval, tuning, or label changes."""
from collections import Counter
import json

from scripts.llm_catalog_selector_20261109 import OUT, CONFIG, load, frozen
from scripts.improvement_cycle import read
from scripts.task_alignment_20261109 import sha


def main():
    frozen()
    config = read(CONFIG)
    rows = load('questions-and-development-expectations.json')['rows']
    selected = load('normalized-selections.json')
    review, run = load('development-review.json'), load('run.json')
    names = {c['id']: c['short_name'] for c in config['cards']}
    unique = [r for r in rows if r['kind'] != 'ORDER_DIAGNOSTIC_REPEAT']
    counts = review['counts']
    lines = ['# LLM 관점 선택 1~3단계 결과', '',
        '**관점 설명 준비, 실제 LLM 선택 구현, 개발 확인 후 지시문 고정까지 완료했다.** 개발20개와 이전에 관찰한 회귀4개는 사전에 정한 선택·보류·범위 밖 기준을 충족했다. 관점 순서를 바꾼4개 재실행도 같은 관점을 선택했다. 이 결과는 개발 기준 통과이며 일반 정확도100%나 사례 검색 성능 개선을 뜻하지 않는다.', '',
        '## 무엇을 만들었는가', '',
        '미리 정리한4개 관점의 뜻·포함/제외 기준·필요 정보와 사용자 질문을 Claude Sonnet5.5에 함께 제공한다. LLM이 각 관점을 선택/정보 부족으로 보류/미선택으로 판단하고, 선택 이유와 질문의 근거 문장을 반환한다. 새 관점을 생성하거나 사례를 추천하지 않는다. 모델을 추가 학습시키지 않았다.', '',
        '기존 관점-사례 연결은 바꾸지 않았다. 원래 카드의 사례 연결 기준과 질문 선택 기준은 별도다. 예를 들어 사례를 연결할 때는 실제 수행 기능을 원문에서 확인하고, 질문에서는 사용자가 그 기능을 필요로 하는지 판단한다. 관점을 선택했다는 사실이 연결된 사례의 세부 조건 충족을 보장하지 않는다.', '',
        '4개는 시범 목록이며 전체 데이터셋의 관점을4개로 확정한 것이 아니다. 기존17개 관점 후보 중 먼저 검토한4개만 사용했다.', '',
        '| 관점 | 질문에서 확인하는 것 |', '|---|---|']
    for c in config['cards']:
        lines.append(f"| {c['id']} {c['short_name']} | {' / '.join(c['need'])} |")
    lines += ['', '## 실제 실행과 개발 확인', '',
        '| 항목 | 결과 | 의미 |', '|---|---:|---|',
        f"| 합성 개발 질문 | {counts['SYNTHETIC_DEVELOPMENT']['development_contract_passed']}/20 기준 충족 | assistant가 미리 작성한 개발 기준 |",
        f"| 이전 회귀 질문 | {counts['PREVIOUSLY_SEEN_REGRESSION']['development_contract_passed']}/4 기준 충족 | 이미 살펴본 실패·모호 사례, 새 시험 아님 |",
        '| 관점 순서 반전 재실행 | 4/4 선택 동일 | 동일 질문4개 반복, 독립 표본 아님 |',
        '| 구조·근거 인용 검사 | 28/28 통과 | 유효 관점ID와 인용의 원문 문자 일치 |',
        '| 구현 관련 검사 | 40개 통과 | 잘못된 인용·중복ID·잘린 응답 등 처리 확인 |', '',
        '합성 질문에는 같은 작업의 다른 표현, 2~3개 관점 동시 요청, 범위 밖 요약·예측, 정보 부족, 과거 작업, 명시 금지, 담당자 승인 조건을 포함했다. 모든 기대 집합과 모호한 질문의 허용 범위는 API 호출 전에 고정했다. 기대 집합·사례ID·검색 정답·검색 점수는 모델에 보내지 않았다.', '',
        '로컬 코드는 선택 의미를 규칙으로 덮어쓰지 않는다. 관점ID와 결정 구조, 질문에 실제 있는 인용, 선택별 근거 종류를 검사한다. 근거 문자가 일치해도 그 해석이 옳다는 독립 증명은 아니다. 반복 질문을 포함한28회를28개 독립 시험으로 세지 않는다.', '',
        '## 이전 질문에서 달라진 선택', '',
        '| 질문 | 이번 선택 | 해석 |', '|---|---|---|']
    for q, note in [
        ('R_IVQ010', '상품 정보 파일의 표준 항목 정리와 누락 확인을 각각 포착했다. 표준 항목이 대조 기준으로 충분한지는 모호할 수 있어 사전 기준에서 P03 선택 또는 보류를 허용했다.'),
        ('R_IVQ020', '은행 입금 내역과 매출 장부를 대조하는 요청을 포착했다.'),
        ('R_IVQ029', '지원서라는 표현도 업무 자료로 이해해 직무 기준 대조를 포착했다. 연결 사례가 그 직무 기준을 실제 지원하는지는 별도다.'),
        ('R_IVQ015', '정책에 비춘 안내 오류 대조를 하위 작업으로 골랐고 교육 자료 개선안 작성은 목록 밖으로 남겼다. 질문 전체를 해결했다고 판단하지 않았다.')]:
        r = selected.get(q)
        lines.append(f"| {q.replace('R_', '')} | {', '.join(r['selected_ids']) if r else '응답 검증 실패'} | {note} |")
    lines += ['', '회귀4개는 이전 규칙 방식에서 비거나 부적절하게 선택했던 질문이다. 이번 관점 선택이 개발 기준을 충족해도 그 질문의 최종 추천 F1이 개선됐다는 뜻은 아니다. 관점 분기가 달라지면서 어떤 사례가 새로 들어오거나 빠지는지 아직 비교하지 않았다.', '',
        '## 출력을 검토한 범위와 남은 한계', '',
        '같은 assistant가 고유24개 출력의 선택 이유와 인용을 읽고 개발 기준과 함께 검토했다. 독립 사람 평가나 별도 AI의 의미 채점은 수행하지 않았다. 관점 설명과 기대 집합을 작성한 주체가 검토도 했으므로 편향 가능성이 있다.', '',
        '- 여러 관점 요청에서는 각각 요청된 작업의 근거를 남겼다. 단순 대조 요청에 추출을 전제로 덧붙이지 않았다.',
        '- ‘문서 처리를 잘하고 싶다’는 작업을 정하지 않고 보류했다. 비교 기준 없는 청구서 검증과 용량 문제 없는 문의 응대도 보류했다.',
        '- 과거의 문서 검색을 현재의 수요 예측 요청에 적용하지 않았다. 상담량 문제라는 배경만으로 요약 요청에 P04를 붙이지 않았다.',
        '- 금지된 추출과 담당자 승인 조건을 질문 원문 그대로 남겼다.',
        '- IVQ010과 IVQ015는 여러 합리적인 해석이 가능한 회귀 사례다. 단 하나의 관점 조합이 정답이라고 인증하지 않는다.',
        '- 순서 반전 확인은 단순 질문4개에서 한 번씩만 했다. 긴 복합 질문·오타·새 업종·프롬프트 공격·대규모 관점 목록에 대한 강건성은 입증하지 않았다.', '',
        'P03에서 대상·기준이 있다는 사실은 사례가 모든 판단을 수행한다는 뜻이 아니다. 예컨대 지원서-증빙 대조 사례가 채용 적합성 판단까지 지원한다고 확대하면 안 된다. 야간·음성·권한 조건도 이후 사례별 원문 대조가 필요하다.', '',
        '## 비용과 고정 상태', '',
        f"실제 Messages 호출28회, 사용량 기준 추정 비용 **${run['estimated_received_usage_usd']:.5f}**다. 사전 예약 상한은 **${run['reserved_upper_usd']:.6f}**, 작업 예산은$3이었다. Models API 가용성 확인은 별도1회이며 Messages28회에 섞지 않았다. 재시도·응답 교체·추가 학습·결과를 본 뒤 프롬프트 수정은0회다.", '',
        '모델은 `claude-sonnet-5-5`, effort `high`, 출력 상한4096 tokens다. 출력 사용량에는 모델이 보고한 생각 토큰 비용이 포함된다. 비용은 저장된 usage와 공식 단가로 계산한 추정치이며 청구서 확정액은 아니다. [공식 모델·요금](https://platform.claude.com/docs/en/models/sonnet-5-5/overview), [구조화 출력 명세](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)를 확인했다.', '',
        'API 호출 전 초기 동결과 개발 확인 후 최종 동결을 모두 남겼다. 처음 작성한 프롬프트를 그대로 실험본으로 고정했다. 기존 규칙 선택기·사례 추천기·연결 목록은 변경하지 않았고 봉인 Test15도 열지 않았다. 자료는 로컬 작업사본에 저장했으며 GitHub에 커밋·업로드하지 않았다.', '',
        '## 다음 단계와 이번 종료 범위', '',
        '**현재 상태는 ‘4단계 개발 비교에 사용할 수 있는 선택 실험본 준비’다.** 아직 최종 추천 성능 향상이나 독립 검증 완료 상태가 아니다. 다음 단계에서는 LLM 선택 근거를 관점별 검색 입력에 연결하고, 동일 사례·예산·후속 조건 확인으로 기존 검색/규칙 선택/LLM 선택의 최종 결과를 비교해야 한다. 연결 변환 자체의 오류도 먼저 확인해야 한다.', '',
        '이번 요청인1~3단계는 여기서 종료했다. 전체60개 추천 비교, 정답 재채점, 전체112 확장, 모델 추가 학습은 진행하지 않았다.', '',
        '## 확인 자료', '',
        '- [LLM에 제공하는 관점 설명](perspectives.ko.md)',
        '- [24개 질문과4개 순서 반복의 실제 선택·이유·인용](examples.ko.md)',
        '- [사전 계획](../llm-catalog-selector-20261109-protocol.md)',
        '- [사전에 정한 질문·개발 기대 집합](questions-and-development-expectations.json)',
        '- [실제 전송 본문: 키·정답 제외](requests.json)',
        '- [개발 확인 결과](development-review.json) / [정규화된 관점 선택](normalized-selections.json)',
        '- [실행과 비용](run.json) / [예약 상한](reservation.json)',
        '- [최초 동결](freeze.json) / [최종 동결](final-freeze.json) / [응답 재파싱 재현](verification.json)',
        '- [소스 원본 묶음](source-snapshot.zip)', '']
    (OUT / 'README.ko.md').write_text('\n'.join(lines), encoding='utf-8')
    cards = ['# LLM에게 주는 4개 시범 관점', '', '모델 추가 학습 없이 질문과 함께 제공하는 참고 목록이다. 기존 사례 연결은 그대로 보존한다.', '']
    for c in config['cards']:
        cards += ['## ' + c['id'] + ' ' + c['short_name'], '', c['select_when'], '',
            '**필요 정보:** ' + ' / '.join(c['need']), '', '**포함:**', ''] + ['- ' + v for v in c['include']]
        cards += ['', '**제외:**', ''] + ['- ' + v for v in c['exclude']]
        cards += ['', '**적용 한계:**', ''] + ['- ' + v for v in c['limits']] + ['']
    (OUT / 'perspectives.ko.md').write_text('\n'.join(cards), encoding='utf-8')
    examples = ['# 실제 Claude 관점 선택 결과', '', '고유24개 개발 질문과4개 순서 반복이다. 일반 정확도나 사례 검색 성능 결과가 아니다.', '']
    display_status = {'SELECTED': '선택', 'PENDING': '보류', 'NOT_SELECTED': '미선택'}
    for row in rows:
        q = row['id']
        r = selected.get(q)
        examples += ['## ' + q, '', '> ' + row['question'], '', '- 자료 구분: ' + row['kind']]
        if row.get('ambiguity'):
            examples += ['- 사전 기록한 모호함: ' + row['ambiguity']]
        if r is None:
            examples += ['', '응답 검증 실패. 호출 원본과 실패 기록을 보존했다.', '']
            continue
        examples += ['- 상태: ' + r['state'], '- 선택: ' + (', '.join(r['selected_ids']) or '없음'),
            '- 보류: ' + (', '.join(r['pending_ids']) or '없음'), '']
        for d in r['decisions']:
            examples += ['### ' + d['id'] + ' ' + names[d['id']] + ': ' + display_status[d['status']], '', d['rationale'], '']
            examples += ['- ' + e['kind'] + ': “' + e['quote'] + '”' for e in d['evidence']]
            if d['missing_information']:
                examples += ['- 확인할 정보: ' + ' / '.join(d['missing_information'])]
            examples += ['']
        if r['unsupported_work']:
            examples += ['**목록 밖 요청:**', ''] + ['- “' + v['quote'] + '”: ' + v['reason'] for v in r['unsupported_work']] + ['']
        if r['constraints']:
            examples += ['**보존한 조건:**', ''] + ['- ' + v['kind'] + ': “' + v['quote'] + '”' for v in r['constraints']] + ['']
    (OUT / 'examples.ko.md').write_text('\n'.join(examples), encoding='utf-8')
    models = Counter()
    input_tokens = output_tokens = 0
    for row in rows:
        path = OUT / 'calls' / (row['id'] + '-receipt.json')
        if path.exists():
            receipt = json.loads(path.read_text(encoding='utf-8'))
            models[receipt['returned_model']] += 1
            input_tokens += receipt['usage'].get('input_tokens', 0)
            output_tokens += receipt['usage'].get('output_tokens', 0)
    notes = {'reviewer': 'same assistant that authored cards and development expectations; not independent',
        'unique_outputs_read': len(unique), 'prespecified_development_criteria_met': True,
        'ambiguous_regressions_retained': ['R_IVQ010', 'R_IVQ015'],
        'retrieval_performance_not_assessed': True, 'returned_models': dict(models),
        'input_tokens': input_tokens, 'output_tokens': output_tokens,
        'next_step': 'Test evidence-to-retrieval adapter and compare fixed final retrieval; not performed now'}
    (OUT / 'manual-review-notes.json').write_text(json.dumps(notes, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    provenance = {'report_is_post_run_interpretation': True, 'source_report_script_sha256': sha(__file__),
        'final_freeze_sha256': sha(OUT / 'final-freeze.json'),
        'artifact_sha256': {p: sha(OUT / p) for p in ['README.ko.md', 'perspectives.ko.md', 'examples.ko.md', 'manual-review-notes.json']},
        'extra_paid_calls': 0, 'prompt_changed': False}
    (OUT / 'report-provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'state': 'STEPS_1_TO_3_REPORTED', 'returned_models': dict(models),
        'unique_development_questions': len(unique), 'estimated_usage_usd': run['estimated_received_usage_usd']}))


if __name__ == '__main__':
    main()
