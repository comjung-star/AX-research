import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from scripts.collect_ax_expansion import OUTPUT, ROOT, export_csv


RELEASE = ROOT / "data/v2_4"
FROZEN = ROOT / "data/v2_3/main_cases_v2_3.json"
EXPECTED_FROZEN_HASH = "5a4683047e86aea67bbe6ca568d799c74b6d2aba1c4799d31cb96bf4b34987a2"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity_url(url):
    parsed = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parsed.query) if key.lower() not in {"currmenu", "topmenu", "parentseq", "pageindex"} and not key.lower().startswith("utm_")]
    return urlunsplit(("https", parsed.netloc.lower(), parsed.path.rstrip("/"), urlencode(sorted(query)), ""))


def source_records():
    rows = []
    for filename, field, kind in [("candidates.json", "candidates", "ENTERPRISE_SOURCE"),
                                  ("case_portals/candidates.json", "candidates", "CASE_PORTAL"),
                                  ("portals/use_cases.json", "records", "PUBLIC_SECTOR_INVENTORY")]:
        rows.extend({**record, "collection_kind": kind} for record in read_json(OUTPUT / filename)[field])
    if len({record["candidate_id"] for record in rows}) != len(rows):
        raise ValueError("Collection candidate IDs must be unique")
    return rows


def leakage_groups(cases):
    parents = {case["case_id"]: case["case_id"] for case in cases}

    def find(case_id):
        while parents[case_id] != case_id:
            parents[case_id] = parents[parents[case_id]]
            case_id = parents[case_id]
        return case_id

    seen_keys = {}
    for case in cases:
        organization = re.sub(r"[^a-z0-9가-힣]", "", case["organization"].casefold().split(" / ")[0])
        if organization.startswith("ibm"):
            organization = "ibm"
        if organization == "starling":
            organization = "starlingbank"
        for key in (("organization", organization), ("source", identity_url(case["source_url"])), ("sampling", case["sampling_group_id"])):
            if key in seen_keys:
                parents[find(case["case_id"])] = find(seen_keys[key])
            else:
                seen_keys[key] = case["case_id"]
    components = defaultdict(list)
    for case in cases:
        components[find(case["case_id"])].append(case["case_id"])
    return {case_id: "LEAKAGE_" + hashlib.sha256("|".join(sorted(members)).encode()).hexdigest()[:12]
            for members in components.values() for case_id in members}


def screen_record(record, seen):
    if record["collection_kind"] == "PUBLIC_SECTOR_INVENTORY":
        return "EXCLUDE", "OUTSIDE_ENTERPRISE_POPULATION", "원천이 공공기관 업무 목록이며 현재 기업 업무 모집단과 다름"
    if record.get("source_dataset_id") == "UK_ATRS":
        return "EXCLUDE", "OUTSIDE_ENTERPRISE_POPULATION", "영국 공공기관 알고리즘 투명성 기록으로 기업 업무 모집단과 다름"
    if record.get("collection_status") != "FETCHED":
        return "HOLD", "SOURCE_ACCESS_UNRESOLVED", "접근 실패·응답 오류·분량 초과로 원문 근거 미확인; 부적격 확정 아님"
    url = identity_url(record.get("canonical_url") or record["url"])
    if url in seen:
        return "EXCLUDE", "DUPLICATE_SOURCE_RECORD", "같은 정규화 출처의 중복 수집 기록; 실제 업무 중복 여부와는 다름"
    seen.add(url)
    title = record.get("source_title", "")
    if title in {"Snowflake: All Customers", "Browse All Customer Stories", "Dataiku web series | Expert webinars for AI success"}:
        return "EXCLUDE", "NOT_AN_INDIVIDUAL_CASE", "사례 목록·행사 안내 페이지로 개별 기업 운영 사례가 아님"
    if record.get("triage_status") == "INSUFFICIENT_PAGE_CONTENT":
        return "HOLD", "SOURCE_CONTENT_INSUFFICIENT", "수집된 본문이 부족하여 업무 문제·AI 구현·운영을 확인할 수 없음"
    return "HOLD", "WORKFLOW_PASSAGE_REVIEW_PENDING", "제목·짧은 설명·키워드만으로 적격 판정 불가; 개별 업무 원문 검토 대기"


