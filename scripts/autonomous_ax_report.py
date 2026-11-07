"""Render the autonomous-work checkpoint without inventing improvement trials."""
from statistics import mean

from ax_research.heldout import read
from scripts import autonomous_ax_gate as run


def pct(value):
    return '미확정' if value is None else f'{100*value:.2f}%'


def pp(value):
    return f'{100*value:+.2f}%p'


def main():
    out=run.OUT
    plan=read(out/'preregistration.json');status=read(out/'status.json')
    audit=read(out/'pending75_audit.json');checks=read(out/'policy_fixture_results.json')
    failures=read(out/'source_validation_failures.json');recover=read(out/'prefix_recovery_log.json')
    sensitivity=read(out/'observed_reviewer_scenarios.json');budget=read(out/'budget_followup.json')
    model={(r['condition'],r['metric']):r for r in plan['historical_models']}
    stability=read(run.client.old.OUT/'discovery.json')['ranking_stability']
    text=['# AX 자율 반복 연구의 정답 신뢰성 점검', '', '2026-11-07', '',
          '**현재 판정은 검증 보류다.** 성능 개선에 들어가기 전 평가자 점검에서 중요한 기준 불일치가 확인됐다. 사용자가 지정한 중단 조건을 적용해 개선 반복·최종 후보 선정·신규 독립 Test는 시작하지 않았다.', '',
          '## ① 연구 진행 현황', '',
          '| 단계 | 상태 | 근거 |', '|---|---|---|',
          '| 1. 정답 신뢰성 정리 | 진단 완료, 진입 조건 미통과 |75보류 원문·응답 및 정책 예시 검토 |',
          '| 2. 최대5회 개선 반복 | 미실행 | 평가 기준을 신뢰할 수 없어0회 |',
          '| 3. 최종 후보 동결 | 미실행 | 최종 후보를 선정하지 않음 |',
          '| 4. 신규40질문 Test | 미실행 | 질문·정답 생성과 예측 실행0건 |', '',
          '기존 기준 브랜치248524d4에서 별도 연구 브랜치를 만들었다. 과거6개 개발 질문의 F1@5·nDCG@10 관측 평균이 가장 높았던 E를 이번 비교 기준으로 먼저 등록했다. 이는 기존 자료에서의 선택이며, E가 실제로 가장 좋은 모델이라는 독립 검증은 끝나지 않았다. [사전 등록](preregistration.json)', '',
          '### 75건 보류 점검', '',
          '| 구분 | 사례 수 | 의미 |', '|---|---:|---|',
          f"| 판정 가능 후보 | {audit['classification_counts'].get('JUDGEABLE',0)} | 두 AI 등급은 같지만 정책 점검 실패로 정답 승인 보류 |",
          f"| 판단 기준 차이 | {audit['classification_counts'].get('CRITERION_DIFFERENCE',0)} | 기능 전이가 충분한지 또는 핵심/보조 작업 판단이 다름 |",
          f"| 원문 정보 부족 | {audit['classification_counts'].get('INSUFFICIENT_SOURCE',0)} | 새 검토에서 수행 근거가 부족하다고 판단 |",
          f"| 출력·근거 추가 확인 대기 | {audit['classification_counts'].get('EXPERT_REVIEW',0)} | 인용·출력 검사를 통과하지 못해 전문가 필요 여부도 확정하지 못함 |", '',
          '위 마지막49건은 전부 업무 전문가가 반드시 필요하다고 확정한 수가 아니다. 잘린 응답과 인용 필드 오류도 포함된 확인 대기 목록이다. 기존75건은 주 평가 정답에서 모두 보류로 유지했고 새 AI 일치12건을 성공적으로 해결된 정답으로 계산하지 않았다. 기존821개 판정도 덮어쓰지 않았다. [사례별 원문과 검토](pending75_audit.json)', '',
          f"75건×2제공자의150개 기대 응답 행 중 형식·인용 검사를 통과한 것은 {failures['valid_case_rows']}행이다. 출력이 잘려 완결 항목을 받지 못한 {failures['missing_received_items']}행과 잘못된 원문 인용 등을 따로 남겼다. 이번에 {len(recover['records'])}개 요청이 출력 한도에서 끝났으며, 완결된 JSON 항목30개만 원문 그대로 복구했다. 잘린 항목을 채우거나 API를 재요청하지 않았다. 이 출력 한도 설정도 이번 작업의 기술적 한계다. [실패 내역](source_validation_failures.json) · [복구 기록](prefix_recovery_log.json)", '',
          '## ② 반복 실험 성능 비교', '',
          '| 회차 | 변경 사항 | F1@5 | nDCG@10 | 결과 | 채택 |', '|---|---|---|---|---|---|']
    for i in range(1,6):text.append(f'| {i} | 미실행 | — | — | 정답 검증 진입 조건 미통과 | 없음 |')
    text += ['', '총 개선 실험0회다. API 검토 요청과 정책 예시 점검은 개선 실험 횟수에 포함하지 않았다. 성능 수치를 만들거나 미실행 실험을 실패한 실험으로 계산하지 않았다. [반복 상태](iterations.json)', '',
             '## ③ 최고 성능 모델', '',
             '기존 관측 평균 기준 비교 모델은 E다. 현재 자료로 신뢰성 있게 검증한 최고 모델과 새 최종 후보는 미확정이다. E의 추가 핵심 업무 추출 단계가 실제 개선 원인인지와 기존 기능 규칙에 잘 맞는 표현을 만든 효과인지는 분리되지 않았다.', '',
             '## ④ 기존 방식과 비교', '',
             '| 기존 방식 | F1@5 | nDCG@10 | 기존 Top-5 반복 Jaccard |', '|---|---:|---:|---:|']
    for c,name in [('A','원문 단독'),('B','동적3관점+원문'),('C','고정3관점+원문'),('E','핵심 보존3관점+원문')]:
        vals=[r['topk_jaccard'] for r in stability if r['condition']==c and r['k']==5]
        text.append(f"| {c} {name} | {pct(model[c,'F1@5']['mean'])} | {pct(model[c,'nDCG@10']['mean'])} | {pct(mean(vals)) if vals else 'LLM 반복 대상 아님'} |")
    text += ['', '성능 표는 기존6질문·기존AI 판정의 관측값을 보존한 참고 표다. 이번에 새로운 모델을 실행해 얻은 성능이 아니다. 반복 안정성은 기존8질문 생성3회에서 계산한 별도 집합 지표다. E86.81%는 사용자가 지정한90% 목표보다 낮았다.', '',
             '## ⑤ 객관적 검증', '',
             f"사전에 작성한 정책 예시8개를 GPT·Claude가 각각 판단했다. 총 {checks['passed']}/{checks['total']}개의 규칙 합치 검사를 통과했다. 이는 사람 Gold에 대한 정확률이 아니라, 사용자가 제시한 기준으로 만든 인공 예시의 일관성 검사다. [예시](policy_fixtures.json) · [실제 응답](policy_fixture_results.json)", '',
             '| 예시 | 관측된 문제 | 영향 |', '|---|---|---|',
             '| F03 현재 감지와 미래 예측 | Claude는 현재 임계치 초과 감지를 미래 고장 예측에2점으로 평가했다. 이유에는 예측 단계가 없다고 적었다. | 보조 작업을 핵심 작업에 충분한 전이로 취급할 위험 |',
             '| F05 수행 정보 부족 | GPT는 구현된 요약 업무가 불명확한 자료에0점·판정 가능을 선택했다. | 정보 부족과 무관을 혼동할 위험 |',
             '| F06 사람 승인 | Claude 응답이 인용 검사를 통과하지 못했다. | 의미 판단 이전에 원문 근거 확인이 필요 |', '',
             '새 평가에서도 Problem의 필요를 실제 수행 증거로 쓰거나 인용 필드를 잘못 연결한 응답이 나왔다. 문제를 더 자주 호출해 다수결로 맞추지 않았다. 사람이 핵심 기능 전이와 보조 기능의 경계, 원문 부족 시 보류 기준을 확인해야 하는 상태다.', '',
             '### 남은 정답 불확실성의 영향', '',
             '| 분석 | E−C F1@5 사례 범위 | E−C nDCG@10 사례 범위 |', '|---|---:|---:|---:|']
    ranges={}
    for label,file in [('관측된 AI 점수 선택지','observed_reviewer_scenarios.json'),('보류에0~3점을 허용한 넓은 가정','sensitivity_witnesses.json')]:
        data=read(out/file);row={}
        for metric in ('F1@5','nDCG@10'):
            values=[w['E_minus_C'] for w in data['witnesses'] if w['metric']==metric]
            row[metric]=f'{pp(min(values))} ~ {pp(max(values))}'
        ranges[label]=row
        text.append(f"| {label} | {row['F1@5']} | {row['nDCG@10']} |")
    text += ['', '기존821개 점수는 고정하고75개 보류에 다른 점수를 적용한4,096개 가정 중 실제 계산된 사례들이다. 관측 AI 점수 선택지 분석에서도 E와 C의 순서가 반대로 나오는 가정이 있었다. AI 점수 선택지가 업무 전문가에게 타당하다고 승인된 것은 아니다.', '',
             '위 범위는 실제 모델의 측정 성능, 전체 가능한 값의 정확한 최솟값·최댓값, 통계적 신뢰구간이 아니다. 4,096개 가정을4,096개 독립 질문으로 취급하지 않았다. 원래 질문 수는8개이며, 양성 사례가0개가 될 수 있는 가정에서는 F1 평가 대상 여부도 불확실하다. 원래 정답표에 가정 점수를 기록하지 않았다. [관측 점수 민감도](observed_reviewer_scenarios.json) · [넓은 가정](sensitivity_witnesses.json) · [수학적 외곽 범위](nDCG_outer_bounds.json)', '',
             '새 후보가 없어 개선폭의 paired bootstrap95% 신뢰구간과 신규 Test 성능은 평가하지 않았다. 남은 불확실성의 수치 영향은 확인했지만, 평가 기준의 독립 검증이 통과되지 않아 개선 실험의 진입 조건은 충족되지 않았다.', '',
             '## ⑥ 실패 원인 분석', '',
             '- 부분 작업이 핵심 목적을 충분히 충족하는지에 대한 판정이 아직 일관되지 않는다.',
             '- 원문의 실행 기능과 Problem에 적힌 필요, 사용자가 원하는 기능을 혼동하는 응답이 남았다.',
             '- 정확한 인용과 의미적으로 충분한 근거는 다르다. 원문을 그대로 인용해도 현재 감지를 미래 예측으로 높게 평가할 수 있었다.',
             '- 이번 출력 구조는 일부 응답을 한도 내에 끝내지 못했다. 복구 가능한 완결 항목만 읽었고 누락은 보류로 남겼다.',
             '- 기존112사례·8개발 질문은 여러 차례 검토됐다. 기존 독립 Test15개를 이번 튜닝에 쓰지 않았으며 새로운 독립 Test도 만들지 않았다.', '',
             '## ⑦ 연구 목표 달성 여부', '',
             '**검증 보류**로 판정한다. 최대5회 반복 중0회 진행했으며, 성능 개선을 못한5개 실험이 있다는 뜻은 아니다. 정답 신뢰성 진입 단계에서 중단했다.', '',
             '| 사전 목표 | 이번 상태 |', '|---|---|',
             '| 기존 최고 기준보다 F1@5 +5%p | 새 후보 미실행 |',
             '| nDCG@10 +3%p | 새 후보 미실행 |',
             '| 두 paired bootstrap95% 하한 >0 | 새 후보 미실행 |',
             '| Top-5 Jaccard≥90% | 새 후보 미실행, 기존E는86.81% |',
             '| 주요 정답 독립 검증 | 미충족 |',
             '| 새로운 독립 Test에서 재현 | 미실행 |', '',
             '이 수치는 사용자가 지정한 이번 연구의 목표이며 학계의 보편적인 합격 기준으로 제시하지 않는다.', '',
             '## ⑧ 논문 활용 가능성과 재개 순서', '',
             '책임님께 보고할 수 있는 것은 기존 개발 결과, 기준 해석의 불일치, 원문 근거 오류, 정답에 따른 순위 비교의 민감도다. E가 새로운 업무에서 더 정확하다는 주장이나 최종 논문 모델 선정은 아직 뒷받침되지 않는다.', '',
             '1. [75건 검토용 자료](expert_review_packet.jsonl)에서 실제 수행 근거와 핵심/보조 기능 경계를 업무 담당자 등이 확인한다. 파일에는 추천 순위·모델별 점수 없이 빈 사람 검토 칸만 있다. 현재 사람 검토가 끝난 자료는 아니다.',
             '2. 현재 감지/미래 예측, 핵심 기능/입력 준비, 정보 부족/무관의 판정 정책을 확정하고 같은 정책으로 개발 정답의 호환성을 점검한다.',
             '3. 출력·인용 검사를 보완하고 평가자 정책 점검을 통과한 뒤 개발 기준 모델을 확정한다. 이후 개선 실험을 최대5회 시작한다. 같은 개발 질문을 반복해 본 이력은 계속 기록한다.',
             '4. 개발 후보가 모든 조건을 충족하면 코드·모델·프롬프트·가중치·정답 정책을 동결한다. 그 뒤 별도 작성자가 이전 개발/15Test 결과를 보지 않고 신규40질문을 설계하고 중복을 확인한다.',
             '5. 최종 Test의 예산과4,480쌍 정답 검증을 준비한 뒤 한 번 평가한다. Test 결과로 모델을 다시 튜닝하지 않는다.', '',
             '## ⑨ GitHub와 비용', '',
             '- 브랜치 `research/autonomous-ax-study-20261107`',
             f"- API {status['API_calls']}회, 사용량 기준 추정 ${status['API_cost']['estimated_received_usd']}, 미확정 비용 예약 ${status['API_cost']['unconfirmed_reserved_usd']}. 이번 Work 상한$2 이내다.",
             '- OpenAI `gpt-6-luna`, Anthropic `claude-haiku-4-5-20251001`을 사용했다. 사람 Gold는 만들지 않았다.',
             '- [최종 상태](final_status.json) · [원문 요청·응답과 사용량](api_ledger.json) · [자동 검사](tests.json) · [보존 검사](preservation_check.json) · [재개 방법](REPRODUCE.md)',
             f"- 현재의 상세2제공자 형식을4,480쌍에 단순 비례한 비용 참고값은 약${float(budget['same_schema_4480_pairs_linear_cost_reference_usd']):.2f}다. 잘린 출력이 포함된 측정값이어서 완전 평가의 정확한 비용이나 상한이 아니다. 평가 형식을 확정한 뒤 다시 견적해야 한다. 이번 중단의 주원인은 잔액이 아닌 평가 신뢰성이다. [비용 참고](budget_followup.json)",
             '- [OpenAI 단가](https://developers.openai.com/api/docs/models/gpt-6-luna) · [Claude 단가](https://platform.claude.com/docs/en/about-claude/pricing)', '']
    text += ['프로그램 자동 검사212개가 통과했다. 코드 검사는 원본 보존·잘린 응답 처리·점수 대응·가정 계산을 확인했다. 평가자 정책 예시의13/16 통과 결과는 별도로 보존했다. [검토 기준 설명](RUBRIC.md) · [비밀정보 검사](secret_scan.json)', '']
    (out/'README.md').write_text('\n'.join(text),encoding='utf-8',newline='\n')


if __name__=='__main__':main()
