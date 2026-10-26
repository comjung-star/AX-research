"use strict";

const state = { bootstrap: null, result: null, busy: false, toastTimer: null };
const byId = (identifier) => document.getElementById(identifier);

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function toast(message) {
  byId("toast").textContent = message;
  byId("toast").hidden = false;
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => { byId("toast").hidden = true; }, 5000);
}

async function request(path, payload) {
  const options = { headers: { "X-AX-Token": state.bootstrap?.token || "" } };
  if (payload !== undefined) {
    options.method = "POST";
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(payload);
  }
  let response;
  try { response = await fetch(path, options); }
  catch { throw new Error("실행 프로그램과 연결이 끊겼습니다. 바탕화면의 AX 나침반을 다시 실행해 주세요."); }
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "처리를 완료하지 못했습니다.");
  return body;
}

function updateRecordSummary(summary) {
  const ratings = summary.ratings || {};
  byId("record-summary").textContent = summary.total
    ? `${summary.sessions}개 테스트 기록 · 유용함 ${ratings.useful || 0} · 부분적 ${ratings.partial || 0} · 무관 ${ratings.irrelevant || 0} · 전체 의견 ${ratings.overall || 0}`
    : "아직 저장된 기록이 없습니다. 평가와 의견을 남기면 이 PC에 보관됩니다.";
}

function selectExample(example) {
  byId("query").value = example.query;
  byId("mode").value = state.bootstrap?.live_key_configured ? "live" : "demo";
  byId("example-select").value = example.query_id;
  updateMode();
  updateCount();
  byId("query").focus();
}

function updateCount() { byId("char-count").textContent = `${byId("query").value.length.toLocaleString("ko-KR")} / 4,000`; }

function updateMode() {
  const live = byId("mode").value === "live";
  const configured = state.bootstrap?.live_key_configured && state.bootstrap?.dense_model_ready;
  byId("mode-help").textContent = live
    ? (configured ? "실제 AI로 관점을 나누고 Dense로 사례를 찾은 뒤 적용 전략을 작성합니다. 업무문제와 관점별 상위 3개 이내의 사례 요약만 OpenAI API로 전송합니다."
      : "실시간 분석은 서버의 API키와 BGE-M3 준비가 필요합니다. 미설정 상태에서도 예시 데모는 바로 실행할 수 있습니다.")
    : (state.bootstrap?.dense_model_ready ? "예시는 저장된 AI 관점을 재생합니다. 자유 입력은 이 PC에서 문장을 나눈 뒤 실제 Dense로 검색합니다. API키가 필요하지 않습니다."
      : "예시는 저장된 AI 관점을 재생하고 기존 Dense로 검색합니다. 자유 입력은 단어 일치 탐색으로 체험합니다.");
  if (live) byId("scorer").value = "dense";
}

function updateConnection() {
  const connection = state.bootstrap.connection || {};
  byId("api-button").textContent = connection.verified ? "API 연결됨 ✓" : state.bootstrap.live_key_configured ? "API 연결 확인" : "API 연결";
  byId("api-model").value = state.bootstrap.live_model;
  byId("remember-key").checked = Boolean(connection.remembered);
  byId("remember-key").disabled = !state.bootstrap.secure_remember_supported;
  byId("disconnect-api").disabled = !state.bootstrap.live_key_configured;
  byId("api-status").className = "api-status" + (connection.verified ? " success" : "");
  byId("api-status").textContent = connection.verified
    ? `연결 성공 · ${state.bootstrap.live_model}의 실제 API 응답으로 ${connection.test_perspective_count}개 관점을 확인했습니다. 이제 실시간 AI로 분석할 수 있습니다.`
    : state.bootstrap.live_key_configured ? "키가 등록되어 있습니다. 연결 확인을 누르면 실제 API 호출로 사용 가능 여부를 확인합니다." : "등록된 키가 없습니다. OpenAI API키를 입력해 주세요.";
}