def build_case(review, source, taxonomies, source_audits):
    cache_path = ROOT / ".local/ax-expansion-source-review" / (review["candidate_id"] + ".json")
    saved_audit_path = RELEASE / "source_review_audit.json"
    saved_audits = {record["candidate_id"]: record for record in read_json(saved_audit_path)} if saved_audit_path.exists() else {}
    saved = saved_audits.get(source["candidate_id"])
    if cache_path.exists():
        cached = read_json(cache_path)
        paragraph_hashes = {str(offset): hashlib.sha256(paragraph.encode()).hexdigest() for offset, paragraph in enumerate(cached["paragraphs"])}
    elif saved:
        cached = saved
        paragraph_hashes = saved["paragraph_hashes"]
    else:
        raise ValueError("No previously reviewed primary-source evidence; fetch and review before inclusion")
    if cached["access"]["status"] != "FETCHED" or identity_url(cached["url"]) != identity_url(source["url"]):
        raise ValueError("Accepted workflow requires a successfully accessed matching primary source")
    required = {"problem", "context", "implementation", "deployment", "outcome"}
    if set(review["anchors"]) != required:
        raise ValueError("All required field evidence anchors must be reviewed")
    anchors = {}
    for field, offsets in review["anchors"].items():
        if not offsets or any(type(offset) is not int or str(offset) not in paragraph_hashes for offset in offsets):
            raise ValueError("Evidence paragraph reference does not exist")
        if saved and any(saved["paragraph_hashes"].get(str(offset)) != paragraph_hashes[str(offset)] for offset in offsets):
            raise ValueError("Primary-source evidence changed; review the affected workflow again")
        anchors[field + "_anchor"] = "원문 문단 " + ", ".join(str(offset) for offset in offsets) + "; source_review_audit.json 참조"
    source_audits[source["candidate_id"]] = {
        "candidate_id": source["candidate_id"], "url": source["url"], "access": cached["access"],
        "paragraph_hashes": paragraph_hashes,
        "full_text_redistributed": False, "review_method": "AI_PRIMARY_PASSAGE_REVIEW_NOT_HUMAN_GOLD"}
    factor = taxonomies["factor"][review["factor"]]
    strategy = taxonomies["strategy"][review["strategy"]]
    case_id = "AXV24_" + hashlib.sha256((source["candidate_id"] + "|" + review["workflow_key"]).encode()).hexdigest()[:12]
    group_id = "AXV24G_" + hashlib.sha256(review["organization"].casefold().encode()).hexdigest()[:12]
    return {"case_id": case_id, "origin": "EXPANSION_PRIMARY_PASSAGE_REVIEW", "candidate_id": source["candidate_id"],
            "workflow_key": review["workflow_key"], "organization": review["organization"], "industry": review["industry"],
            **{field: review[field] for field in ("problem", "task", "context", "implementation", "outcome", "uncertainty")},
            "ai_technology": review["technology"], "source_url": source["url"], "additional_primary_sources": [],
            "evidence": anchors, "evidence_paragraph_indices": review["anchors"],
            "factor_label": factor, "factor_labels": [factor], "strategy_label": strategy, "strategy_labels": [strategy],
            "factor_review": {"rationale": review["factor_reason"], "input_view": "PROBLEM_VIEW_RATIONALE", "independently_blind": False},
            "strategy_review": {"rationale": review["strategy_reason"], "input_view": "SOLUTION_VIEW"},
            "deployment_stage": "PRODUCTION", "outcome_type": review.get("outcome_type", "VENDOR_REPORTED_NOT_INDEPENDENTLY_VERIFIED"),
            "quantitative_outcome_approved": False, "human_ground_truth_approved": False,
            "annotation_status": "AI_SOURCE_REVIEWED_PROVISIONAL", "source_review_status": "AI_PRIMARY_PASSAGE_REVIEWED",
            "sampling_group_id": group_id, "dataset_release": "2.4.0-expansion.1",
            "eligible_for_retrieval": True, "eligible_for_wald_confirmatory_analysis": False,
            "corpus_status": "EXPANSION_RESEARCH_CORPUS_NOT_GROUND_TRUTH"}


