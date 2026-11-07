"""Render the Korean report from preserved experiment artifacts."""
import json
from statistics import mean

from ax_research.heldout import jsonl, read, write
from scripts.fixed_three_views import DEV, OUT, ROOT, SLOTS

CORRECTED = OUT / 'corrected'
NAMES = {'A': '원문', 'B': '동적 3관점+원문', 'C': '고정 3관점+원문', 'D': '고정 3관점만'}
SLOT_NAMES = dict(zip(SLOTS, ('현업', '운영', '기술')))


def percent(value):
    return '미정의' if value is None else f'{value*100:.2f}%'


def metric_table(lines, macro, metrics, spread=False):
    lines.extend(['| 조건 | ' + ' | '.join(metrics) + ' |',
                  '|---|' + '---:|' * len(metrics)])
    for name, label in NAMES.items():
        values = []
        for metric in metrics:
            row = macro[name, metric]
            suffix = f" ± {row['repeat_sd']*100:.2f}%p" if spread and row['repeat_sd'] is not None else ''
            values.append(f"{percent(row['mean'])}{suffix} (n={row['n']})")
        lines.append(f'| {name} {label} | ' + ' | '.join(values) + ' |')


def main():
    data = read(CORRECTED/'evaluation.json')
    pilot = read(OUT/'evaluation.json')
    pred = read(CORRECTED/'comparison_predictions.json')
    original = read(OUT/'predictions.json')
    assert all(pred['systems'][c] == original['systems'][c] for c in 'AB')
    macro = {(r['condition'], r['metric']): r for r in data['macro']}
    cost = read(OUT/'api_ledger_final.json')
    grounding = read(CORRECTED/'grounding.json')['rows']
    pilot_grounding = read(OUT/'grounding.json')['rows']
    source_review = read(OUT/'source_review.json')
    tests = read(OUT/'tests.json')
    slots = read(CORRECTED/'slots.json')['records']
    rows = data['per_query']
    paths = data['path_discovery']
    comparisons = []
    for baseline in 'ABD':
        for metric in ('F1@5', 'nDCG@10'):
            a, b = macro[baseline, metric]['mean'], macro['C', metric]['mean']
            comparisons.append({'baseline': baseline, 'metric': metric, 'delta': b-a if None not in (a,b) else None})
    fmt = lambda value: '미정의' if value is None else f'{value*100:+.2f}%p'
    lines = ['# 고정 3관점 개발 실험', '', '2026-11-07', '', '## ① 전체 진행 결과', '',
             '1단계에서 현업·운영·기술을 정의했고, 2단계에서 기존 C1에 관점 생성 연결부를 추가했다. 3단계에서 개발 질문 10개와 사례 112개로 네 조건을 실행했고, 4단계에서 점수·원문 보존·관점별 발견을 분석했다.',
             '', '첫 고정 프롬프트는 원문에 정보가 있는 슬롯도 비우는 경우가 있었다. 결과 점수를 열기 전에 슬롯 기준을 보완하고 고정 조건 30회를 모두 다시 생성했다. 동적 조건의 동일 응답을 두 실험에 공통으로 사용했다. 첫 실험의 입력·출력·성능도 예비 결과로 보존했다.',
             '', '[설계](design.md) · [사전 등록](preregistration.json) · [보완 기록](corrected/amendment.json)', '',
             '## ② 성능 비교표', '',
             '± 뒤 숫자는 회차별 평균의 모집단 표준편차다. A는 한 번 계산한 원문 순위를 재사용한다. 같은 지표에서 네 조건의 질문 집합을 맞췄다.', '']
    metric_table(lines, macro, ['F1@5', 'F1@10', 'F1@20', 'nDCG@5', 'nDCG@10'], True)
    lines += ['']
    metric_table(lines, macro, ['Precision@5', 'Recall@5', 'Precision@10', 'Recall@10', 'Precision@20', 'Recall@20'])
    lines += ['', '기존 v2 AI-Silver의 완전 판정 질문을 주 비교에 사용했다. 양성이 없는 질문의 Recall·F1과 이상 순위 이득이 0인 질문의 nDCG는 미정의다. 일부 판정 질문은 정의 가능한 개별 지표만 별도 기록했다.', '',
              '| 비교 | C의 F1@5 차이 | C의 nDCG@10 차이 |', '|---|---:|---:|']
    for i, baseline in enumerate('ABD'):
        lines.append(f"| C − {baseline} | {fmt(comparisons[2*i]['delta'])} | {fmt(comparisons[2*i+1]['delta'])} |")
    for name, evaluation in [('예비 고정 C', pilot), ('보완 고정 C', data)]:
        cm = {r['metric']: r for r in evaluation['macro'] if r['condition'] == 'C'}
        lines.append(f"\n{name}의 F1@5는 {percent(cm['F1@5']['mean'])}, nDCG@10은 {percent(cm['nDCG@10']['mean'])}였다.")
    matched = {(r['condition'], r['metric']): r for r in data['three_searchable_paths_sensitivity']}
    lines += ['', '세 회차 모두 검색 가능 경로가 3개인 질문만 남긴 민감도 결과다.', '']
    metric_table(lines, matched, ['F1@5', 'nDCG@10'])
    lines += ['', '## ③ 관점별 성능 분석', '',
              '| 고정 관점 | 검색 가능 회차 | 기능 인식 경로 | Top-5 관련 발견 | 그 관점에서만 발견 |',
              '|---|---:|---:|---:|---:|']
    role_stats = {}
    for role, name in SLOT_NAMES.items():
        rr = [p for p in paths if p['kind'] == 'corrected' and p['view'] == role and p['k'] == 5]
        role_stats[name] = {'searched': len(rr), 'functions': sum(bool(r['functions']) for r in rr),
                            'hits': sum(len(r['known_relevant']) for r in rr),
                            'unique': sum(len(r['unique_within_triplet']) for r in rr)}
        row = role_stats[name]
        lines.append(f"| {name} | {row['searched']}/30 | {row['functions']} | {row['hits']} | {row['unique']} |")
    most = max(v['hits'] for v in role_stats.values())
    useful = ', '.join(k for k, v in role_stats.items() if v['hits'] == most)
    lines += ['', f'개별 경로의 Top-5 관련 발견 수는 {useful} 관점이 가장 많았다. 발견 수는 질문·회차별 합계다. 원질문 AI-Silver로 셌으며 각 관점의 독립 정답이나 인과 효과를 뜻하지 않는다.', '',
              '| 방식 | 행동 | 대상 | 결과 | 목적 | 빈 슬롯 |',
              '|---|---:|---:|---:|---:|---:|']
    for label, records, kind in [('동적', grounding, 'dynamic'), ('고정 예비', pilot_grounding, 'fixed'),
                                 ('고정 보완', grounding, 'corrected')]:
        subset = [r for r in records if r['kind'] == kind]
        counts = [sum(r['triplet'][key] for r in subset) for key in ('action', 'object', 'output', 'purpose')]
        lines.append('| '+label+' | '+' | '.join(f'{n}/{len(subset)}' for n in counts)
                     +f" | {sum(3-r['searchable_count'] for r in subset)} |")
    lines += ['', '단어 검사는 3슬롯 전체에서 원문 핵심 표현을 찾는 진단이다. 다른 말로 충실히 옮긴 내용과 부정 표현의 뒤집힘은 이 숫자만으로 구별하기 어렵다.', '']
    for observation in source_review['observations']:
        lines.append(f'- {observation}')
    recognized = {}
    for kind in ('dynamic','corrected'):
        subset = [r for r in paths if r['kind'] == kind and r['k'] == 5]
        recognized[kind] = {'total': len(subset), 'recognized': sum(bool(r['functions']) for r in subset)}
    source = read(DEV/'predictions/C1_details.json')['filtered_query_profiles']
    lines += ['', f"기존 C1 규칙이 기능을 하나 이상 찾은 입력은 원문 {sum(bool(v['function_ids']) for v in source.values())}/{len(source)}, 동적 {recognized['dynamic']['recognized']}/{recognized['dynamic']['total']}, 고정 {recognized['corrected']['recognized']}/{recognized['corrected']['total']}였다. 기능 ID 검출은 정확한 기능 매핑을 보장하지 않는다.",
              '', '## ④ 실제 추천 사례 비교', '',
              '| 비교 | Top-5 진입 / 이탈 | Top-10 진입 / 이탈 | Top-20 진입 / 이탈 |',
              '|---|---:|---:|---:|']
    for left,right in ('AB','AC','BC','DC'):
        values = []
        for k in (5,10,20):
            events = [r for r in data['changes'] if (r['from'],r['to'],r['k']) == (left,right,k)]
            values.append(f"{sum(len(r['gained']) for r in events)} / {sum(len(r['lost']) for r in events)}")
        lines.append(f'| {left} → {right} | '+' | '.join(values)+' |')
    registry = read(ROOT/'docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    rankings = {(c,r['query_id'],r.get('repeat',0)):r['ranking'] for c,rs in pred['systems'].items() for r in rs}
    for key, name in [('gained','진입'),('lost','이탈')]:
        examples = [r for r in data['changes'] if r['from']=='B' and r['to']=='C' and r['k']==5 and r[key]]
        if not examples:
            examples = [r for r in data['changes'] if r['from']=='B' and r['to']=='C' and r['k']==20 and r[key]]
        for event in examples[:2]:
            q, repeat, cid = event['query_id'], event['repeat'], event[key][0]
            a,b = (rankings[c,q,repeat].index(cid)+1 for c in 'BC')
            lines.append(f"\n- {q[-2:]}번 {repeat}회차 {name}. {registry[cid]['task']} ({cid}), B {a}위 → C {b}위.")
    focus_query, focus_case = 'NV20261102_01', 'AXALL_US_OMB_2025_02663'
    trace = {}
    for condition, folder, repeat in [('B', OUT, 1), ('C', CORRECTED, 4)]:
        trace[condition] = next(r['conditions']['E4'] for r in jsonl(folder/'inference/combined_scores.jsonl')
                                if (r['query_id'], r['case_id'], r['repeat']) ==
                                (focus_query, focus_case, repeat))
    lines += ['', '01번의 이탈 원인을 점수로 확인했다. 동적 관점의 짧은 문서 위치 확인 문구에서는 C1이 지식 검색 기능을 인식해 규칙 점수가 4였다. 보완 고정 현업은 확인 기능을 잡았으나 이 사례의 지식 검색 기능과 겹치지 않았고, 운영·기술도 공통 기능을 찾지 못해 최고 규칙 점수가 2였다.',
              '', f"해당 사례의 의미 점수는 B {trace['B']['semantic']:.3f}, C {trace['C']['semantic']:.3f}였다. 최종 점수는 B {trace['B']['score']:.3f}에서 C {trace['C']['score']:.3f}로 내려갔다. 이 사례는 기능을 하나 이상 찾는 비율과 올바른 기능을 연결하는 능력이 다르다는 점을 보여준다.",
              '', '질문별 세 회차의 원점수와 관련 사례 진입·이탈은 결과 파일에 있다. 반복에서 같은 사례가 여러 번 움직이면 각 회차에 기록했다.', '',
              '## ⑤ 연구적 결론', '']
    diff_f1, diff_ndcg = comparisons[2]['delta'], comparisons[3]['delta']
    lines.append(f'동적 3관점 대비 고정 3관점의 F1@5 차이는 {fmt(diff_f1)}, nDCG@10 차이는 {fmt(diff_ndcg)}다.')
    if diff_f1 is not None and diff_ndcg is not None:
        if diff_f1 > 1e-10 and diff_ndcg > 1e-10:
            lines.append('\n두 지표의 개발 평균에서 고정 관점이 앞섰다.')
        elif diff_f1 <= 1e-10 and diff_ndcg <= 1e-10:
            lines.append('\n두 지표에서 고정 관점의 개선을 확인하지 못했다.')
        else:
            lines.append('\n두 지표의 방향이 달라 고정 관점의 전반적인 우위를 확인하기 어렵다.')
    for metric in ('F1@5', 'nDCG@10'):
        b, c = (macro[name, metric]['repeat_sd'] for name in 'BC')
        if None not in (b, c):
            lines.append(f'\n{metric}의 회차 변동은 B {b*100:.2f}%p, C {c*100:.2f}%p였다.')
    for metric in ('F1@5','nDCG@10'):
        per = {}
        for q in pred['query_ids']:
            vals = [[r['metrics'][metric] for r in rows if r['query_id']==q and r['condition']==c] for c in 'BC']
            if all(v and None not in v for v in vals):
                per[q[-2:]] = mean(vals[1])-mean(vals[0])
        per = {q:d for q,d in per.items() if abs(d)>1e-10}
        lines.append(f"\n{metric}에서 B→C가 달라진 질문은 " + (', '.join(f'{q}번 {fmt(d)}' for q,d in per.items()) or '없다')+'.')
    leave_one = {(r['condition'], r['metric']): r['mean'] for r in data['leave_one_out'][focus_query]}
    lines += ['', f"01번을 제외하면 B·C의 F1@5는 둘 다 {percent(leave_one['B','F1@5'])}이고, nDCG@10은 B {percent(leave_one['B','nDCG@10'])}, C {percent(leave_one['C','nDCG@10'])}다. 전체 F1@5 하락은 이 질문 한 개에 집중됐다. 예비 고정의 높은 nDCG@10은 빈 슬롯이 있는 별도 결과여서 보완 고정의 동등 경로 비교와 나눠 해석한다.",
              '', '고정에 원문을 더하면 Top-5 F1과 Top-10 nDCG는 조금 올라갔다. 반대로 F1@10·20에서는 고정관점만 사용한 D가 더 높았다. 원문 결합 효과는 추천 길이에 따라 달랐다.',
              '', '세 회차 표준편차는 동일한 개발 질문에서의 생성 흔들림을 나타낸다. 개발 질문 수와 AI 평가표의 한계 때문에 다른 질문에서 같은 효과가 유지되는지는 아직 확인되지 않았다.',
              '', '## ⑥ 다음 연구 제안', '',
              '고정 관점의 우위를 확인하는 5단계 진입은 보류를 권한다. 개발 자료에서 01번처럼 짧은 핵심 행동을 각 역할에 남기는지와 10번처럼 우선순위를 제외 조건으로 바꾸는지를 먼저 점검할 필요가 있다. 이번 실험에서는 신규 독립 Test를 실행하지 않았다.',
              '', '## ⑦ GitHub 작업 결과', '',
              '- 연구 브랜치 `research/fixed-three-views-20261107`',
              f"- 자동 검사 {tests['passed']}개 통과.",
              f"- 유료 요청 {len(cost['calls'])}회. 사용량 추정 ${cost['estimated_usd']}, 보수적 한도 계산 ${cost['conservative_usd']}. 캐시 쓰기 요금을 포함했다. [공식 가격](https://developers.openai.com/api/docs/models/gpt-6-luna)",
              '- 첫 고정 06번 2회차에서 현업 인용문이 원문과 일치하지 않아 한 번 재요청했다. 두 응답과 비용을 저장했다. [형식 실패 기록](generation_failures.json)',
              '- [완료 상태](final_status.json) · [호출별 비용](api_ledger_final.json) · [주 결과](corrected/evaluation.json) · [예비 결과](evaluation.json) · [질문별 보존 점검](corrected/grounding.json)', '',
              '재현 순서는 분리된 작업 디렉터리에서 `scripts.fixed_three_views`의 prepare, generate, infer를 실행하고 `scripts.fixed_three_corrected`의 같은 세 단계를 실행하는 것이다. infer에는 서로 다른 빈 `--scratch` 경로를 준다. 이어 `scripts.fixed_three_evaluate`와 `scripts.fixed_three_grounding`을 기본 출력과 corrected 출력에 각각 적용한다. 검색 재현에는 보존한 API 응답을 사용할 수 있다. 모델·입력 해시는 사전 등록과 각 추론 봉인에 있다.', '']
    (OUT/'README.md').write_text('\n'.join(lines), encoding='utf-8', newline='\n')
    status = {
        'status': 'COMPLETE_WITH_LIMITATIONS', 'stages_complete': [1,2,3,4],
        'new_independent_test_executed': False, 'label_source': 'Dev frozen v2 AI-Silver',
        'primary': 'corrected fixed prompt', 'pilot_preserved': True, 'comparisons': comparisons,
        'metrics': data['macro'], 'path_contributions': role_stats, 'function_recognition': recognized,
        'tests': tests['passed'], 'api_calls': len(cost['calls']), 'api_estimated_usd': cost['estimated_usd'],
        'api_conservative_usd': cost['conservative_usd'], 'git_branch': 'research/fixed-three-views-20261107',
        'focus_case_trace': trace, 'focus_question_leave_one_out': {
            f'{condition}/{metric}': leave_one[condition, metric]
            for condition in 'BC' for metric in ('F1@5','nDCG@10')},
        'recommended_stage5': 'defer',
    }
    (OUT/'final_status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2)+'\n',
                                         encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