function download(data, filename, mime) {
  const blob = data instanceof Blob ? data : new Blob([data], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = element("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function exportRecords(format) {
  try {
    const response = await fetch(`/api/export.${format}`, { headers: { "X-AX-Token": state.bootstrap.token } });
    if (!response.ok) throw new Error("내보내기에 실패했습니다. 실행 프로그램을 확인해 주세요.");
    download(await response.blob(), `AX_사용자테스트_${new Date().toISOString().slice(0, 10)}.${format}`);
    toast("이 PC에 저장된 사용자 테스트 기록을 내보냈습니다.");
  } catch (error) { toast(error.message); }
}

async function saveFeedback(payload) {
  if (!byId("consent").checked) {
    byId("consent").focus();
    throw new Error("결과 위의 저장 동의 항목을 체크해 주세요. 동의 전에는 기록을 저장하지 않습니다.");
  }
  const summary = await request("/api/feedback", {
    ...payload, session_id: state.result.session_id, consent: true, tester: byId("tester").value
  });
  updateRecordSummary(summary);
}

function renderCard(card, branch) {
  const article = element("article", "case-card");
  article.id = `case-${branch.id}-${card.case_id}`;
  const topline = element("div", "case-topline");
  topline.append(element("span", "case-rank", `CASE ${String(card.rank).padStart(2, "0")}`), element("span", "case-id", card.case_id));
  article.append(topline, element("h4", "", card.task), element("p", "organization", card.organization), element("p", "case-problem", card.problem));
  const metadata = element("div", "source-metadata");
  const kinds = { REVIEWED_WORKFLOW: "개별 업무 검토", SOURCE_REPORTED_USE_CASE: "원천 보고 사례", SOURCE_REFERENCE: "출처·참고자료" };
  const aiLabels = { SOURCE_CLASSIFIED_AI: "원천 분류: AI", SOURCE_REVIEWED_AI_WORKFLOW: "원문 검토: AI", NON_AI_OR_UNCONFIRMED_TECHNOLOGY: "비AI 또는 기술 미확인", AI_SIGNAL_IN_PAGE_NOT_VERIFIED: "AI 언급 · 개별 업무 미확인" };
  metadata.append(element("span", "tag", card.business_scope_label || "업무 구분 미확인"), element("span", "tag", card.deployment_stage_label || "단계 미확인"), element("span", "tag", kinds[card.record_kind] || "원천 자료"), element("span", "tag", aiLabels[card.ai_status] || "AI 여부 미확인"));
  article.append(metadata);
  const solution = element("div", "case-solution");
  const solutionText = card.solution || card.original.implementation;
  solution.append(element("h5", "", "자료에 기록된 해결 방식"), element("p", "", solutionText.startsWith("UNKNOWN") ? "해결 방식이 별도로 확인되지 않았습니다. 아래 출처 설명을 확인해 주세요." : solutionText));
  const outcome = element("div", "case-outcome");
  const outcomeText = card.outcome || card.original.outcome;
  outcome.append(element("h5", "", "출처에서 보고한 변화"), element("p", "", outcomeText.startsWith("UNKNOWN") ? "별도로 확인된 관측 성과가 없습니다. 기대효과를 실제 성과로 해석하지 마세요." : outcomeText));
  article.append(solution, outcome);
  const strategies = element("div", "strategy-tags");
  card.strategies.forEach((strategy) => strategies.append(element("span", "tag", strategy.name)));
  const factors = element("div", "factor-tags");
  card.factors.forEach((factor) => factors.append(element("span", "tag", `사례 요인 · ${factor.name}`)));
  article.append(strategies, factors);
  const details = element("details", "case-details");
  details.append(element("summary", "", "추천 근거 · 원문 · 한계 확인"));
  details.append(element("h5", "", "이 관점에서 살펴볼 이유"), element("p", "", card.reason));
  details.append(element("p", "caution", card.caution));
  const original = element("details", "case-details");
  original.append(element("summary", "", "원본 사례 정보 펼치기"));
  const labels = { problem: "원본 업무문제", task: "대상 업무", context: "도입 환경", implementation: "실제 구현", outcome: "원문 보고 성과 · 독립 검증 아님", uncertainty: "원본 검토의 불확실성" };
  Object.entries(labels).forEach(([key, label]) => {
    const field = element("div", "original-field");
    field.append(element("strong", "", label), element("p", "", card.original[key]));
    original.append(field);
  });
  details.append(original);
  if (card.source_description) details.append(element("h5", "", "원천 설명 · 문제와 해결 방식이 섞여 있을 수 있어요"), element("p", "", card.source_description));
  if (card.reported_benefits && !card.reported_benefits.startsWith("UNKNOWN")) details.append(element("h5", "", "원천에 적힌 기대·보고 효과 · 독립 검증 아님"), element("p", "", card.reported_benefits));
  const reviewLabels = { SOURCE_REPORTED_NOT_INDEPENDENTLY_VERIFIED: "원천기관 보고 · 독립 사실 검증 아님", AUTOMATED_PAGE_CHECK_NOT_WORKFLOW_FACT_VERIFICATION: "페이지 자동 점검 · 개별 업무 미검증", AI_SOURCE_REVIEWED_PROVISIONAL: "AI 원문 대조 · 잠정 분류", AI_REVIEWED: "AI 검토 · 인간 정답 아님" };
  details.append(element("p", "source-review-note", `확인 수준: ${reviewLabels[card.annotation_status] || "기존 출처 검토 자료"} · 자동 분류는 연구자가 확정한 정답이 아닙니다.`));
  const source = element("a", "source-link", "원문 출처에서 확인하기 ↗");
  try {
    const sourceUrl = new URL(card.source_url);
    if (["http:", "https:"].includes(sourceUrl.protocol)) source.href = sourceUrl.href;
  } catch { source.removeAttribute("href"); }
  source.target = "_blank";
  source.rel = "noopener noreferrer";
  details.append(source, element("h5", "", "출처의 확인 위치"), element("p", "", card.source_anchor));
  if (card.view_scores) {
    const scores = element("div", "view-scores");
    Object.entries(card.view_scores).forEach(([name, score]) => scores.append(element("span", "", `${name} ${card.view_availability?.[name] === false ? "미확인" : score.toFixed(3)}`)));
    details.append(scores);
  }
  details.append(element("div", "score-label", `검색 점수 ${card.score.toFixed(3)} · 정답 확률이 아닙니다`), element("div", "trace", `근거 경로: ${card.trace.join(" → ")}`));
  article.append(details);
  const ratingArea = element("div", "rating-area");
  const ratingButtons = element("div", "rating-buttons");
  ratingButtons.setAttribute("role", "group");
  ratingButtons.setAttribute("aria-label", `${branch.title} · ${card.organization} 사례 평가`);
  let selectedRating = "";
  const buttonNodes = [];
  for (const [value, label] of [["useful", "유용함"], ["partial", "부분적"], ["irrelevant", "무관"]]) {
    const button = element("button", "rating-button", label);
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => {
      selectedRating = value;
      buttonNodes.forEach((node) => { node.classList.remove("selected"); node.setAttribute("aria-pressed", "false"); });
      button.classList.add("selected");
      button.setAttribute("aria-pressed", "true");
      saveState.textContent = "아직 저장되지 않았습니다.";
    });
    buttonNodes.push(button);
    ratingButtons.append(button);
  }
  const comment = element("textarea", "rating-comment");
  comment.rows = 2;
  comment.maxLength = 4000;
  comment.placeholder = "그렇게 판단한 이유 (선택)";
  comment.setAttribute("aria-label", `${card.organization} · ${card.task} 평가 이유`);
  const save = element("button", "save-rating", "이 사례 평가 저장");
  const saveState = element("div", "save-state");
  saveState.setAttribute("role", "status");
  comment.addEventListener("input", () => { saveState.textContent = "수정한 의견은 저장 버튼을 눌러 주세요."; });
  save.addEventListener("click", async () => {
    if (!selectedRating) return toast("유용함·부분적·무관 중 하나를 선택해 주세요.");
    save.disabled = true;
    try {
      await saveFeedback({ perspective_id: branch.id, case_id: card.case_id, rating: selectedRating, comment: comment.value });
      saveState.textContent = "✓ 이 PC에 저장했습니다. 다시 저장하면 수정됩니다.";
      toast("사례 평가를 저장했습니다.");
    } catch (error) { toast(error.message); }
    finally { save.disabled = false; }
  });
  ratingArea.append(element("p", "rating-title", "이 관점의 업무에 도움이 되나요?"), ratingButtons, comment, save, saveState);
  article.append(ratingArea);
  return article;
}

function textList(items, className) {
  const list = element("ul", className || "");
  items.forEach((item) => list.append(element("li", "", item)));
  return list;
}

function renderStrategyOverview(result) {
  const target = byId("strategy-overview");
  target.replaceChildren();
  const report = result.strategy_report;
  target.hidden = !report;
  if (!report) return;
  const heading = element("div", "strategy-overview-heading");
  heading.append(element("p", "section-number", "YOUR AX DIRECTION · 우리 업무의 방향"), element("span", "strategy-method", report.provider === "live_llm" ? "실제 AI · 사례 근거 기반 제안" : "사례 기반 시연 설명"));
  const metrics = element("div", "strategy-metrics");
  [[result.branches.length, "문제 관점"], [report.strategy_count, "적용 전략"], [report.evidence_case_count, "근거 사례"]].forEach(([count, label]) => {
    const metric = element("div");
    metric.append(element("strong", "", String(count)), element("span", "", label));
    metrics.append(metric);
  });
  const next = element("div", "next-step");
  next.append(element("span", "", "먼저 해볼 일"), element("p", "", report.next_step));
  target.append(heading, element("h3", "", "이 업무에는 이렇게 접근해 보세요"), element("p", "strategy-summary", report.summary), metrics, next);
  if (report.generation_error) target.append(element("p", "strategy-warning", report.notice));
  else {
    const method = element("details", "strategy-provenance");
    method.append(element("summary", "", "이 설명을 만든 방식 확인"), element("p", "", report.notice));
    target.append(method);
  }
}

function renderBranchStrategies(branch) {
  const target = element("div", "branch-strategies");
  const recommendation = branch.recommendation;
  if (!recommendation?.strategies?.length) return target;
  target.append(element("p", "output-label", "우리 업무에 적용할 전략 · 제안"));
  recommendation.strategies.forEach((strategy, index) => {
    const article = element("article", "applied-strategy");
    const topline = element("div", "strategy-topline");
    topline.append(element("span", "strategy-index", `STRATEGY ${String(index + 1).padStart(2, "0")}`), element("span", "priority", strategy.priority));
    article.append(topline, element("h4", "", strategy.title), element("p", "strategy-explanation", strategy.explanation));
    const body = element("div", "strategy-body");
    const actionArea = element("div", "strategy-actions");
    const actionList = element("ol");
    strategy.actions.forEach((action) => actionList.append(element("li", "", action)));
    actionArea.append(element("h5", "", "실행은 이렇게 시작해요"), actionList);
    const conditions = element("div", "strategy-conditions");
    conditions.append(element("h5", "", "먼저 준비할 것"), textList(strategy.prerequisites), element("h5", "", "적용 전 확인할 점"), textList(strategy.limitations));
    body.append(actionArea, conditions);
    const evidence = element("div", "strategy-evidence");
    evidence.append(element("strong", "", "왜 이 전략인가요?"), element("p", "", strategy.evidence_reason));
    const links = element("div", "strategy-case-links");
    strategy.supporting_case_ids.forEach((caseId) => {
      const card = branch.cases.find((item) => item.case_id === caseId);
      if (!card) return;
      const link = element("a", "", `${card.organization} · ${card.task} ↓`);
      link.href = `#case-${branch.id}-${caseId}`;
      links.append(link);
    });
    evidence.append(links);
    if (strategy.factor_links?.length) evidence.append(element("p", "factor-link-note", `참고 사례의 문제 요인: ${strategy.factor_links.join(" · ")}`));
    article.append(body, evidence);
    target.append(article);
  });
  return target;
}

function strategyMarkdown(result) {
  const report = result.strategy_report;
  const lines = ["# 우리 업무의 AX 적용 전략", "", `업무문제: ${result.query}`, "", `실행방식: ${report?.provider === "live_llm" ? "실제 LLM + 사례 근거" : "사례 기반 시연 설명"}`, "", report?.summary || "", "", `먼저 해볼 일: ${report?.next_step || ""}`, ""];
  for (const branch of result.branches) {
    lines.push(`## ${branch.id}. ${branch.title}`, "", branch.description, "");
    for (const strategy of branch.recommendation?.strategies || []) {
      lines.push(`### ${strategy.title} · ${strategy.priority}`, "", strategy.explanation, "", "실행 순서:");
      strategy.actions.forEach((action, index) => lines.push(`${index + 1}. ${action}`));
      lines.push("", "준비할 것:", ...strategy.prerequisites.map((item) => `- ${item}`), "", "적용 전 확인할 점:", ...strategy.limitations.map((item) => `- ${item}`), "", `추천 근거: ${strategy.evidence_reason}`, `근거 사례 ID: ${strategy.supporting_case_ids.join(", ")}`, "");
    }
    for (const card of branch.cases) lines.push(`### 참고 사례: ${card.organization} · ${card.task}`, "", `실제 해결 방식: ${card.solution}`, "", `원문 보고 성과: ${card.outcome}`, "", `출처: ${card.source_url}`, "");
  }
  lines.push("## 읽을 때 알아둘 점", "", report?.notice || "", "", ...(result.limitations || []).map((item) => `- ${item}`));
  return lines.join("\n");
}

function renderResults(result) {
  const providers = { cached_llm_dense: "저장 관점 + 실제 Dense 계산", live_llm_dense: "실시간 AI + Dense", local_dense: "문장 분리 + 로컬 Dense", local_lexical: "간편 탐색 · 단어 일치", cached_qci256: "연구 비교 · 256d QCI 재생" };
  byId("results").hidden = false;
  byId("result-summary").textContent = `${result.branches.length}개 문제 관점 · 관점별 최대 ${result.top_k}개 사례 · ${providers[result.provider]} · ${result.elapsed_seconds}초`;
  byId("execution-notice").textContent = result.notice;
  byId("execution-notice").classList.toggle("fallback", result.provider === "local_lexical" || result.provider === "cached_qci256");
  renderStrategyOverview(result);
  byId("perspective-nav").replaceChildren();
  byId("branches").replaceChildren();
  for (const branch of result.branches) {
    const nav = element("a", "", `${branch.id} · ${branch.title}`);
    nav.href = `#branch-${branch.id}`;
    byId("perspective-nav").append(nav);
    const section = element("section", "branch");
    section.id = `branch-${branch.id}`;
    const heading = element("div", "branch-heading");
    const text = element("div");
    text.append(element("h3", "", branch.title), element("p", "", branch.description), element("div", "branch-meta", `${branch.candidate_count}개 사례를 비교 · 독립 순위 ${branch.cases.length}개 · 다른 관점과 중복 허용`));
    heading.append(element("span", "perspective-id", branch.id), text);
    section.append(heading);
    section.append(renderBranchStrategies(branch));
    if (branch.cases.length) section.append(element("p", "output-label case-output-label", "참고 기업은 실제로 어떻게 해결했을까요? · 사례 사실"));
    const grid = element("div", "case-grid");
    branch.cases.forEach((card) => grid.append(renderCard(card, branch)));
    section.append(grid);
    if (branch.empty) section.append(element("p", "empty-state", "이 관점과 단어가 일치하는 사례가 없습니다. 표현을 바꾸거나 예시 Dense 검색을 이용해 주세요."));
    if (Object.keys(branch.strategy_support).length) {
      const support = element("div", "strategy-support");
      const descriptions = Object.entries(branch.strategy_support).map(([name, cases]) => `${name} (${cases.length}개 사례)`);
      support.append(element("strong", "", "참고 사례의 전략 분류"), element("p", "", `${descriptions.join(" · ")} — 위의 적용 전략과 연결된 사례 분류입니다.`));
      section.append(support);
    }
    byId("branches").append(section);
  }
  byId("limitations-list").replaceChildren(...result.limitations.map((limitation) => element("li", "", limitation)));
  byId("results").scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block: "start" });
}

