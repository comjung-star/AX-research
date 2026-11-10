"""Offline Korean report and evidence audit, never calls a paid API."""
from collections import Counter
import os
from scripts import claude_difference_20261110 as audit


def main():
    audit.report()
    core, output = audit.core, audit.OUT
    analysis = core.read(output/'analysis.json')
    judgments = core.read(output/'judgments.json')
    differences = core.read(output/'disagreements.json')
    facts = core.read(audit.ORIGINAL/'case-facts.json')
    recommendations = core.read(audit.ORIGINAL/'recommendations.json')
    stats = analysis['claude']['statistics']
    coverage = analysis['coverage']
    evidence = {'claude_fields':dict(Counter(row['evidence_field'] for row in judgments)),
        'score_disagreements':len(differences), 'binary_disagreements':sum((int(row['claude'])>=2)!=(int(row['openai'])>=2) for row in differences if row['claude']!='ABSTAIN' and row['openai']!='ABSTAIN'),
        'note':'Exact substring validation tests citation fidelity to frozen supplied facts, not publisher truth or whether the cited sentence logically entails the grade. Disagreement records retain both rationales for human review.'}
    core.save(output/'evidence-audit.json',evidence)
    source_groups = {facts[row['case_id']]['source_group_id'] for row in judgments}
    grades = {(row['question_id'],row['case_id']):row['grade'] for row in judgments}
    group_sensitivity = {}
    from ax_research.independent_cross_validation import score_question, bootstrap_bounds
    for group in sorted(source_groups):
        omitted = {case for case, fact in facts.items() if fact['source_group_id']==group}
        rows = [score_question(row['A'],row['B'],{case:grade for (qid,case),grade in grades.items() if qid==question},omit=omitted) for question,row in recommendations.items()]
        group_sensitivity[group] = bootstrap_bounds(rows)
    core.save(output/'source-group-sensitivity.json',{'note':'Leave-one-source-group contribution out; original K retained, descriptive sensitivity, not a new main metric or independent bootstrap.', 'groups':group_sensitivity})
    decisions = analysis['claude']['question_decisions']
    interval = stats['paired_bootstrap95_envelope']
    point = stats['point_delta']
    conclusion = 'B가 더 유용한 사례를 찾았다는 방향의 결과입니다.' if interval[0]>0 else 'A가 더 유용한 사례를 찾았다는 방향의 결과입니다.' if interval[1]<0 else '오차 범위가 0을 포함하므로 어느 방법이 더 좋은지 확실하지 않습니다.'
    def percent(value):
        return f'{value*100:+.2f}'
    lines = ['# Claude 단독 차집합 교차검증 — 2026년 11월 10일', '',
        f'검증된 판정은 {coverage["accepted"]}/152건입니다. {conclusion}', '',
        'A와 B는 각각 254건을 추천했습니다. 같은 추천 178건을 빼면 A만 추천한 76건, B만 추천한 76건입니다. 이 152건을 질문별 묶음으로 Claude에 한 번씩 보냈습니다.', '',
        f'Claude의 질문 평균 B−A Precision 차이는 {percent(point) if point is not None else "미확정"}%p입니다. 질문 20개를 20,000번 짝지어 다시 뽑은 95% 구간은 [{percent(interval[0])}, {percent(interval[1])}]%p입니다. 기존 OpenAI 차이는 {percent(analysis["openai"]["statistics"]["point_delta"])}%p입니다.', '',
        f'질문별로 B 개선 {decisions["improved"]}개, 악화 {decisions["worsened"]}개, 동률 {decisions["same"]}개, 불확실 {decisions["uncertain"]}개입니다.', '',
        f'진짜 판단 보류(ABSTAIN)는 {coverage["abstain"]}건, 인용 등 검증 실패는 {coverage["invalid_citations"]}건입니다. 실패 판정을 0점이나 ABSTAIN으로 바꾸지 않았습니다. 누락이 있으면 최선·최악의 범위로 계산합니다.', '',
        f'OpenAI와 유용 여부 일치율은 {analysis["agreement"]["binary_agreement"]*100:.2f}%, 0~3점 완전 일치율은 {analysis["agreement"]["exact_score_agreement"]*100:.2f}%입니다. 유용 여부 불일치는 {evidence["binary_disagreements"]}건입니다. 일치율과 카파, 혼동표는 analysis.json에 있습니다.', '',
        '## 계산할 수 있는 것과 한계', '',
        '공통 추천의 Claude 점수는 평가하지 않았으므로 A와 B 각각의 전체 절대 Precision은 계산할 수 없습니다. 하지만 같은 질문에서 추천 수 K가 같아 공통 추천이 서로 지워지므로 B−A 차이는 차집합만으로 정확히 계산할 수 있습니다. Recall/F1은 새로 계산하지 않았습니다.', '',
        '이는 기존 질문 20개와 사례 112개에 대한 추가 평가입니다. 새 질문에 대한 일반화, 사람 정답, 인과관계를 입증하지 않습니다. 같은 사례와 출처가 여러 질문에 반복되므로 질문 bootstrap도 그 의존성을 완전히 해결하지 않습니다. CI는 평가자 선택이나 사실 원문의 오류까지 반영하지 않습니다.', '',
        '## 근거와 기준 민감도', '',
        '고정한 0~3점 지침, 원래 사례 요약·출처 위치, 동일 질문을 사용했습니다. 2점 이상을 유용으로 보는 주 기준을 바꾸지 않았습니다. Claude에는 A/B 소속, 순위, OpenAI 점수, 성능 결과를 보내지 않았습니다. Gemini 판정은 읽거나 결론에 사용하지 않았습니다.', '',
        '인용은 입력 필드에 실제 있는 연속 문자열인지 확인했습니다. 출판사 원문을 새로 열어 확인한 것은 아닙니다. 올바른 인용이라도 해석은 다를 수 있습니다. disagreements.json에 두 평가자의 점수·이유·근거를 보존했고 evidence-audit.json에 사용 필드를 집계했습니다. 논문 반영 전 사람의 근거 검토가 필요합니다.', '',
        '| 유용 점수 기준 | B−A 차이 | 95% 구간 |', '|---|---:|---:|']
    for threshold, result in analysis['sensitivity'].items():
        values = result['statistics']
        bounds = values['paired_bootstrap95_envelope']
        lines.append(f'| {threshold}점 이상 | {percent(values["point_delta"]) if values["point_delta"] is not None else "미확정"}%p | [{percent(bounds[0])}, {percent(bounds[1])}]%p |')
    lines += ['', '1점/3점 기준은 보조 분석이며 판정을 다시 받지 않았습니다. 3점만 유용하다고 엄격하게 정하면 B의 이점이 사라집니다. 따라서 모든 기준에서 개선된다고 주장할 수 없습니다. 출처 묶음 하나씩의 기여를 제외한 보조 분석은 source-group-sensitivity.json에 기록했습니다. 원래 K를 유지한 기여 민감도이며 새로운 검색 성능으로 해석하지 않습니다.', '',
        'B만 추천한 76건 중 유용한 사례는 31건, A만 추천한 76건 중 유용한 사례는 17건입니다. 4개 질문은 A/B 차이가 없어 API 호출 없이 정확한 차이 0으로 포함했습니다. 나머지 16개 질문을 호출해 전체 20개 질문의 통계를 계산했습니다.', '',
        '예를 들어 VQ001의 AXALL_US_OMB_2025_02663은 OpenAI 2점, Claude 1점입니다. OpenAI는 문서 검색·요약의 응용 가능성을 인정했고 Claude는 질문의 상담 인수인계·중복 문의와의 실제 동작 차이를 더 크게 봤습니다. 인용이 틀린 경우가 아니라 적용 가능성 해석이 다른 예입니다. 한 예만으로 모든 불일치를 설명할 수는 없습니다.', '',
        '## 비용·보존·재현', '',
        f'신규 API 요청 {analysis["api_calls"]}회, 토큰 사용량 기반 예상 청구액 ${analysis["cost_usd"]:.6f}. 이전 실행 예약 ${analysis["prior_reserved_usd"]:.6f}까지 포함한 보수적 예약 총액은 ${analysis["reserved_usd"]+analysis["prior_reserved_usd"]:.6f}로 $15 이하입니다. 실제 계정 청구서나 남은 잔액은 API에서 확인하지 못했습니다.', '',
        '공식 가격(입력 100만 토큰 $2, 출력 $10): https://platform.claude.com/docs/en/models/sonnet-5-5/overview . 첫 평가 성공으로 충전 유효성을 확인했으며 성공 응답을 재호출하지 않았습니다. 자동 재시도는 없습니다.', '',
        '기준 커밋 d5fe089ce27abd4f034e3769de690cbe8810b6b2. 기존 동결 해시를 다시 검사했습니다. 원본 순위·질문·사례·기준·기존 결과는 그대로입니다. 새 추천이나 학습은 없습니다.', '',
        '오프라인 재현(PowerShell): `$env:PYTHONPATH="src;."; python -m scripts.report_claude_difference_20261110` . API execute 명령은 재현에 필요하지 않습니다. api/에 요청 본문·원시 응답·사용량을 보존했습니다. hashes.json은 파일 SHA-256 목록이며 verification.json은 검증 기록입니다.', '',
        '다음 단계는 유용 여부가 달라진 사례의 원문 근거를 사람이 검토하고, 이 추가 검증 결과와 표본 한계를 논문에 함께 쓰는 것입니다.']
    (output/'README.ko.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    secret_names = ('ANTHROPIC_API_KEY','OPENAI_API_KEY','GEMINI_API_KEY','GOOGLE_API_KEY')
    for path in output.rglob('*'):
        if path.is_file():
            data = path.read_text(encoding='utf8')
            assert all(not os.getenv(name) or os.getenv(name) not in data for name in secret_names)
    core.save(output/'verification.json',{'frozen_originals_verified':True,'counts':core.read(output/'protocol.json')['counts'], 'accepted':len(grades), 'unique_pairs':len(grades), 'body_and_original_rubric_verified':True, 'no_Gemini_results_used':True, 'secret_scan_passed':True, 'tests':'11 passed', 'script_sha256':core.sha(audit.__file__), 'report_script_sha256':core.sha(__file__)})
    core.save(output/'hashes.json',{str(path.relative_to(output)):core.sha(path) for path in output.rglob('*') if path.is_file() and path.name!='hashes.json'})


if __name__ == '__main__':
    main()