def main():
    if digest(FROZEN) != EXPECTED_FROZEN_HASH:
        raise ValueError("Frozen baseline hash mismatch; stop rather than overwrite")
    records = source_records()
    by_id = {record["candidate_id"]: record for record in records}
    reviews = read_json(RELEASE / "reviewed_workflows.json")
    taxonomies = {}
    for kind, filename, key in [("factor", "root_cause_taxonomy_v2_3.csv", "factor_id"), ("strategy", "strategy_taxonomy_v2_3.csv", "strategy_id")]:
        with (ROOT / "data/v2_3" / filename).open(encoding="utf-8-sig", newline="") as handle:
            taxonomies[kind] = {row[key].split("_")[0]: row[key] for row in csv.DictReader(handle)}
    new_cases = []
    source_audits = {}
    source_to_cases = defaultdict(list)
    workflow_decisions = []
    held_workflows = defaultdict(list)
    for review in reviews["cases"]:
        if review["candidate_id"] not in by_id:
            raise ValueError("Workflow review must trace to an existing collected source")
        if review.get("disposition_override") == "HOLD":
            held_workflows[review["candidate_id"]].append(review["decision_reason"])
            workflow_decisions.append({"candidate_id": review["candidate_id"], "workflow_key": review["workflow_key"], "decision": "HOLD", "case_id": "", "reason": review["decision_reason"]})
            continue
        case = build_case(review, by_id[review["candidate_id"]], taxonomies, source_audits)
        new_cases.append(case)
        source_to_cases[review["candidate_id"]].append(case["case_id"])
        workflow_decisions.append({"candidate_id": review["candidate_id"], "workflow_key": review["workflow_key"], "decision": "INCLUDE", "case_id": case["case_id"], "reason": "기업 운영·업무 문제·AI 구현의 원문 근거와 고정 분류체계의 적용 근거 확인; AI 검토"})
    explicit = {review["candidate_id"]: review for review in reviews["source_decisions"]}
    previous_audits = {record["candidate_id"]: record for record in read_json(RELEASE / "source_review_audit.json")} if (RELEASE / "source_review_audit.json").exists() else {}
    for candidate_id in explicit:
        cache_path = ROOT / ".local/ax-expansion-source-review" / (candidate_id + ".json")
        if cache_path.exists():
            cached = read_json(cache_path)
            source_audits[candidate_id] = {"candidate_id": candidate_id, "url": cached["url"], "access": cached["access"],
                "paragraph_hashes": {str(offset): hashlib.sha256(paragraph.encode()).hexdigest() for offset, paragraph in enumerate(cached["paragraphs"])},
                "full_text_redistributed": False, "review_method": "AI_PRIMARY_SOURCE_REVIEW_" + explicit[candidate_id]["decision"]}
        elif candidate_id in previous_audits:
            source_audits[candidate_id] = previous_audits[candidate_id]
    dispositions = []
    seen = set()
    for record in records:
        decision, code, reason = screen_record(record, seen)
        method = "RULE_SCREENING_NOT_FULL_CONTENT_REVIEW"
        if record["candidate_id"] in explicit:
            decision = explicit[record["candidate_id"]]["decision"]
            reason = explicit[record["candidate_id"]]["reason"]
            code = "PRIMARY_REVIEW_" + decision
            method = "AI_PRIMARY_PASSAGE_REVIEW"
        if record["candidate_id"] in source_to_cases:
            decision, code, reason = "INCLUDE_REVIEWED_WORKFLOWS", "PRIMARY_WORKFLOW_EVIDENCE_CONFIRMED", "이 출처에서 검토한 업무만 포함; 페이지 전체·모든 기능의 승인 아님"
            method = "AI_PRIMARY_PASSAGE_REVIEW"
        dispositions.append({"candidate_id": record["candidate_id"], "collection_kind": record["collection_kind"],
                             "source_dataset_id": record.get("source_dataset_id", ""), "publisher": record.get("publisher", ""),
                             "title": record.get("source_title") or record.get("title") or "", "source_url": record.get("url") or record.get("source_url"),
                             "decision": decision, "reason_code": code, "decision_reason": reason, "review_method": method,
                             "source_reported_stage": record.get("development_stage", "UNKNOWN"),
                             "included_case_ids": "|".join(source_to_cases.get(record["candidate_id"], [])),
                             "held_workflow_reasons": "|".join(held_workflows.get(record["candidate_id"], [])), "human_ground_truth_approved": False})
    base_cases = read_json(FROZEN)["cases"]
    cases = base_cases + new_cases
    if len({case["case_id"] for case in cases}) != len(cases):
        raise ValueError("Duplicate case ID")
    if len({(case["organization"], case["workflow_key"]) for case in new_cases}) != len(new_cases):
        raise ValueError("Duplicate reviewed workflow")
    corpus = {"dataset_release": "2.4.0-expansion.1", "status": "SOURCE_REVIEWED_EXPANSION_NOT_FROZEN_NOT_GROUND_TRUTH",
              "baseline_release": "2.3.0", "baseline_sha256": EXPECTED_FROZEN_HASH,
              "counts": {"inherited_frozen": len(base_cases), "new_reviewed_workflows": len(new_cases), "total": len(cases)},
              "cases": cases}
    write_json(RELEASE / "main_cases_v2_4.json", corpus)
    flat = [{"case_id": case["case_id"], "organization": case["organization"], "industry": case["industry"],
             "business_problem": case["problem"], "ax_target_task": case["task"], "business_context": case["context"],
             "root_cause_factor": "|".join(case["factor_labels"]), "strategy": "|".join(case["strategy_labels"]),
             "implementation": case["implementation"], "outcome": case["outcome"], "source_url": case["source_url"],
             "sampling_group_id": case["sampling_group_id"], "annotation_status": case["annotation_status"],
             "human_ground_truth_approved": False} for case in cases]
    export_csv(RELEASE / "main_cases_v2_4.csv", flat, list(flat[0]))
    export_csv(RELEASE / "source_disposition.csv", dispositions, list(dispositions[0]))
    export_csv(RELEASE / "workflow_disposition.csv", workflow_decisions, list(workflow_decisions[0]))
    for decision, filename in [("EXCLUDE", "excluded_sources.csv"), ("HOLD", "held_sources.csv")]:
        export_csv(RELEASE / filename, [row for row in dispositions if row["decision"] == decision], list(dispositions[0]))
    write_json(RELEASE / "source_review_audit.json", list(source_audits.values()))
    queries = read_json(ROOT / "data/v2_3/dev_query_candidates_v2_3.json")["queries"]
    annotations = [{"query_id": query["query_id"], "perspective_id": perspective["id"], "case_id": case["case_id"],
                    "relevance_0_4": "", "annotator_id": "", "status": "UNJUDGED", "dataset_release": corpus["dataset_release"]}
                   for query in queries for perspective in query["draft_perspectives"] for case in cases]
    export_csv(RELEASE / "dev_relevance_annotation_sheet.csv", annotations, list(annotations[0]))
    groups = leakage_groups(cases)
    split_rows = [{"case_id": case["case_id"], "organization": case["organization"], "sampling_group_id": case["sampling_group_id"],
                   "leakage_group_id": groups[case["case_id"]],
                   "source_group": identity_url(case["source_url"]),
                   "split_policy": "KEEP_ORGANIZATION_AND_SOURCE_TOGETHER; NO_AUTOMATIC_TRAIN_TEST_ASSIGNMENT"} for case in cases]
    export_csv(RELEASE / "split_groups.csv", split_rows, list(split_rows[0]))
    decisions = Counter(row["decision"] for row in dispositions)
    summary = {"review_date": "2026-10-26", "dataset_release": corpus["dataset_release"], **corpus["counts"],
               "source_records_screened": len(records), "source_decisions": dict(decisions),
               "reason_counts": dict(Counter(row["reason_code"] for row in dispositions)),
               "sources_with_included_workflows": len(source_to_cases), "workflow_decisions": dict(Counter(row["decision"] for row in workflow_decisions)),
               "sources_with_ai_passage_review": len(set(explicit) | set(source_to_cases)),
               "new_case_industry_counts": dict(Counter(case["industry"] for case in new_cases)),
               "new_case_strategy_counts": dict(Counter(case["strategy_label"] for case in new_cases)),
               "unjudged_dev_slots": len(annotations), "paid_api_calls": 0,
               "full_content_review_completed_for_all_sources": False,
               "baseline_preserved": digest(FROZEN) == EXPECTED_FROZEN_HASH}
    write_json(RELEASE / "review_summary.json", summary)
    outputs = ["main_cases_v2_4.json", "main_cases_v2_4.csv", "reviewed_workflows.json", "source_disposition.csv", "source_review_audit.json", "dev_relevance_annotation_sheet.csv", "split_groups.csv", "review_summary.json", "workflow_disposition.csv", "excluded_sources.csv", "held_sources.csv"]
    write_json(RELEASE / "release_manifest.json", {"dataset_release": corpus["dataset_release"], "status": corpus["status"],
               "sha256": {filename: digest(RELEASE / filename) for filename in outputs},
               "baseline_sha256": EXPECTED_FROZEN_HASH, "prior_qrels_reused": False,
               "quantitative_outcomes_approved": False, "human_ground_truth_approved": False})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