byId("query-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.busy || !state.bootstrap) return;
  state.busy = true;
  byId("search-button").disabled = true;
  byId("error").hidden = true;
  byId("loading").hidden = false;
  byId("search-button").textContent = "관점과 적용 전략을 정리하고 있어요…";
  try {
    state.result = await request("/api/recommend", { query: byId("query").value, mode: byId("mode").value, top_k: Number(byId("top-k").value), scorer: byId("scorer").value, business_scope: byId("business-scope").value });
    byId("overall-comment").value = "";
    renderResults(state.result);
  } catch (error) {
    byId("error").textContent = error.message;
    byId("error").hidden = false;
    byId("error").scrollIntoView({ block: "center" });
  } finally {
    state.busy = false;
    byId("loading").hidden = true;
    byId("search-button").disabled = false;
    byId("search-button").replaceChildren(document.createTextNode("AX 전략과 사례 보기 "), element("span", "", "↗"));
  }
});

byId("query").addEventListener("input", updateCount);
byId("mode").addEventListener("change", updateMode);
byId("all-examples-button").addEventListener("click", () => {
  byId("all-examples").hidden = !byId("all-examples").hidden;
  byId("all-examples-button").textContent = byId("all-examples").hidden ? "예시 10개 모두 보기 ↓" : "예시 목록 접기 ↑";
});
byId("example-select").addEventListener("change", () => {
  const example = state.bootstrap.examples.find((row) => row.query_id === byId("example-select").value);
  if (example) selectExample(example);
});
byId("guide-button").addEventListener("click", () => byId("guide").showModal());
byId("close-guide").addEventListener("click", () => byId("guide").close());
byId("guide-start").addEventListener("click", () => { byId("guide").close(); byId("query").focus(); });
byId("api-button").addEventListener("click", () => { updateConnection(); byId("api-dialog").showModal(); });
byId("close-api").addEventListener("click", () => byId("api-dialog").close());
byId("api-dialog").addEventListener("close", () => { byId("api-key").value = ""; });
byId("api-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = { api_key: byId("api-key").value, model: byId("api-model").value, remember: byId("remember-key").checked };
  byId("api-key").value = "";
  byId("connect-api").disabled = true;
  byId("disconnect-api").disabled = true;
  byId("api-status").className = "api-status";
  byId("api-status").textContent = "실제 OpenAI API로 연결을 확인하고 있습니다. 응답을 기다려 주세요…";
  try {
    state.bootstrap = await request("/api/connection", payload);
    byId("mode").value = "live";
    byId("scorer").value = "dense";
    updateConnection();
    updateMode();
    toast("실제 API 연결을 확인했습니다. 창을 닫고 AX 전략과 사례 보기를 누르면 실시간 분석합니다.");
  } catch (error) {
    byId("api-status").className = "api-status error";
    byId("api-status").textContent = error.message;
  } finally {
    payload.api_key = "";
    byId("connect-api").disabled = false;
    byId("disconnect-api").disabled = !state.bootstrap.live_key_configured;
  }
});
byId("disconnect-api").addEventListener("click", async () => {
  byId("disconnect-api").disabled = true;
  try {
    state.bootstrap = await request("/api/disconnect", {});
    byId("mode").value = "demo";
    updateConnection();
    updateMode();
    toast("이 앱의 연결과 저장된 키를 해제했습니다.");
  } catch (error) { toast(error.message); }
  finally { byId("disconnect-api").disabled = !state.bootstrap.live_key_configured; }
});
byId("export-csv").addEventListener("click", () => exportRecords("csv"));
byId("export-json").addEventListener("click", () => exportRecords("json"));
byId("shutdown").addEventListener("click", async () => {
  if (!window.confirm("프로그램을 종료할까요? 저장한 평가와 의견은 남습니다.")) return;
  try {
    await request("/api/shutdown", {});
    byId("search-button").disabled = true;
    toast("프로그램을 종료했습니다. 다시 사용할 때는 바탕화면의 AX 나침반을 실행해 주세요.");
  } catch (error) { toast(error.message); }
});
byId("download-result").addEventListener("click", () => {
  if (state.result) download(JSON.stringify(state.result, null, 2), `AX_추천결과_${state.result.session_id.slice(0, 8)}.json`, "application/json;charset=utf-8");
});
byId("download-strategy").addEventListener("click", () => {
  if (state.result) download(strategyMarkdown(state.result), `AX_적용전략_${state.result.session_id.slice(0, 8)}.md`, "text/markdown;charset=utf-8");
});
byId("save-overall").addEventListener("click", async () => {
  byId("save-overall").disabled = true;
  try {
    await saveFeedback({ perspective_id: "", case_id: "", rating: "overall", comment: byId("overall-comment").value });
    toast("자유의견을 이 PC에 저장했습니다.");
  } catch (error) { toast(error.message); }
  finally { byId("save-overall").disabled = false; }
});

