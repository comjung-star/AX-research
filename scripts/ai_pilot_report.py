"""Build an honest reader-facing pilot report and question list from sealed data."""
import json

from scripts.claude_blind_questions import OUT


def main():
    data = json.loads((OUT / 'evaluation.json').read_text(encoding='utf-8'))
    audit = json.loads((OUT / 'audit.json').read_text(encoding='utf-8'))
    questions = json.loads((OUT / 'claude_authored_questions.json').read_text(encoding='utf-8'))['questions']
    question_text = ['# Claude가 작성한 새 업무 질문40개', '', 'AI가 만든 가상 업무 시나리오이며 실제 현업 제출 또는 사람 검토 질문이 아니다. 기존 사례·정답·성능을 보내지 않은 별도 요청에서 한 번 생성했고, 성능에 맞춰 수정·제외하지 않았다.', '']
    for row in questions:
        question_text.extend([f"## {row['query_id']} · {row['sector']}", '', row['business_problem'], ''])
    with (OUT / 'questions.ko.md').open('x', encoding='utf-8') as target:
        target.write('\n'.join(question_text))
    lines = ['# 새 Claude 질문40개를 사용한 AI 예비 검증 결과', '',
             '질문 생성부터 고정된 네 방법의 추천·AI 채점·재계산까지 실제 수행했다. 사람 검토자가 없어 사람 Gold는 만들지 않았다. 질문 작성은 Claude Sonnet5.5, 관점 생성은 기존 GPT-6 Luna, 관련성 평가는 Claude Haiku5.5와 Gemini3.1Flash-Lite다. 평가 AI는2모델·2제공사이며 작성자와 한 평가자는 Anthropic을 공유한다.', '',
             '## 실제 수행 범위', '',
             '-10개 업무 분야×4개씩40질문. 기존38개 개발 질문과 정규화 정확 중복0개. 문자 유사도 점검은 의미적 신규성이나 현실성의 인간 인증이 아니다.',
             '-질문×112사례=4480쌍을 두 평가자가 각각 판정해8960개 원점수를 저장했다. 모델명·추천 순위·과거 정답을 채점 요청에 제공하지 않았다.',
             '-동결한 원문 Dense/기존 E/새 원문 토큰/새 원문+관점 토큰을3반복해480개 순위를 생성했다. 관점350개가 실제 생성됐고10개 슬롯은 MISSING으로 보존했다.',
             '-추론에서 네트워크와 정답/검토 경로 접근을 차단했다. 예측 봉인 뒤 별도 평가를 실행했다. 기존 Test15와 기존 정답·모델·가중치는 변경하지 않았다.', '',
             '## 같은 평가자 기준에서의 비교', '',
             '| 평가자 | 양성 질문 수 | 방법 | F1@5 | nDCG@10 |', '|---|---:|---|---:|---:|']
    for provider, name in [('claude', 'Claude'), ('gemini', 'Gemini')]:
        result = data['results'][provider]
        for system in ('Dense', 'E', 'TokenSingle', 'TokenMulti'):
            row = result['summary'][system]
            lines.append(f"|{name}|{row['F1@5']['queries']}|{system}|{row['F1@5']['mean'] * 100:.2f}%|{row['nDCG@10']['mean'] * 100:.2f}%|")
    lines += ['', '각 평가자는40질문·4480쌍 전부를 판정했다. Claude는12질문, Gemini는38질문에 관련 사례가 있다고 판단했다. 양성0개 질문의 F1/nDCG를0으로 채우지 않아 평균 분모가 다르다. 따라서 Claude와 Gemini 행의 절대 점수를 전후 변화처럼 비교하지 않는다. 각 평가자 안에서 같은 질문에 대한 방법 차이를 비교한다.', '',
              '## 무엇이 확인됐나', '',
              '새 관점 토큰 방식은 두 평가자 모두에서 기존 E보다 F1/nDCG가 높았고, 사전 지정6대비의 Bonferroni 보정 구간에서도 이4개 E대비 차이의 하한이0보다 높았다. 그러나 Dense대비는 Claude에서 낮고 Gemini에서 높아 결론이 일치하지 않았다. Gemini의 nDCG대비만 보정 구간 하한>0이었고 Dense대비 F1은 두 평가자 모두 미확정이다. 관점 추가의 원문 토큰 대비 효과는 두 지표 모두 확정되지 않았다. 사람 Gold나 현실 업무에서의 보편적 우위라고 주장하지 않는다.', '',
              f"두 모델의 이진 합의는{data['consensus_judged']}/4480쌍이고 {data['consensus_abstain']}쌍은보류다. 한 질문이라도 필요한 판정이 빠지면 전수 F1/nDCG에서 제외하는 원래 정책을 지켰다. 완전 합의 질문2개는 양성이 없어 합의 기준의 F1/nDCG를 계산할 수 없다. 이견을 임의 확정하거나 무관으로 채워 합의 성능을 만들지 않았다.", '',
              '## 평가 신뢰성과 오류 처리', '',
              '초기 채점의 생각 토큰 한도 소진·일부 사례만 반환 문제는 중단하고 원본을 보존했다. 전체112위치 구조화 응답으로 기술적 형식을 고친 뒤 사전 점검을 통과하고 실행했다. 기존 정상 판정을 좋은 결과가 나올 때까지 재생성하지 않았다. HTTP429거절7건만 별도 기록 후1회 복구했다. 상세는 ../AI_PILOT_AMENDMENT.ko.md다.',
              '단순한 가상 통제6개에서는 Claude6/6, Gemini5/6이 기대한 이진 판정을 했다. Gemini는 답변 생성 없이FAQ검색만 수행하는 사례를 답변 초안 요구에 충분한 핵심 전이로 높게 평가했다. 이는 사람 검수 부재와 핵심/보조 기능 경계의 불확실성을 보여준다. 통제 통과도 실제 정답 정확성 인증은 아니다.',
              f"원문 인용 자동 검사에서는 핵심 추출 근거{len(audit['invalid_core_literal_evidence'])}건, 관점 source_quote{len(audit['invalid_perspective_source_quotes'])}건의 문자 불일치를 발견했다. 원본을 고치거나 재생성하지 않고 품질 한계로 남겼다. 문자 일치와 의미 보존은 다른 검사다.", '',
              '## 비용과 재현', '',
              f"사용량 기반 비용 추정은 ${audit['known_usage_estimate_usd']:.6f}, 실패·미확정 요청 예약을 유지한 보수 합계는 ${audit['conservative_total_usd']:.6f}로 전체2달러 상한 이내다. 실제 카드 청구 명세 금액은 아니다. 질문 생성 비용은별도 영수증 기준$0.097452다.",
              '원본 AI판정8960행,112사례가 모두 포함된480순위, 각 평가자의6대비 총12개 보정 재표집 계산을 별도 실행에서 다시 확인했다. 검증 파일은 verification.json이다. 새 검증 코드와 준비 단계의 관련 검사25개가 통과했다. 코드 검사가 AI의 정답성까지 입증하는 것은 아니다.', '',
              '## 현재 판단', '',
              '사람 없이 AI 예비 검증을 실제로 진행할 수 있었고 새 질문에서 기존 E보다 좋은 결과를 얻었다. 그러나 단순 Dense를 안정적으로 이겼거나 다중관점의 기여가 입증됐다는 결론은 얻지 못했다. 평가자 이견342건과 평가 가능한 질문 수 차이를 숨기지 않는다. 이40개에 맞춰 알고리즘이나 정답을 바꾸면 이후에는 개발 자료로 분류해야 한다. 사람 검토가 없으므로 결과는 AI-Silver 조건부로 보고한다.', '',
              '원본: author_preregistration.json, author_response.json, author_receipt.json, author_screen.json, runtime/execution.json, predictions.json, blind_review_v2/, blind_review_429_recovery/, ai_consensus.json, evaluation.json, audit.json, verification.json. 질문 원문은 questions.ko.md다. 실행 스크립트는 scripts/claude_blind_questions.py, ai_pilot_review_v2.py, ai_pilot_generation.py, ai_pilot_infer.py, ai_pilot_evaluate.py 및 verify_ai_pilot.py다. 유료 호출 스크립트는 기존 실행 경로가 있으면 재호출을 거부한다.']
    with (OUT / 'README.ko.md').open('x', encoding='utf-8') as target:
        target.write('\n'.join(lines) + '\n')
    print(json.dumps({'report': 'README.ko.md', 'questions': 'questions.ko.md', 'human_gold': False}))


if __name__ == '__main__':
    main()
