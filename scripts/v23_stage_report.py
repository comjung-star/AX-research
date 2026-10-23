#!/usr/bin/env python3
"""Write honest, reproducible per-stage v2.3 Dev experiment reports."""
import sys,csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"experiments/v23_dev"
stage=int(sys.argv[1]);base=R/f"stage{stage}"
def read(p):
 with open(p,encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
m=json.loads((base/"manifest.json").read_text(encoding="utf-8"))
lines=[f"# AX v2.3 Stage {stage} — 실제 Dev 실험 결과",
 "**코퍼스:** 업무 사례 84개 · 개발 문제 10개 · AI 관련도 2,520개",
 "**평가:** Dev AI 평가자료만 사용. 인간 Gold나 독립 Test가 아님.",
 "", "## 실행 조건",json.dumps(m,ensure_ascii=False,indent=2),""]
if stage in (1,2):
 s=read(base/"summary.csv")
 lines+=["## 비교 결과","| 방식 | K | Recall | 관점 Coverage | 전략 Coverage* |","|---|---:|---:|---:|---:|"]
 for r in s:lines.append(f"| {r['system']} | {r['k']} | {float(r['recall_mean']):.3f} | {float(r['perspective_coverage_mean']):.3f} | {float(r['strategy_coverage_mean']):.3f} |")
 lines+=["","* 전략 커버리지 기준은 Silver 양성 사례의 전략을 합친 **파생 지표**이며 독립적인 전략 정답 아님."]
 if stage==2:
  a=read(base/"candidate_union_metrics.csv")
  delta=[float(x["hybrid_candidate_recall"])-float(x["dense_candidate_recall"]) for x in a]
  lines+=["",f"**2-3 후보 풀 평균 Recall 변화(동일 검색 슬롯)**: {sum(delta)/len(delta):+.3f}. 손실도 그대로 보고한다.",
  "2-2/2-4 학습형 모델은 평가 대상 질의가 훈련에 포함되지 않는 Leave-One-Query-Out을 적용했다."]
if stage==3:
 lines+=["## 통계 및 추적 결과",f"- Factor×Strategy: {m['pairs']}쌍",
  f"- Wald 분석 가능한 쌍: {m['wald_eligible']}",
  f"- Wald 표본부족으로 보류: {m['wald_sparse_abstentions']}",
  f"- 추적 대상 검색 사례: {m['unique_rank_occurrences']}",
  f"- 사례–원인–전략 근거 연결: {m['trace_rows']}",
  "Wald 결과는 인과관계가 아닌 연관성이다. 표본 부족이면 통계 판단을 보류한다."]
if stage==4:
 s=read(base/"summary.csv")
 lines+=["## 추천 전략 비교 (탐색적 Dev)","| 방식 | Strategy Recall@3 | Strategy Precision@3 |","|---|---:|---:|"]
 for r in s:lines.append(f"| {r['system']} | {float(r['strategy_recall_at_3_mean']):.3f} | {float(r['strategy_precision_at_3_mean']):.3f} |")
 lines +=["",f"근거 연결 {m['trace_records']}건. 실제 API 생성 답변 {m['evidence_grounded_llm_answers']}회.",
 "전략 기준은 AI 관련도 양성 사례들에서 파생됐고 독립 정답이 아니다. 최종 전략추천 정확도의 검증으로 해석할 수 없다."]
lines +=["","## 연구상 제한","- 사후에 사례 또는 Ground Truth를 성능 개선 목적으로 변경하지 않았다.",
 "- v2.3 코퍼스에 Dev 관점에 맞춰 추가한 사례가 있으므로 선택 편향이 존재한다.",
 "- 독립 Held-out Test를 완료한 것으로 표현하지 않는다."]
(base/"DEV_RESULT_ANALYSIS.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
if stage==4:
 text=["# AX v2.3 Stage 1–4 통합 실행 보고","**모든 Stage가 실제 완료된 후 생성됨.**",""]
 for i in range(1,5):
  p=R/f"stage{i}/manifest.json";assert p.exists(),f"Stage {i} not run"
  st=json.loads(p.read_text(encoding="utf-8"))
  assert st.get("stage","").startswith(f"STAGE_{i}_REAL_EXECUTED")
  text +=[f"## Stage {i}",f"[개별 실행 분석](stage{i}/DEV_RESULT_ANALYSIS.md)",st["stage"],""]
 text+=["## 주의","결과는 실제 v2.3 Dev 실행 결과이다. AI 관련도 점수와 파생 전략 평가 기준을 사용하였으므로 독립 인간 Gold·Test 성능은 아직 검증하지 않았다."]
 (R/"STAGE1_TO_4_EXECUTION_REPORT.md").write_text("\n".join(text)+"\n",encoding="utf-8")
print("WROTE STAGE REPORT",stage,flush=True)
