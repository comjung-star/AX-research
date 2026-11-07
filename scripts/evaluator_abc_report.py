"""Build a factual Korean report from completed evaluator artifacts."""
from collections import Counter
from decimal import Decimal
from statistics import mean
import json
import platform
import subprocess
import sys
from ax_research.heldout import read,write,sha
from scripts import evaluator_abc as run


def main():
    out=run.OUT
    final=out/'final-review'
    comparison=read(final/'benchmark_recovered_analysis.json')
    pending=read(final/'pending75_review.json')
    versions=read(final/'evaluation_versions.json')
    cost=run.aggregate_cost()
    technical=[]
    for provider in run.CAPS:
        old=read(out/provider/'pending_results.json')['records']
        new=read(out/provider/'recovery-v2'/'pending_recovered_results.json')['records']
        recover=read(out/provider/'recovery-v2'/'local_recovery_log.json')['records']
        technical.append({'provider':provider,'old_counts':dict(Counter(r['status'] for r in old)),
            'new_counts':dict(Counter(r['status'] for r in new)),
            'recovered_decision_rows':sum(a['status']=='UNJUDGED' and b['status']!='UNJUDGED' for a,b in zip(old,new)),
            'local_component_recoveries':sum(r.get('new_failure','x') is None for r in recover),
            'previously_unexecuted_judge_calls':sum(r['new_API_call'] for r in recover),
            'remaining_failures':dict(Counter(r['failure'] for r in new if r.get('failure'))),
            'independent_core_execution':dict(Counter(r['case_core']['data'].get('execution')
                for r in new if r.get('case_core') and r['case_core'].get('valid'))),
            'input_tokens':sum(r.get('usage',{}).get('input_tokens',0) for r in cost['calls'] if r['provider']==provider),
            'output_tokens':sum(r.get('usage',{}).get('output_tokens',0) for r in cost['calls'] if r['provider']==provider),
            'cost_usd':str(sum((Decimal(r.get('cost_usd','0')) for r in cost['calls'] if r['provider']==provider),Decimal()))})
    old49={r['id'] for r in read(run.PRIOR/'pending75_audit.json')['records'] if r['classification']=='EXPERT_REVIEW'}
    technical_summary={'by_provider':technical,'prior_invalid_rows':57,'prior_valid_rows':93,
        'same_150_expected_pairs_but_different_evaluator_and_batching':True,
        'old49_followup':dict(Counter(r['category'] for r in pending['records'] if r['id'] in old49)),
        'known_fixes':['Single item per question/case request','Small independent query/case extraction',
            'Literal T/C anchor IDs with field and character span','Unchanged exact quote relocation Task/Context',
            'Complete single fenced JSON followed by prose recovery without synthesis',
            'One bounded technical retry; no semantic/unfavorable-grade reroll; uncertain call cost held',
            'Original raw replies and failed interpretations retained'],
        'still_unresolved':['LLMs interpret described Task as unconfirmed execution too often',
            'Problem anchors still appear in some decisions and are rejected',
            'Exact source anchor existence does not establish semantic entailment'],
        'paid_semantic_rerolls':0}
    write(out/'technical_summary.json',technical_summary)
    selected=read(out/'method_selection.json')
    gate={'passed':False,'policy_controls_passed':False,'source_semantics_verified':False,
        'unresolved_retained_not_forced':True,'same_frozen_predictions_used':True,
        'full_query_point_metrics_available':False,'human_approval_obtained':False,
        'reason':'No evaluator passed all fresh controls. Selected B has excessive false abstention; literal/ID checks do not prove functional judgment correctness.',
        'algorithm_iterations_executed':0,'new_Test_executed':False}
    write(out/'entry_gate.json',gate)
    write(out/'iterations.json',{'executed':0,'maximum':5,'gate':gate,
        'records':[{'iteration':i,'status':'NOT_STARTED','hypothesis':None,'performance':None,
                    'adopted':False,'reason':'Label reliability gate not passed'} for i in range(1,6)]})
    write(out/'environment.json',{'python':sys.version,'platform':platform.platform(),
        'packages':subprocess.run([sys.executable,'-m','pip','freeze'],capture_output=True,text=True).stdout.splitlines(),
        'paid_API_models':run.transport.PROVIDERS,'BGE_M3_or_BM25_reexecuted':False})
    tests=read(out/'tests_final_v2.json');assert tests['returncode']==0
    passed=int(tests['stdout'].split(' passed')[0].split()[-1])
    status={'work':'Evaluator reliability ABC comparison and pending75 diagnostic review',
        'branch':'research/evaluator-reliability-abc-20261107','base_commit':'76b1cc93a859086d3f07dfe9b315ef6475a58cd0',
        'stages':{'1_failure_audit':'COMPLETED','2_ABC_comparison':'COMPLETED_GATE_FAILED',
            '3_technical_recovery':'COMPLETED_WITH_REMAINING_SOURCE_SEMANTIC_FAILURES',
            '4_pending75_review':'COMPLETED_DIAGNOSTIC_NOT_APPROVED',
            '5_reliability_gate':'NOT_PASSED','6_algorithm_iterations':'NOT_STARTED'},
        'selected_diagnostic_evaluator':selected['method'],'approved_resolutions':0,
        'pending_primary':75,'provisional_agreements':pending['agreement_proposals'],
        'human_approved':False,'human_gold':False,'algorithm_iterations':0,'new_independent_Test_executed':False,
        'original_labels_and_rankings_changed':False,'API_cost_usd':cost['estimated_usd'],
        'unconfirmed_reserved_usd':cost['unconfirmed_reserved_usd'],'API_cap_usd':2,
        'tests_passed':passed,'report':'README.md','completion':'Automatic safe work completed; research trust and tuning entry unresolved'}
    write(out/'final_status.json',status)
    def pct(v):return '계산 불가' if v is None else f'{100*v:.2f}%'
    def metric(version,condition,key):return next(r for r in versions[version]['macro'] if r['condition']==condition and r['metric']==key)
    table=[]
    for condition in 'ABCE':
        f=metric('original',condition,'F1@5');n=metric('original',condition,'nDCG@10')
        table.append(f"| {condition} | {pct(f['mean'])} | {pct(n['mean'])} | {f['n']} / {n['n']} |")
    controls=[]
    for r in comparison['summary']:
        if r['split']!='FRESH_VALIDATION':continue
        controls.append(f"| {r['method']} | {r['policy_pass']}/{r['n']} ({100*r['policy_pass']/r['n']:.2f}%) | {r['dangerous_errors']} | {r['output_evidence_failures']} | {r['grade_agreements']}/{r['both_judged_pairs']} | {r['binary_agreements']}/{r['both_judged_pairs']} |")
    techrows=[f"| {r['provider']} | {r['old_counts'].get('UNJUDGED',0)} | {r['new_counts'].get('UNJUDGED',0)} | {r['recovered_decision_rows']} | ${r['cost_usd']} |" for r in technical]
    versionrows=[]
    for name in versions:
        f=metric(name,'E','F1@5');n=metric(name,'E','nDCG@10')
        versionrows.append(f"| {name} | {f['n']} / {n['n']} | {pct(f['mean'])} | {pct(n['mean'])} |")
    witnesses=read(final/'label_scenarios.json')['witnesses']
    witness_lines=[]
    for metric_name in ('F1@5','nDCG@10'):
        values=[w['E_minus_C']*100 for w in witnesses if w['metric']==metric_name]
        witness_lines.append(f"{metric_name} 차이(E−C) {min(values):+.2f}~{max(values):+.2f}%p")
    text=f'''# AX 정답 평가 신뢰성 개선 실험

2026-11-07 · AI 진단 자료 · 사람 승인 없음

**평가 프로그램의 일부 오류는 고쳤지만, 믿을 만한 정답을 확보했다는 결론에는 이르지 못했습니다.** 유효한 낮은 점수나 판단 차이는 재요청하지 않았습니다. 자율 알고리즘 개선과 신규 독립 Test는 시작하지 않았습니다.

## ① 전체 진행 현황

| 작업 | 결과 |
|---|---|
| 이전 실패 원인 분석 | 완료: 핵심/보조, 정보 부족/무관, Problem/실제 수행 구분 |
| A·B·C 평가 방식 비교 | 기존 재현8개 + 신규16개, 두 제공자, 총144개 평가 행 |
| 기술 복구 | 완료된 단일 JSON 복구·ID·출처·필드 검사, 제한 재시도 구현 |
| 기존75건 재검토 | 150개 평가 행 보존. 승인된 해결0건, 주 정답 보류75건 |
| 정답 신뢰성 진입 심사 | 미통과 |
| 자율 개선 최대5회 | 0회 |
| 신규 독립 Test40개 | 생성·판정·검색 모두 미실행 |

기준76b1cc93에서 새 브랜치로 작업했습니다. 프롬프트065eccea → 신규 예시·기대 범위528fc377 → 선택48b73d3e 순서로 기록했습니다. 기대 범위는 정책으로 만든 인공 예시이며 사람 정답이 아닙니다. 기존 Test15개는 읽거나 튜닝에 사용하지 않았습니다. [사전 계획](protocol.json) · [실험 입력](benchmark.json)

## ② 평가 방식 비교

추천 방법 A·B·C·E와 **아래 평가자 A·B·C는 서로 다른 구분**입니다.

- 평가자 A: 기존 직접 판정 구조에 공통 기준을 명확히 하고 질문·사례1쌍씩 요청.
- 평가자 B: 질문만 읽는 요청과 사례만 읽는 요청으로 핵심 기능을 따로 추출한 뒤 비교.
- 평가자 C: B의 동일 추출 결과에서 근거 확인 → 직접 일치 → 기능 전이 → 핵심 충족 순서로 확인하고 프로그램이 등급 계산.

세 방식 모두 같은 0~3점 기준을 사용합니다. 3은 직접 핵심 수행, 2는 구현된 핵심 기능의 충분한 전이, 1은 부분·준비·보조, 0은 수행 기능이 확인됐으나 무관, 정보 부족은 ABSTAIN입니다. 업종이 달라도 같은 기능이면 인정합니다. 현재 감지를 미래 예측으로, 추출을 검증으로, 추천을 실행으로 바꾸어 인정하지 않습니다.

다음은 **새 예시16개 × 두 제공자=32행**의 결과입니다. 완성된 JSON의 로컬 복구 후 값이며 원본 값도 보존했습니다.

| 평가자 | 정책 예시 합치 | 중요한 오판 | 출력·근거 실패 | 세부 등급 일치 | 관련 여부 일치 |
|---|---:|---:|---:|---:|---:|
{chr(10).join(controls)}

중요한 오판은 낮은 관련성 예시에2점 이상 또는 정보 부족 예시에0점 확정입니다. A의 Claude는 현재 진동 감지를 미래 베어링 고장 예측의 입력으로 쓸 수 있다며2점을 줬습니다. 아직 구현되지 않은 핵심 예측 기능을 인정한 오판입니다. 일치율의 분모는 두 제공자가 모두 실제 등급을 낸 예시 수입니다. 보류끼리 같다는 이유로 정확한 판정이라고 계산하지 않았습니다. 단어가 원문에 있다는 검사와 의미가 맞다는 검사는 다릅니다. 원문 밖 기능 생성의 실제 비율은 독립적인 의미 검토 정답이 없어 확정할 수 없고, 근거 위반 후보와 검증 실패를 따로 공개합니다.

안전 우선으로 미리 정한 순서에 따라 **B를 추가75건 진단에 사용**했습니다. B가 가장 정확하다고 입증된 것은 아닙니다. A는 전반적인 예시 합치가 높지만 감지→예측 오판이 남고, B·C는 명시된 수행 업무도 미상으로 보는 과도한 보류가 나타났습니다. 모든 기준을 통과한 평가자는 없습니다. 복구 전 선택을 복구 후 유리한 방식으로 바꾸지 않았습니다. [복구 전 비교](benchmark_analysis.json) · [복구 후 비교](final-review/benchmark_recovered_analysis.json) · [선정 기록](method_selection.json)

## ③ 기술적 오류 개선

| 제공자 | 로컬 복구 전 미판정 행 | 복구 후 미판정 행 | 복구된 행 | 이번 전체 비용 |
|---|---:|---:|---:|---:|
{chr(10).join(techrows)}

위 분모는 각75행입니다. ABSTAIN은 출력 실패인 UNJUDGED와 구분합니다. 과거57/150행 실패와 이번 수를 단순한 동일 실험의 개선율로 해석하면 안 됩니다. 판정 구조와 배치가 함께 달라졌습니다.

실제 발견한 출력 오류는 Claude가 완성된 JSON 뒤에 설명을 붙여 파서가 거부한 경우입니다. 단 하나의 완성된 JSON 블록만 원문 그대로 읽도록 고쳤습니다. 여러 답변 블록·잘린 JSON은 합치지 않습니다. Task/Context는 원문 앵커와 필드·문자 위치로 연결합니다. 기존 자유 인용의 필드가 틀렸을 때는 같은 인용문이 실제 다른 허용 필드에 있을 때만 위치를 바로잡습니다. Problem을 실제 수행 근거로 쓰는 응답은 여전히 거부합니다.

기술 실패는 최대1회만 추가 요청하며 출력 한도만 늘립니다. 미확정 요청은 다시 보내지 않고 예약 비용을 유지합니다. 유효한 불리한 점수·의미 불일치·근거 위반은 다시 호출하지 않습니다. 실행 중인 구버전 프로세스에서 발생한 실패와 비용도 보존했습니다. 새 파서는 저장 응답을 추가 비용 없이 재해석하며, 기존 유효 답을 교체하지 않습니다. [기술 전후 내역](technical_summary.json) · [원문 복구 기록 OpenAI](openai/recovery-v2/local_recovery_log.json) · [Claude](claude/recovery-v2/local_recovery_log.json)

## ④ 75건 재검증

- 사람 승인된 해결: **0건**, 주 정답 보류: **75건**.
- 두 AI의 등급 일치 제안: **{pending['agreement_proposals']}건**. 정책 검증 실패 상태라 승인하지 않았습니다.
- 분류: `{json.dumps(pending['counts'],ensure_ascii=False)}`.

추천 이름·순위·점수·다른 평가자의 답은 API에 전달하지 않았습니다. 그러나 조정자는 기존 연구 결과를 아는 AI이므로 완전히 독립적인 인간 검증이라고 부르지 않습니다. 실제 원본 웹페이지를 이번에 새로 검증한 것도 아닙니다. 기존112개 구조화 원문과 출처 위치를 사용했습니다.

주요 새 문제는 별도 추출기가 업무 설명을 실제 수행 근거로 인정하지 않고 구현 상태 미상을 요구하는 과도한 보류입니다. 반대로 그 상태를 일괄 CONFIRMED로 바꿀 수도 없습니다. 업무 기능이 적혀 있는 것과 운영 여부가 확인된 것을 분리한 기준 검토가 필요합니다. 기존75건 중 출력·인용 확인 대기49건의 후속 상태는 기술 요약에 따로 집계했습니다. 49건 전부가 전문가만 해결할 문제였다고 단정하지 않았습니다.

원본821건 판정·75건 보류는 그대로입니다. 진단용 제안 버전과 원본을 분리했습니다. [75건별 근거·답변](final-review/pending75_review.json) · [기존 정답 보존](final-review/labels_primary_unchanged.json) · [진단 전용 제안](final-review/labels_provisional_diagnostic.json) · [추천과 AI점수를 가린 검토 자료](final-review/expert_review_packet.jsonl)

## ⑤ 성능 비교

추천 알고리즘은 다시 실행하거나 변경하지 않았습니다. 동일한 봉인 순위를 재사용했습니다. 다음 표는 **기존 AI 정답·평가 가능한6질문**에서의 과거 결과 재계산입니다.

| 추천 방식 | F1@5 | nDCG@10 | 실제 평가 질문 수 F1 / nDCG |
|---|---:|---:|---:|
{chr(10).join(table)}

새 검토를 반영한 전체 성능이 아닙니다. 정답을 바꿔서 점수가 달라지는 현상을 모델 개선이라고 부르지 않습니다.

| 정답 버전 | E 평가 질문 수 F1 / nDCG | E F1@5 | E nDCG@10 |
|---|---:|---:|---:|
{chr(10).join(versionrows)}

부분 판정을 0점으로 채우지 않아 주 정답에서 전체8질문의 F1·Recall·nDCG 확정 평균을 낼 수 없습니다. 질문별 Precision@5/10/20은 해당 Top-K가 모두 판정된 경우만 계산하며, 완전 정답이 필요한 평균과 구분합니다. 모든 방식은 지표마다 같은 질문 집합으로 비교합니다. [전체 지표·질문·반복별 결과](final-review/evaluation_versions.json)

남은 판정에 따라 E와 C의 우열이 바뀔 수 있는지, 정확한 이진 F1 차이 범위와4096개 가능한 판정 시나리오 및 nDCG 보수적 범위를 저장했습니다. 시나리오는 실제 정답·실측 성능·신뢰구간이 아닙니다. 주 정답에서 완전 평가 질문이 없으므로 유효한 전체 성능 신뢰구간도 확정하지 않습니다. [F1 범위](final-review/F1_uncertainty.json) · [가능 시나리오](final-review/label_scenarios.json) · [nDCG 범위](final-review/nDCG_outer_bounds.json) · [기존 순위·관점별 진입/이탈](final-review/ranking_diagnostics.json)

가능한 판정 시나리오에서 {', '.join(witness_lines)}로, 같은8질문에서 E가 C보다 낮은 경우와 높은 경우가 모두 존재했습니다. 이 범위는4096개 시나리오 중 관측한 범위이며 전체 수학적 극값은 아닙니다. F1은 모든 질문에 양성이 존재하는4094개 시나리오, nDCG는 등급 이득이 존재하는4096개 시나리오에서 비교했습니다.

## ⑥ 자율 개선 결과

1~5회 모두 미실행이며 가설·성능·채택 결과를 만들지 않았습니다. 먼저 평가자 실패를 확인하고, 파서·스키마·출처 연결·복구·자동 검사를 마친 뒤에도 정책 검증을 통과하지 못했습니다. 기술 오류를 해결하지 않은 채 작업을 끝낸 것이 아니라, 남은 의미 판단을 임의로 정답화하지 않은 상태입니다. [진입 판단](entry_gate.json) · [반복 상태](iterations.json)

## ⑦ 연구 목표

| 목표 | 상태 |
|---|---|
| 새 모델 F1@5 +5%p | 검증 보류: 새 알고리즘 실행0회 |
| 새 모델 nDCG@10 +3%p | 검증 보류 |
| 두 paired bootstrap95% 하한>0 | 전체 정답 미확보로 확정 불가 |
| Top-5 반복 Jaccard≥90% | 기존 E86.81%로 미충족; 새 반복 실험 아님 |
| 정답 신뢰성 | 미통과 |
| 신규 독립 Test 재현 | 미실행 |

## ⑧ 다음 연구 방향

현재 E의 우월성을 확정하거나 새 최종 모델을 선정할 근거는 부족합니다. 다음 순서가 필요합니다.

1. 책임님이 수행 기능의 명시와 운영 상태 미상의 구분, 핵심 기능 전이의 충분성을 판정할 예시를 승인합니다. 사람 검토 자료에는 추천 순위와 AI 점수가 없습니다.
2. 과도한 보류를 줄이는 별도 평가 설계를 **새 검증 예시**에서 확인합니다. 이번 실패 예시를 반복 호출해 통과시켜 성공이라고 하지 않습니다.
3. 남은 근거·등급 불일치를 보류로 관리하고, 가능한 판정에 따라 모델 우열이 바뀌는지 다시 확인합니다.
4. 신뢰성 조건을 통과한 뒤 한 요소씩 최대5회 개선하고 후보를 동결합니다. 그다음 신규 독립 Test40문항을 별도 진행합니다. 이미 본 Test15개로 튜닝하지 않습니다.

기술적 오류 감소는 확인했지만 정답 신뢰성 확보와 추천 성능 향상은 확인하지 못했습니다. 논문에는 평가 방식의 실패·한계와 기술 개선 근거로 제시할 수 있고, E가 확실히 더 좋다는 결론의 근거로는 아직 부족합니다.

## ⑨ GitHub 결과

- 브랜치: `research/evaluator-reliability-abc-20261107`
- 기준 커밋: `76b1cc93a859086d3f07dfe9b315ef6475a58cd0`
- 이번 유료 API 추정 비용: **${cost['estimated_usd']} / $2**, 총 **{cost['call_count']}회 호출**. 미확정 예약 **${cost['unconfirmed_reserved_usd']}**. 청구서가 아니라 실제 응답 토큰에 공개 단가를 적용한 값입니다.
- 자동 검사: **{passed}개 통과**, 실제 Test와 유료 API를 호출하지 않는 검사입니다.
- API별 입력·출력 토큰, 응답 모델 ID, 호출별 비용·시간·원본은 제공자별api 디렉터리 및 [비용표](final-review/cost_summary.json)에 보존했습니다.
- Claude 이전 확인 지출/예약$1.850220과 이번 비용을 합쳐 기존$5 및 최소$0.50 여유 조건을 확인했습니다. 실시간 계정 잔액 조회나 추가 충전은 하지 않았습니다.
- 기존 모델·설정·사례·정답·예측의 해시: [보존 검사](final-review/preservation_check.json). [상태 JSON](final_status.json) · [재현 명령](REPRODUCE.md)

최종 커밋은 GitHub 브랜치의 최신 커밋으로 확인합니다. 보고서 안에 자기 자신의 최종 커밋 해시를 넣어 순환 해시를 만들지 않습니다.
'''
    text=text.replace('算出不可','계산 불가')
    (out/'README.md').write_text(text,encoding='utf-8',newline='\n')
    print('Report generated',pending['counts'],passed,cost['estimated_usd'])


if __name__=='__main__':main()
