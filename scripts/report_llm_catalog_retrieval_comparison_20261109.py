"""Post-run explanation and error accounting; no API, inference, or method changes."""
from collections import Counter
import json

from scripts.llm_catalog_retrieval_comparison_20261109 import OUT, load, frozen, inputs, SYSTEMS, REGRESSION_IDS
from scripts.task_alignment_20261109 import sha


def main():
    frozen()
    x, raw = load('evaluation.json'), load('predictions.json')
    p, questions, details = raw['questions'], load('questions.json'), load('query-case-evidence.json')
    catalog, rules, profiles, registry = inputs()
    names = {'original': '개발20 원본', 'working_transfer': '개발20 작업용', 'partial_review_464': '개발20 부분 재검토',
        'claude': '재사용40 Claude', 'gemini': '재사용40 Gemini'}
    system_names = {'A_Dense17': 'A 기존 Dense 검색', 'B_Task17': 'B 업무 중심 검색',
        'C_Catalog17': 'C 규칙 관점 선택', 'E_LLMCatalog17': 'E LLM 관점 선택'}
    pct = lambda v: 'NA' if v is None else f'{100*v:.1f}'
    accounting = {}
    for label, group in x['failure_accounting'].items():
        counts = {'no_llm_view': 0, 'adapter_pending': 0, 'unlinked_to_selected_view': 0,
            'condition_deferred': 0, 'final5_drop': 0, 'hits': 0}
        rows = {}
        for q, row in group.items():
            pos = set(row['positive_inside17'])
            candidates = set(p[q]['systems']['E_LLMCatalog17']['candidates'])
            final = set(p[q]['systems']['E_LLMCatalog17']['ranking'])
            reasons = {k: [] for k in counts}
            if not p[q]['llm_selected']:
                reasons['no_llm_view'] = sorted(pos)
            elif not p[q]['adapted_selected']:
                reasons['adapter_pending'] = sorted(pos)
            else:
                linked = {link['case_id'] for c in catalog['cards'] if c['id'] in p[q]['adapted_selected']
                    for link in c['links'] if link['status'] == 'SUPPORTED_FOR_PILOT'}
                reasons['unlinked_to_selected_view'] = sorted(pos-linked)
                reasons['condition_deferred'] = sorted((pos&linked)-candidates)
                reasons['final5_drop'] = sorted((pos&candidates)-final)
            reasons['hits'] = sorted(pos&final)
            assert sum(map(len, reasons.values())) == len(pos)
            rows[q] = reasons
            for key in counts:
                counts[key] += len(reasons[key])
        accounting[label] = {'counts': counts, 'per_query': rows}
    p03 = {q: sorted(r['systems']['E_LLMCatalog17']['ranking']) for q, r in p.items() if r['adapted_selected'] == ['P03']}
    assert len(p03) == 16 and len({tuple(v) for v in p03.values()}) == 1
    lines = ['# LLM 관점 선택을 실제 사례 검색에 연결한 결과', '',
        '**요청한1~4단계를 완료했다. LLM 선택은 이전 규칙 방식보다 점수가 높았지만, 단순 검색보다 일관되게 좋지는 않았다. 현재 방식의 전체 성능 개선을 확정하거나 전체112 확장으로 바로 넘어갈 근거는 부족하다.**', '',
        '좋아진 부분은 실제로 있다. 개발20개에서 세 채점표 모두 F1이 높아졌고,40개에서도 규칙 방식이 놓친 일부 사례를 회수했다. 다만40개에서는 보조 기준선인 업무 중심 검색이 여전히 더 높았고, Gemini 판정에서는 기존 Dense도 더 높았다. 이전에 살펴본4개 질문에서 얻은 이득이 크게 포함돼 새 질문에 일반화됐다고 할 수 없다.', '',
        '## 수행 범위와 같은 조건', '',
        '- 기존4개 시범 관점·18승인연결·17고유사례만 사용했다. 전체112개로 확장하지 않았다.',
        '- 질문은 앞선 개발20개와 재사용40개를 모두 유지했다. 이미 관찰한 자료이며 독립 최종 시험이 아니다.',
        '- 관점 선택 설명·모델·프롬프트를 바꾸지 않았다. 기존4개 LLM 응답은 동일 요청 본문을 확인해 재사용했고56개만 새로 호출했다.',
        '- A 단일 Dense, B 질문 전체−사례Task 유사도, C 규칙 선택, E LLM 선택을 같은 후보 상한20·출력 상한5로 비교했다.',
        '- 기존 A/B/C 순위와 C의 전체 근거 결과60개를 정확히 재현했다. E에서도 후속 조건 확인·직접/응용 구분·Task cosine·관점별 배정의 코드 본문은 그대로 썼다.',
        '- 어댑터가 LLM의 관점ID와 질문 인용을 기존 검색 형식으로 연결한다. LLM이 새 검색문을 쓰거나 사례 점수를 채점하지 않는다. 선택ID와 근거 표현을 함께 교체한 실험이다.',
        '- 관련 검사50개를 통과한 뒤 정책과 소스를 동결했다. 순위 저장 후 기존 채점표를 읽었고 결과를 본 뒤 규칙·가중치·정답을 수정하지 않았다.', '',
        '## 주요 점수', '',
        'F1@5×100이며 높을수록 좋다. 정답이 있는 질문에서 관련 사례 적중과 누락을 함께 평가한다. 정답이 있는데 빈 답을 내면0점이다. 정답이 없는 질문은 F1 평균에서 제외하되 출력 수·불필요 출력·빈칸 포함 P@5에는 반영했다. 아래 양성 질문 수는17개 안에 기존 채점표의 정답이 하나 이상 있는 질문 수다.', '',
        '| 채점표 | 양성 질문 | A 기존 검색 | B 업무 중심 | C 규칙 관점 | E LLM 관점 |',
        '|---|---:|---:|---:|---:|---:|']
    for name, r in x['results_inside17'].items():
        lines.append('| ' + names[name] + ' | ' + str(r['positive_questions']) + ' | ' + ' | '.join(pct(r['summary'][s]['F1@5']['mean']) for s in SYSTEMS) + ' |')
    lines += ['', '개발20개의 F1은 양성7개 질문에서 계산했다. 원본89양성쌍, 작업용54양성쌍, 부분 재검토53양성쌍은 서로 다른 표이며 하나로 합치지 않았다. 부분 재검토는464쌍만 검토한 표를 기존 작업용 표에 적용한 것이지 전체 Gold 인증이 아니다.', '',
        '40개에서도 C보다 E가 높다. 하지만 E−C의95% 질문 bootstrap 구간은 Claude +0.0556~+0.5833, Gemini +0.0417~+0.3385이고, 보수적8비교 보정 구간의 하한은 둘 다0이다. E−B는 Claude −0.0811, Gemini −0.1664이며 E의 우위를 뒷받침하지 않는다. Gemini E−B의95%구간은 −0.3278~−0.0147이나 보정 구간은0을 포함한다. 선택 편향이 있는 작은 개발 자료의 기술통계로 해석한다.', '',
        'nDCG@5도40개에서 C→E는 Claude0.1462→0.5051, Gemini0.2065→0.4330으로 올랐다. B는 각각0.6130·0.6902로 E보다 높았다. F1과 순서 지표 모두 단순 업무 중심 검색의 안정적 우위를 넘지 못했다.', '',
        '## 이전4개 질문을 빼도 좋아졌는가', '',
        'IVQ010/015/020/029는 관점 선택 개발에 이미 썼다. 그4개 응답을 재사용했으므로 이득을 독립 개선이라고 부르면 안 된다. 나머지36개도 과거 연구에서 본 질문이지만 별도로 나눠 계산했다.', '',
        '| 채점표·질문 범위 | 양성 질문 | B 업무 중심 F1 | C 규칙 F1 | E LLM F1 |', '|---|---:|---:|---:|---:|']
    for provider, groups in x['selector_development_subgroups'].items():
        for group, r in groups.items():
            title = '이전 개발4개' if group == 'previous_selector_development4' else '나머지36개'
            lines.append(f"| {provider} {title} | {r['positive_questions']} | " + ' | '.join(pct(r['summary'][s]['F1@5']['mean']) for s in ('B_Task17','C_Catalog17','E_LLMCatalog17')) + ' |')
    lines += ['', 'Claude의 나머지36개에서는 C와 E의 F1이 같았다. Gemini에서는 조금 높아졌지만 B보다 낮았다. **현재 이득은 알려진 일부 실패 회복의 성격이 강하며 폭넓은 일반화 증거가 아니다.**', '',
        '두 공급자가 모두17개 안에 양성이 있다고 본 동일6개 질문에서도 B→E는 Claude49.5→41.4, Gemini61.0→57.1이다. 이진 양성 교집합·합집합 민감도 계산도 B를 넘지 못했다. 양성 교집합·합집합을 새 타협 정답으로 채택하지 않았다.', '',
        '## 실제로 더 찾은 사례와 빈 답', '',
        '| 채점표 | C 출력·정답 적중 수 | E 출력·정답 적중 수 | B 출력·정답 적중 수 | C→E 양성인데 빈 답인 질문 |',
        '|---|---:|---:|---:|---:|']
    for name in ('working_transfer', 'claude', 'gemini'):
        z = x['results_inside17'][name]['summary']
        c, e, b = [z[s]['output'] for s in ('C_Catalog17','E_LLMCatalog17','B_Task17')]
        lines.append(f"| {names[name]} | {c['emitted']}·{c['hits']} | {e['emitted']}·{e['hits']} | {b['emitted']}·{b['hits']} | {c['positive_but_empty']}→{e['positive_but_empty']} |")
    lines += ['', 'E는40개에서65개를 제시했다. C는33개, B는200개였다. 출력량을 줄이면서 C보다 적중을 늘렸지만 B가 찾던 양성을 일부 놓쳤다. 출력한 것 중 정답 비율만 비교하면 빈 답의 손실이 가려지므로 그 수치만으로 성공이라고 하지 않는다.', '',
        '## 관점을 잘 골라도 남은 문제', '',
        '**1. 관점 안에서 질문별로 사례를 충분히 가려내지 못한다.** P03의 승인 사례는5개이고 출력 상한도5개다. P03만 선택한16개 질문 모두 동일한5개 사례를 제시했고 순서만 달랐다. 현재 소스 조건과 유형 구분을 통과하면 유사도가 낮아도 따로 탈락시키는 기준이 없다. 따라서 관점 선택 성공이 곧 질문별 정밀 추천 성공이 아니다.', '',
        '예를 들어 대출 서류 불일치 확인 IVQ017에서는 P03이 선택되지만 P02에만 연결된 대출 문서 추출 사례와 보험 신청서 사례가 후보에서 빠진다. 기존 AI Silver는 일부를 양성으로 봤다. 반대로 P03 안의 운송 청구서·직원 신원 검증 사례는 다른 질문에도 계속 남는다. 사례를 다른 업무에 전이할 수 있는 범위와 현재 관점 연결의 세밀함을 구분해서 검토해야 한다.', '',
        '**2. 고정된 기존 문장·조건 해석 오류도 남아 있다.**', '',
        '- VQ020에서 LLM은 민원 내용의 조치·장소 파악을 P02로 골랐지만, 기존 문장 구분기가 ‘제안하고’의 일부를 부정 표현으로 읽어 작업 절을 제외로 분류했다. 어댑터는 이를 조용히 덮어쓰지 않고 보류했다. 이번 결과를 본 뒤 수정하지 않았다.',
        '- IVQ013의 입력은 ‘통화 녹취 텍스트’인데 기존 조건 규칙은 ‘통화’를 보고 음성 입력이 필요하다고 처리했다. P02 사례 중 그 조건을 확인할 수 없어0개가 됐다. 이미 텍스트인 입력과 음성 원본을 구별할 필요가 있다. 이는 현 규칙의 구체적 한계이며, 그 사례들이 질문 전체를 해결할 수 있다는 뜻은 아니다.', '',
        '**3. 현재4관점 목록 밖의 작업이 많다.** LLM은27개 질문에서 관점을 골랐고, 어댑터 보류1개를 거쳐26개가 검색 분기를 만들었다. 조건 확인으로1개가 더 비어 실제 사례를 제시한 질문은25개다. P01 1회·P02 10회·P03 17회가 원래 선택됐고 P04는0회다. 복수 관점은 IVQ010 한 질문뿐이다. 이 표본으로 다중관점 일반 효과나 P04의 검색 이득을 입증하지 못했다.', '',
        '관점 선택이 없는 나머지 질문을 모두 오류라고 하지는 않는다. 요약·예측·원인 분석 등 현재 상세 관점 목록 밖의 요청도 있다. 그러나 기존 채점표상 전이 관련성이 있는 사례를 강한 관점 제한으로 배제하는 경우도 있다.', '',
        '## 정답을 잃은 위치', '',
        '숫자는 기존 AI 채점표가17개 안에서 양성으로 본 질문×사례 쌍이다. 연결되지 않은 사례가 실제로 정답인지 독립 인증한 것은 아니다.', '',
        '| 채점표 | LLM 관점 미선택 | 연결 보류 | 선택 관점 밖 사례 | 조건 보류 | 최종5개 배정 탈락 | 최종 적중 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for label, result in accounting.items():
        counts = result['counts']
        lines.append('| ' + names[label] + ' | ' + ' | '.join(str(counts[k]) for k in ('no_llm_view','adapter_pending','unlinked_to_selected_view','condition_deferred','final5_drop','hits')) + ' |')
    lines += ['', 'Claude40의 양성21쌍 중11쌍은 최종 출력에 남았고10쌍은 선택 관점의 연결 밖이라 빠졌다. 이 자료에서는 남은 손실을 관점 미선택만의 문제로 설명할 수 없다. Gemini40은 양성78쌍 중33쌍이 남고, 관점 미선택15쌍·선택 관점 밖25쌍·최종5개 배정5쌍을 놓쳤다.']
    lines += ['', '## 전체112 정답으로 보면', '',
        '현재17개가 포함하는 기존 양성 쌍은 개발 원본22/89, 작업용19/54, 부분 재검토20/53, Claude21/48, Gemini78/382다. 이 작은 목록 밖의 정답을 검색하는 능력은 이번 주 비교로 확인하지 못했다.', '',
        '전체112 정답을 분모로 해도 E의 F1은 개발20에서 A/B/C보다 높았지만40개에서는 B보다 낮았다(Claude E0.1833, B0.1993; Gemini E0.0686, B0.1026). 이 계산은17개 출력의 전역 누락을 드러내는 것이며 전체112 검색 확장 실험이 아니다.', '',
        '## 이번 판단과 다음 최소 보완', '',
        '1. **LLM 선택을 사용해볼 근거는 생겼다.** 규칙 방식의 알려진 누락을 일부 회복했고 개발20개의 최종 사례 점수도 올랐다. 그러나 현재 E를 단순 검색의 우월한 대체 모델로 채택하지 않는다.',
        '2. 전체112 확장 전에 현재 연결된 사례를 질문별로 구별하는 최소 기준을 정해야 한다. 관점은 후보 경로로 활용하되 각 사례의 실제 작업·자료·기준·지원 범위를 확인해 출력에서 제외하거나 조건부로 구분하는 방법이 필요하다. 단순히 유사도 임계값을 이번 결과에 맞춰 정하지 않는다.',
        '3. ‘제안하고’의 부정 오인, 녹취 텍스트의 음성 입력 오인처럼 확인된 문장·조건 오류는 추천 점수와 분리한 기능 검사로 보완할 수 있다. 이는 후속 작업이며 이번 동결 실험에는 적용하지 않았다.',
        '4. 보완 효과는 지금 본 실패 질문만으로 판정하지 않고 별도로 고정한 미사용 질문에서 확인해야 한다. 관점 밖의 전이 사례를 살리는 보조 검색과 관점 세분화도 가설로 남기며, 이번에 추가 실험하지 않는다.', '',
        '**이번 요청 범위는 모두 완료했고 여기서 종료한다.** 전체112 확장·새 정답 채점·추가 학습·결과를 보고 프롬프트 반복 수정은 하지 않았다.', '',
        '## 비용·재현·검사', '',
        f"새 API 호출56회, 이전 응답 재사용4개다. 신규 사용량 기준 추정 비용은 **${load('selection-run.json')['estimated_new_usage_usd']:.6f}**이며 사전 예약 상한은$4.246160, 작업 예산은$5였다. 이전 선택 실험 비용은 이번 신규 비용에 다시 더하지 않았다. 새 호출56개와 재사용4개 모두 구조·질문 인용 검증을 통과했다. [모델·공식 요금](https://platform.claude.com/docs/en/models/sonnet-5-5/overview)을 사용했으며 추정액은 청구서 확정액이 아니다.", '',
        '기존 로컬 BGE로 새 문자열16개만 벡터화했다. 새 학습은0회다. 60개 LLM 응답, 최종 순위·근거, 전체 지표·bootstrap, 기존 A/B/C 보존, 기존83개 채점파일 지문을 재현 검사했다. 기존 모델·프롬프트·사례·정답을 결과에 맞춰 바꾸지 않았다. 봉인 Test15는 열지 않았다.', '',
        '처음 재현 검사에서 개수 집계의 숫자형 키가 JSON 저장 후 문자열 키가 되는 형식 차이가 발견됐다. 수치 지표는 처음부터 같았다. 원본 동결 검증기를 수정하지 않고 별도 검증기에서 JSON 형식만 정규화해 비교했다. 모델·순위·점수·정답은 그대로이며 [검증 형식 보완 기록](verification-format-note.json)에 지문과 사유를 남겼다. 재현 명령은 `python -m scripts.verify_llm_catalog_retrieval_comparison_20261109`다.', '',
        '## 원본 확인', '',
        '- [사전 계획](../llm-catalog-retrieval-comparison-20261109-protocol.md)',
        '- [60개 질문별 선택·사례·F1](questions-and-results.ko.md)',
        '- [전체 지표·구간·코호트·민감도](evaluation.json)',
        '- [순위](predictions.json) / [질문과 사례의 근거](query-case-evidence.json)',
        '- [LLM 선택 원본](selections.json) / [전송 본문](requests.json) / [기존 응답 재사용 근거](reused-selections.json)',
        '- [손실 위치별 집계](failure-attribution.json) / [동일 P03 사례 집합 진단](same-p03-case-set.json)',
        '- [개발 연결 예시](integration-examples.json) / [입력 접근·보존 기록](inference-audit.json)',
        '- [실행 비용](selection-run.json) / [예산 예약](reservation.json)',
        '- [동결 지문](freeze.json) / [소스 보관본](source-snapshot.zip) / [재현 확인](verification.json)', '',
        '모든 채점은 기존 AI Silver이며 독립 사람 Gold가 아니다. assistant가 같은 자료를 보고 관점 목록과 설명을 만들었으므로 개발 편향이 있다. 자료는 로컬 작업사본에 저장했으며 GitHub에 커밋·업로드하지 않았다.', '']
    (OUT / 'README.ko.md').write_text('\n'.join(lines), encoding='utf-8')
    readable = ['# 질문별 비교 결과', '', '기존 개발·재사용60개. 아래 F1은 같은17개 안의 기존 AI Silver이며×100 표시다. NA는 해당 표에 양성이 없는 질문이다.', '']
    for q, row in questions.items():
        r = p[q]
        readable += ['## ' + q, '', '> ' + row['text'], '',
            '- LLM 선택: ' + (', '.join(r['llm_selected']) or '없음'),
            '- 검색에 연결된 관점: ' + (', '.join(r['adapted_selected']) or '없음'),
            '- 상태: ' + r['catalog_state'], '- 이전 선택기 개발에 사용: ' + ('예' if q in REGRESSION_IDS else '아니오; 과거 연구에서는 이미 관찰'), '',
            '| 채점표 | A 기존 | B 업무 중심 | C 규칙 | E LLM |', '|---|---:|---:|---:|---:|']
        for name, result in x['results_inside17'].items():
            if q in result['per_query']:
                v = result['per_query'][q]
                readable.append('| ' + names[name] + ' | ' + ' | '.join(pct(v[s]['F1@5']) for s in SYSTEMS) + ' |')
        readable += ['', '**LLM 방식이 제시한 사례:**', '']
        for case in r['systems']['E_LLMCatalog17']['ranking']:
            readable.append('- ' + case + ': ' + registry[case]['task'])
        if not r['systems']['E_LLMCatalog17']['ranking']:
            readable.append('- 제시 없음')
        for record in details[q]['perspective_selection']['selected']:
            readable += ['', '**' + record['id'] + ' 선택 근거:** ' + ' / '.join(record['reasons']), '']
            readable += ['- ' + e['kind'] + ': “' + e['quote'] + '”' for e in record['evidence']]
        if r['adapter_problems']:
            readable += ['', '**연결 보류:** ' + json.dumps(r['adapter_problems'], ensure_ascii=False)]
        readable += ['']
    (OUT / 'questions-and-results.ko.md').write_text('\n'.join(readable), encoding='utf-8')
    for name, value in [('failure-attribution.json', accounting), ('same-p03-case-set.json', {
        'single_P03_queries': len(p03), 'same_case_set_for_all': True, 'per_query': p03,
        'interpretation': '5 approved P03 cases and output cap5: same cases, ordering may change; no extra per-case rejection threshold'})]:
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    provenance = {'post_run_interpretation': True, 'report_script_sha256': sha(__file__),
        'evaluation_sha256': sha(OUT / 'evaluation.json'),
        'artifact_sha256': {p: sha(OUT / p) for p in ['README.ko.md','questions-and-results.ko.md','failure-attribution.json','same-p03-case-set.json']},
        'extra_paid_calls': 0, 'method_or_prompt_changed': False}
    (OUT / 'report-provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('REQUESTED_STEPS_1_TO_4_REPORTED')


if __name__ == '__main__':
    main()
