"""Render source-limited new-Dev findings without selecting favorable runs."""
import json
from collections import Counter
from statistics import mean

from ax_research.heldout import read
from scripts import core_preservation_run as run
from scripts.core_preservation_quality import FIELDS

NAMES = {'A': '원문', 'B': '동적 3관점+원문',
         'C': '기존 고정 3관점+원문', 'E': '핵심 보존 고정 3관점+원문'}


def pct(value):
    return '미정의' if value is None else f'{value*100:.2f}%'


def delta(value):
    return '미정의' if value is None else f'{value*100:+.2f}%p'


def main():
    out = run.OUT
    data = read(out/'evaluation.json')
    quality = read(out/'quality_summary.json')
    discovery = read(out/'discovery.json')
    costs = read(out/'api_ledger.json')
    pred = read(out/'predictions.json')
    labels = read(out/'labels.json')['records']
    macro = {(r['condition'], r['metric']): r for r in data['macro']}
    intervals = {(r['baseline'], r['metric']): r for r in data['bootstrap']}
    meta = {q: [r for r in labels if r['query_id'] == q] for q in pred['query_ids']}
    conclusion = {}
    for baseline in 'ABC':
        f, n = (intervals[baseline, metric]['mean_E_minus_baseline']
                for metric in ('F1@5', 'nDCG@10'))
        conclusion[baseline] = {'F1@5': f, 'nDCG@10': n}
    successful = all(conclusion['C'][k] is not None and conclusion['C'][k] > 1e-10
                     for k in ('F1@5', 'nDCG@10'))
    text = ['# 핵심 업무 보존형 고정 3관점 개발 실험', '', '2026-11-07', '',
            '## 1. 진행 결과', '',
            '1단계에서 추출 필드와 E 프롬프트를 먼저 고정했다. 그 뒤 새 개발 질문8개를 작성하고 질문·판정 기준·모델 해시를 동결했다. 2단계에서 추출→관점 생성 연결을 구현했고, 3단계에서 A·B·C·E를 모두 새 질문으로 실행해 봉인했다. 4단계에서는 별도 관련성·품질 판정으로 같은 출력들을 평가했다.',
            '', '신규 질문은 기존112사례 목록을 확인한 같은 AI가 작성했다. 기존 개발 성능과 이번 성능은 질문·정답이 달라 직접 비교하지 않는다. 과거 독립 Test 파일은 이번 생성·추론·평가의 입력으로 사용하지 않았다. 작성자는 이전 연구 대화의 맥락을 알고 있어 외부 독립 작성자 수준의 독립성을 주장할 수 없다.',
            '', '추출응답 한 건이 미상 필드를 객체 대신 null로 반환해 초기 파서가 멈췄다. 같은 수신 응답을 다시 읽도록 파서만 수정해 이어갔다. 모델 응답과 정보 누락을 보존했고 유료 재호출은0회였다. [수신 복구 기록](parser_recovery.json)', '',
            '## 2. A·B·C·E 추천 성능', '',
            '| 조건 | F1@5 | F1@10 | F1@20 | nDCG@5 | nDCG@10 |',
            '|---|---:|---:|---:|---:|---:|']
    for c in 'ABCE':
        cells = []
        for metric in ('F1@5', 'F1@10', 'F1@20', 'nDCG@5', 'nDCG@10'):
            row = macro[c, metric]
            spread = f" ± {row['repeat_sd']*100:.2f}%p" if row['repeat_sd'] is not None else ''
            cells.append(f"{pct(row['mean'])}{spread} (n={row['n']})")
        text.append(f'| {c} {NAMES[c]} | '+' | '.join(cells)+' |')
    text += ['', '±는 회차별 평균의 모집단 표준편차다. 같은 지표의 모든 조건은 동일한 질문 집합을 사용했다. 전수 판정이 없는 질문은 전체 Recall·F1·nDCG를 계산하지 않았고 양성이0개인 질문의 Recall·F1도 미정의로 남겼다.',
             '', '| 조건 | P@5 | R@5 | P@10 | R@10 | P@20 | R@20 |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for c in 'ABCE':
        text.append(f'| {c} | '+' | '.join(
            f"{pct(macro[c,m]['mean'])} (n={macro[c,m]['n']})"
            for m in ('Precision@5', 'Recall@5', 'Precision@10', 'Recall@10', 'Precision@20', 'Recall@20'))+' |')
    text += ['', '| 질문 | 판정 /112 | 보류 | 알려진 관련 사례 | A F1@5 | B | C | E |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    qmeans = {}
    for q, rs in meta.items():
        cells = []
        for c in 'ABCE':
            values = [r['metrics']['F1@5'] for r in data['per_query']
                      if r['condition'] == c and r['query_id'] == q]
            qmeans[c, q] = mean(values) if None not in values else None
            cells.append(pct(qmeans[c, q]))
        text.append(f"| {q} | {sum(r['status']=='JUDGED' for r in rs)} | "
                    f"{sum(r['status']=='ABSTAIN' for r in rs)} | "
                    f"{sum(r['grade'] is not None and r['grade']>=2 for r in rs)} | "+' | '.join(cells)+' |')
    text += ['', '## 3. 기존 고정 C 대비 효과', '',
             ('두 주 지표의 평균에서 E가 C보다 높았다.' if successful
              else '두 주 지표에서 E의 일관된 평균 우위를 확인하기 어렵다.'),
             '', '## 4. 기존 동적 B 및 원문 A 대비 효과', '',
             '| 비교 | 지표 | E의 차이 | 질문 bootstrap95% 구간 |',
             '|---|---|---:|---|']
    for baseline in 'ABC':
        for metric in ('F1@5','nDCG@10'):
            row = intervals[baseline, metric]
            lo, hi = row['paired_question_bootstrap95']
            text.append(f"| E−{baseline} | {metric} | {delta(row['mean_E_minus_baseline'])} | {delta(lo)} ~ {delta(hi)} |")
    text += ['', '신뢰구간은 같은 질문의 세 회차를 먼저 평균한 뒤 질문을 짝지어1만번 재표집했다. 이 작은 AI-Silver 표본에 조건부인 구간이며, 표본8개나 같은 모델 반복을 큰 독립 표본으로 바꾸지는 않는다.',
             '', '## 5. 핵심 업무 보존과 관점 기여', '',
             '| 조건 | 목적 평균/2 | 행동 | 대상 | 결과 | 제약 | 역할 구분 | 근거 밖 내용 지적 응답 |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in quality['summary']:
        text.append('| '+r['condition']+' | '+' | '.join(
            f"{r['mean_scores0to2'][f]:.2f}" for f in FIELDS)+f" | {r['unsupported_candidate_count']}/{r['n']} |")
    literal = quality['extraction_evidence_checks']
    text += ['', f"추출 필드 {len(literal)}개 중 미상은 {sum(r['unknown'] for r in literal)}개, 인용 근거가 원문과 다르게 반환된 필드는 {sum(not r['all_quotes_literal'] for r in literal)}개였다. 정확한 인용은 의미가 모두 맞음을 보장하지 않는다.",
             '', '품질 검토자는 방식명과 추천 순위를 받지 않은 같은 모델의 별도 요청이다. 원문 대비 3관점 전체를 평가했다. 역할 구분 점수는 현업·운영·기술을 의도한 C와 E에서 주로 해석한다. 동일 모델의 평가 편향과 원문 의미 검토의 불완전성이 남는다.',
             '', '| E 관점 | Top-5 관련 발견 합계 | 그 관점만의 발견 | 기능을 찾은 경로 |',
             '|---|---:|---:|---:|']
    role_stats = []
    for role, name in zip(run.SLOTS, ('현업','운영','기술')):
        subset = [r for r in discovery['path_discovery'] if
                  r['condition']=='E' and r['view']==role and r['k']==5]
        row = {'role': name, 'paths': len(subset),
               'related': sum(len(r['related_cases']) for r in subset),
               'unique': sum(len(r['unique_cases']) for r in subset),
               'function_paths': sum(bool(r['functions']) for r in subset)}
        role_stats.append(row)
        text.append(f"| {name} | {row['related']} | {row['unique']} | {row['function_paths']}/{row['paths']} |")
    text += ['', '발견 수는 질문·사례·회차별 합계이며 전체 문제의 Silver 관련성으로 셌다. 특정 관점 자체의 정답이나 그 관점을 제거한 인과 효과와는 구분한다.',
             '', '| 조건 | 기능 하나 이상 인식 | 표현 가능한 핵심 기능 전부 인식 |',
             '|---|---:|---:|']
    recognition = discovery['source_referenced_function_recognition']
    for c in 'BCE':
        subset = [r for r in recognition if r['condition']==c]
        representable = [r for r in subset if r['representable']]
        text.append(f"| {c} | {sum(r['any_recognized'] for r in subset)}/{len(subset)} | "
                    f"{sum(r['all_required_found'] for r in representable)}/{len(representable)} |")
    text += ['', '기대 기능은 추천 결과를 보기 전 새 질문의 핵심 동작을 기존18개 규칙과 연결해 작성한 진단 기준이다. 번역에는 전용 규칙이 없어 표현 가능한 기능 비율에서 제외했고 해당 질문의 추천 점수는 그대로 평가했다. 부가 기능 검출이 모두 오류인 것은 아니며, 양성 사례에서의 공유 기능도 별도 기록했다.',
             '', '## 6. 실제 추천 사례와 진입·이탈', '',
             '| 비교 | Top-5 진입/이탈 | Top-10 진입/이탈 | Top-20 진입/이탈 |',
             '|---|---:|---:|---:|']
    for c in 'ABC':
        values = []
        for k in (5,10,20):
            rs = [r for r in discovery['changes'] if r['baseline']==c and r['k']==k]
            values.append(f"{sum(len(r['gained']) for r in rs)} / {sum(len(r['lost']) for r in rs)}")
        text.append(f'| {c}→E | '+' | '.join(values)+' |')
    ranks = {(c,r['query_id'],r.get('repeat',0)):r['ranking']
             for c, rs in pred['systems'].items() for r in rs}
    registry = read(run.ROOT/'docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    examples = []
    for field, name in [('gained','진입'),('lost','이탈')]:
        selected = [r for r in discovery['changes'] if r['baseline']=='C' and r['k']==5 and r[field]]
        if not selected:
            selected = [r for r in discovery['changes'] if r['baseline']=='C' and r['k']==20 and r[field]]
        for row in selected[:2]:
            cid = row[field][0]
            q, repeat = row['query_id'], row['repeat']
            a,b = (ranks[c,q,repeat].index(cid)+1 for c in ('C','E'))
            examples.append({'query_id':q,'repeat':repeat,'case_id':cid,'change':name,'C':a,'E':b})
            text.append(f"\n- {q} {repeat}회차 {name}. {registry[cid]['task']} ({cid}), C {a}위→E {b}위.")
    text += ['', '위 수는 알려진 관련 사례의 움직임이다. 보류 사례는 무관으로 바꾸지 않았고, 전체112개 후보를 유지했다.',
             '', '## 7. 성능 변화와 실패 원인', '']
    changed_queries = []
    for q in pred['query_ids']:
        a,b = qmeans['C',q], qmeans['E',q]
        if a is not None and b is not None and abs(a-b)>1e-12:
            changed_queries.append({'query_id':q,'delta':b-a})
            text.append(f"- {q} F1@5의 E−C 차이는 {delta(b-a)}였다.")
    if not changed_queries:
        text.append('평가 가능한 질문의 F1@5는 C와 E에서 같았다.')
    text += ['', '질문을 하나씩 제외한 결과와 사례별 규칙·의미 점수는 결과 파일에 보존했다. 좋은 질문만 빼거나 나쁜 질문의 정답을 고쳐 주 결과를 만들지 않았다. 핵심 보존 지시와 추가 구조화·토큰이 함께 달라진 E 전체의 효과를 비교했으며 추출 단계만의 독립 효과는 분리하지 않았다.',
             '', '## 8. 신뢰성과 한계', '',
             f"896개 판정 상태는 {data['label_counts']}다. 질문·정답과 품질 평가는 같은 AI 계열에 의존하며 사람 Gold 검증은 수행하지 않았다. 질문은 코퍼스의 업무 목록을 참고해 작성한 개발 자료다. 실제 독립 업무 전체에 대한 일반화나 큰 표본의 유의성을 주장하기 어렵다.",
             '', '세 회차 모두와 보류·무양성 질문을 보존했다. 지표 분모와 정의 불가 이유는 질문별 결과에 있다. 실제 업무 인계·권한·부정 표현의 오류 여부는 수치와 함께 원문을 다시 확인할 필요가 있다.',
             '', '## 9. 다음 독립 Test 권고', '',
             ('E를 후속 독립 검증의 후보로 검토할 수 있으나 최종 논문 모델 채택은 독립 질문과 판정 검증 뒤에 판단해야 한다.'
              if successful else '최종 논문 모델로 E를 채택할 근거는 아직 부족하다. 별도 개발 자료에서 핵심 보존과 실제 검색 기능 연결을 먼저 확인하는 편이 적절하다.'),
             '', '신규 독립 Test 실행은 이번 범위에 포함하지 않았다.',
             '', '## 10. GitHub와 비용', '',
             '- 브랜치 `research/core-preserved-three-views-20261107`',
             '- [사전 등록](preregistration.json) · [추출·생성 프롬프트](../../scripts/core_preservation_prompts.py) · [전체 지표](evaluation.json) · [블라인드 품질 점검](quality_summary.json)',
             f"- 유료 호출 {len(costs['calls'])}회, 추정 ${costs['estimated_usd']}, 보수 계산 ${costs['conservative_usd']}로 $2 이내다. 캐시 쓰기 요금을 포함한다. [공식 단가](https://developers.openai.com/api/docs/models/gpt-6-luna)", '',
             '| 용도 | 호출 수 | 추정 비용 |','|---|---:|---:|']
    by_kind = {}
    for kind in ('B','C','X','E','judge','quality'):
        subset = [r for r in costs['calls'] if r['kind']==kind]
        from decimal import Decimal
        amount = sum((Decimal(r['estimated_usd']) for r in subset), Decimal())
        by_kind[kind] = {'calls':len(subset),'usd':str(amount)}
        text.append(f"| {kind} | {len(subset)} | ${amount} |")
    text += ['', 'E의 실제 생성 비용에는 X 추출 비용도 더해야 한다. 원문 A는 추가 LLM 호출을 사용하지 않았다. 키는 환경 설정에서 읽고 결과에는 기록하지 않았다. 모든 원문 모델 응답·호출별 사용량·해시와 추론·평가 봉인을 보존했다.',
             '', '단계별 실행은 `core_preservation_run prepare / generate / infer / judge`, `core_preservation_quality`, `core_preservation_evaluate`, `core_preservation_report` 순서다. infer에 새 scratch 경로를 지정한다. 기존 실험 결과가 있으면 다시 쓰기를 거부한다. 재현에는 보존한 API 응답과 모델 해시를 사용하며 동일 API를 다시 호출할 필요는 없다.', '']
    (out/'README.md').write_text('\n'.join(text),encoding='utf-8',newline='\n')
    return {'conclusions':conclusion,'improves_C_on_both_means':successful,
            'changed_queries':changed_queries,'role_contributions':role_stats,
            'examples':examples,'API_by_kind':by_kind}


if __name__ == '__main__':
    result = main()
    (run.OUT/'report_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',
                                               encoding='utf-8',newline='\n')