async function initialize() {
  byId("search-button").disabled = true;
  try {
    state.bootstrap = await request("/api/bootstrap");
    byId("business-scope").disabled = !state.bootstrap.scope_filter_supported;
    byId("active-case-count").textContent = state.bootstrap.case_count;
    byId("active-corpus-version").textContent = `자료 버전 ${state.bootstrap.version}`;
    byId("active-corpus-notice").textContent = state.bootstrap.dataset_notice;
    byId("architecture-case-count").textContent = `공공·기업·개인·교육 등을 포함한 검색 자료 ${state.bootstrap.case_count}건`;
    byId("inclusive-update-section").hidden = !state.bootstrap.version.startsWith("2.5.");
    byId("inclusive-update-summary").textContent = `현재 자료 버전 ${state.bootstrap.version}: 전체 ${state.bootstrap.record_count}개 기록을 보관하고 ${state.bootstrap.case_count}개 자료를 검색합니다. 기존 동결 사례는 별도로 보존했습니다.`;
    byId("mode").value = state.bootstrap.default_mode || "demo";
    updateConnection();
    state.bootstrap.examples.slice(0, 4).forEach((example) => {
      const chip = element("button", "example-chip", `+ ${example.label}`);
      chip.type = "button";
      chip.addEventListener("click", () => selectExample(example));
      byId("example-chips").append(chip);
    });
    state.bootstrap.examples.forEach((example) => {
      const option = element("option", "", `${example.label} · ${example.query.slice(0, 35)}…`);
      option.value = example.query_id;
      byId("example-select").append(option);
    });
    updateRecordSummary(state.bootstrap.feedback);
    updateMode();
    byId("search-button").disabled = false;
  } catch (error) { byId("error").hidden = false; byId("error").textContent = error.message; }
}

initialize();
