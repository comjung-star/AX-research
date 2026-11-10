import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/claude-difference-20261110/human-review'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    differences = read(ROOT/'docs/claude-difference-20261110/disagreements.json')
    recommendations = read(ROOT/'docs/independent-cross-validation-20261110/recommendations.json')
    facts = read(ROOT/'docs/independent-cross-validation-20261110/case-facts.json')
    cases = [row for row in differences if (int(row['claude'])>=2)!=(int(row['openai'])>=2)]
    assert len(cases)==58
    lines = ['# 직접 판단하는 Claude 교차검증 검토표', '',
        '검토 대상: 유용한지에 대한 답이 달랐던 58건. 기존 AI 점수는 수정하지 않습니다. 아래의 내 판단은 별도 사람 검토 기록입니다.', '',
        '## 먼저 볼 결과', '',
        '| 항목 | 결과 |', '|---|---|',
        '| 평가 | 차집합 152건 전부 완료 |',
        '| B만 추천한 유용한 사례 | 76건 중 31건 |',
        '| A만 추천한 유용한 사례 | 76건 중 17건 |',
        '| 질문 평균 B의 이점 | +4.96%p (OpenAI: +9.77%p) |',
        '| 95% 오차 범위 | +0.84~+9.34%p |',
        '| 질문 20개의 결과 | 개선 10 · 악화 4 · 동률 6 |',
        '| 두 AI의 유용 여부 일치 | 94/152건, 61.84% |',
        '| 매우 엄격한 기준: 3점만 유용 | −0.13%p, 오차 범위 −1.89~+1.69%p → 우열 불확실 |', '',
        '전체 추천의 절대 정답률은 알 수 없습니다. 공통 추천은 평가하지 않았지만, 두 방법의 차이는 계산할 수 있습니다.', '',
        '## 판단하는 방법', '',
        '1. 질문을 읽고 어떤 문제가 해결되어야 하는지 확인합니다.',
        '2. 사례가 실제로 한 일을 읽습니다. 같은 업종인지보다 해결 동작이 실질적으로 참고되는지 봅니다.',
        '3. 두 AI의 이유를 비교합니다. 질문에 없는 원인을 가정하거나 사례에 없는 기능을 보탠 부분이 있는지 확인합니다.',
        '4. 내 점수와 이유를 남깁니다. A/B 소속은 점수에 영향을 주지 않도록 마지막에 확인합니다.', '',
        '| 내 점수 | 판단 기준 |', '|---|---|',
        '| 3 | 문제와 해결 방식이 매우 비슷해 직접 참고 가능 |',
        '| 2 | 분야가 달라도 실제 수행된 해결 동작을 실질적으로 참고 가능 |',
        '| 1 | 일부 공통점은 있지만 적용 연관성은 낮음 |',
        '| 0 | 관련이 없거나 확인된 사실로 유용성을 뒷받침하기 어려움 |',
        '| 판단 보류 | 사실이 없거나 모순돼 판단 자체가 불가능 |', '',
        '근거는 기존 평가에 제공한 구조화 요약입니다. 출처 링크가 있다고 원문 전체를 새로 검증한 것은 아닙니다. 영어 자료는 원래 표현을 보존했습니다.', '',
        '## 질문별 검토 순서', '', '| 질문 | 판단이 달랐던 건수 |', '|---|---:|']
    counts = Counter(row['question_id'] for row in cases)
    for question, count in sorted(counts.items()):
        lines.append(f'| {question} | {count} |')
    review_rows = []
    for number, row in enumerate(cases,1):
        question, case = row['question_id'], row['case_id']
        fact = facts[case]
        claude, openai = row['claude_evidence'], row['openai_evidence']
        affiliation = 'A만 추천' if case in recommendations[question]['A'] else 'B만 추천'
        useful = lambda grade:'유용' if int(grade)>=2 else '유용하지 않음'
        lines += ['', '---', '', f'## 검토 {number:02d} / 58 · {question}', '',
            '### 해결하려는 문제', '', recommendations[question]['question'], '',
            f'### 사례: {case}', '',
            f'- 원래 문제: {fact["problem"]}', f'- 수행 업무: {fact["task"]}',
            f'- 적용 상황: {fact["context"]}', f'- 실제 구현: {fact["implementation"]}',
            f'- 관측 성과: {fact["outcome"]}', '',
            f'### OpenAI: {row["openai"]}점 · {useful(row["openai"])}', '',
            openai.get('brief_bridge','기록 없음'), '',
            f'적용할 때 둔 가정: {openai.get("assumption","기록 없음")}', '',
            f'### Claude: {row["claude"]}점 · {useful(row["claude"])}', '',
            claude['reason'], '', f'인용 위치: `{claude["evidence_field"]}`', '',
            '> '+claude['evidence_quote'].replace('\n','\n> '), '',
            '### 내 판단', '',
            '- 내 점수: □ 0  □ 1  □ 2  □ 3  □ 판단 보류',
            '- 사례에서 실제로 확인한 해결 동작:',
            '- 질문의 문제와 연결되는 이유 / 연결되지 않는 이유:',
            '- 원문을 더 확인할 부분:', '',
            '<details>', '<summary>추천 소속과 출처 확인</summary>', '',
            f'{affiliation}. [출처]({fact["source_url"]})', '',
            f'근거 위치: `{fact["evidence"].get("evidence_locator","UNKNOWN")}`', '',
            '</details>']
        review_rows.append({'검토번호':number,'질문ID':question,'사례ID':case,'질문':recommendations[question]['question'],'실제구현':fact['implementation'],'OpenAI점수':row['openai'],'OpenAI이유':openai.get('brief_bridge',''),'OpenAI가정':openai.get('assumption',''),'Claude점수':row['claude'],'Claude이유':claude['reason'],'내점수':'','내판단이유':'','추천소속':affiliation,'출처':fact['source_url']})
    (OUTPUT/'직접판단_58건_검토표.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    import csv
    with (OUTPUT/'직접판단_58건_기록표.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(review_rows[0]))
        writer.writeheader()
        writer.writerows(review_rows)
    print('Created 58 review entries and editable CSV')


if __name__ == '__main__':
    main()
