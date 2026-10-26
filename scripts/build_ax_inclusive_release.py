import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from functools import lru_cache
from urllib.parse import unquote, urlsplit

from scripts.build_ax_expansion_release import EXPECTED_FROZEN_HASH, FROZEN, ROOT, digest, identity_url, read_json, write_json
from scripts.collect_ax_expansion import export_csv, limited_text
from scripts.collect_ax_portals import clean, parse_csv
from scripts.review_all_ax_sources import DESTINATION, all_inputs


RELEASE = ROOT / "data/v2_5"
VERSION = "2.5.0-inclusive"
SCOPE_LABELS = {"public_work": "공공기관·공공서비스", "enterprise_work": "기업 업무·고객서비스",
                "consumer_personal": "개인·소비자 활용", "education_research": "교육·연구",
                "social_nonprofit": "사회·비영리", "mixed": "복합 영역", "unspecified": "업무 구분 미확인"}
STAGE_LABELS = {"PRODUCTION": "실제 운영", "DEPLOYED": "원천 보고: 운영", "PILOT": "시험·파일럿",
                "PRE_DEPLOYMENT": "도입 전", "IN_DEVELOPMENT": "개발 중", "PLANNED": "계획",
                "RETIRED": "종료", "NOT_IN_USE": "미사용", "UNKNOWN": "단계 미확인"}
UNKNOWN = "UNKNOWN"


def meaningful(value):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if text and not re.match(r"^UNKNOWN(?:$|[;_])", text, re.I) and text.upper() not in {"N/A", "NONE", "NAN"} else ""


def classify_scope(record, title):
    text = " ".join(str(record.get(field, "")) for field in ("organization", "organization_unit", "context", "source_title_hint", "source_description_excerpt", "source_description")) + " " + title
    tags = []
    if record.get("collection_kind") == "PUBLIC_SECTOR_INVENTORY" or record.get("source_dataset_id") == "UK_ATRS" or re.search(r"\b(?:government|ministry|municipal|public administration|city council)\b|공공행정|공공기관|시청|구청|정부", text, re.I):
        tags.append("public_work")
    if re.search(r"\b(?:universit|school|student|education|research|laborator)|language learning|learning app|tutor|학교|학생|교육|연구|개인 학습", text, re.I):
        tags.append("education_research")
    if re.search(r"\b(?:personal use|consumer app|hobby|individual creator)\b|개인용|개인 활용|취미|개인 창작", text, re.I):
        tags.append("consumer_personal")
    if re.search(r"\b(?:nonprofit|non-profit|charity|foundation)\b|비영리|사회복지|자선", text, re.I):
        tags.append("social_nonprofit")
    if record.get("collection_kind") == "ENTERPRISE_SOURCE" or re.search(r"\b(?:company|business|enterprise|customer service|manufactur|retail|bank|insurance)|기업|업무|제조|보험|은행", text, re.I):
        tags.append("enterprise_work")
    tags = list(dict.fromkeys(tags)) or ["unspecified"]
    primary = tags[0] if len(tags) == 1 or tags[0] == "public_work" else "mixed"
    return primary, tags


def separate_source_statements(text):
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?。])\s+|\n+", text) if sentence.strip()]
    problems = []
    implementations = []
    anchors = {"problem": [], "implementation": []}
    for offset, sentence in enumerate(sentences):
        has_problem = bool(re.search(r"\b(?:challenge|manual|difficult|lack|bottleneck|struggl|inefficient|fragment|unstructured|delays|burden|slow|costly|limited|cannot|could not)|수작업|어려움|부족|분산|병목|지연|비효율", sentence, re.I))
        has_solution = bool(re.search(r"\b(?:uses?|using|leverages?|applies|implemented|deployed|AI-powered|automates?)\b|활용하여|도입하여|구현|자동화", sentence, re.I))
        if has_problem and not has_solution and len(problems) < 2:
            problems.append(sentence)
            anchors["problem"].append(offset)
        if has_solution and len(implementations) < 2:
            implementations.append(sentence)
            anchors["implementation"].append(offset)
    return " ".join(problems) or UNKNOWN, " ".join(implementations) or UNKNOWN, anchors


@lru_cache(maxsize=4)
def taxonomy_prefixes(taxonomy_file, identifier):
    import csv
    with (ROOT / "data/v2_3" / taxonomy_file).open(encoding="utf-8-sig", newline="") as handle:
        return {row[identifier].split("_")[0]: row[identifier] for row in csv.DictReader(handle)}


def rule_labels(text, rules, taxonomy_file, identifier):
    taxonomy = taxonomy_prefixes(taxonomy_file, identifier)
    return [taxonomy[prefix] for prefix, pattern in rules.items() if re.search(pattern, text, re.I)]


def factor_labels_from_problem(problem):
    if not meaningful(problem):
        return []
    return rule_labels(problem, {"F01": r"\bmanual|repetitive|수작업|반복 입력", "F02": r"fragmented knowledge|scattered (?:documents|information)|지식.{0,15}분산",
        "F04": r"unstructured|비정형|다양한 양식", "F06": r"high.volume|growing volume|large volume|대량|처리량.{0,15}증가",
        "F07": r"data silos|fragmented data|lack of visibility|데이터.{0,15}분산|가시성.{0,10}부족",
        "F08": r"errors|compliance risks|오류|규정 준수", "F10": r"translation.{0,50}(?:slow|cost|time)|번역.{0,20}(?:시간|비용)"},
        "root_cause_taxonomy_v2_3.csv", "factor_id")


def strategy_labels_from_report(text):
    rules = {"S1": r"knowledge (?:retrieval|search)|retriev.{0,35}knowledge|retrieval.augmented|지식검색|검색증강|\bRAG\b",
             "S2": r"chatbot|conversational (?:assistant|agent)|voice (?:agent|assistant)|챗봇|대화형 (?:지원|에이전트)",
             "S3": r"document (?:classification|extraction)|extract.{0,30}(?:fields|information from|data from)|summariz.{0,30}(?:document|survey|meeting)|speech.to.text|문서.{0,15}추출|정보 추출|회의.{0,10}요약",
             "S4": r"anomaly detection|fraud detection|predictive maintenance|forecast|risk prediction|이상.{0,10}탐지|수요 예측|예지보전",
             "S5": r"resource allocation|decision support|optimis.{0,25}(?:schedul|rout|resource)|optimiz.{0,25}(?:schedul|rout|resource)|의사결정 지원|최적화",
             "S6": r"workflow automation|robotic process automation|automat.{0,25}(?:workflow|invoic|request processing)|워크플로.{0,15}자동화|프로세스 자동화",
             "S7": r"generat.{0,25}(?:content|reports|images|drafts)|draft.{0,20}(?:email|response)|이미지 생성|초안 작성|콘텐츠 생성"}
    selected = rule_labels(text, rules, "strategy_taxonomy_v2_3.csv", "strategy_id")
    if any(label.startswith("S2_") for label in selected):
        selected = [label for label in selected if not label.startswith("S1_")]
    return selected


def source_to_case(record, audit=None):
    identifier = record["candidate_id"]
    title = meaningful(record.get("title")) or meaningful(record.get("source_title_hint")) or meaningful(record.get("source_title"))
    if not title and audit:
        title = meaningful(audit.get("source_title"))
    source_id = meaningful(record.get("source_record_id"))
    if not title:
        title = "출처 링크 · " + unquote(urlsplit(record.get("url", "")).path.rstrip("/").split("/")[-1])[:120]
    scope_input = {**record}
    if audit and not scope_input.get("source_description_excerpt"):
        scope_input["source_description_excerpt"] = audit.get("source_description_excerpt", "")
    scope, tags = classify_scope(scope_input, title)
    is_inventory = record["collection_kind"] == "PUBLIC_SECTOR_INVENTORY"
    is_malformed = record["collection_kind"] == "MALFORMED_SOURCE_ROW"
    source_statement = meaningful(record.get("source_description")) or meaningful(record.get("problem"))
    if is_inventory:
        problem, implementation, anchors = separate_source_statements(source_statement)
        supplied_implementation = meaningful(record.get("implementation"))
        if supplied_implementation:
            implementation = supplied_implementation
        context_parts = [meaningful(record.get(field)) for field in ("organization", "organization_unit", "context", "country")]
        context = "; ".join(dict.fromkeys(value for value in context_parts if value)) or UNKNOWN
        kind = "SOURCE_REPORTED_USE_CASE"
        content_status = "STRUCTURED_SOURCE_ROW_CHECKED"
        review_status = "SOURCE_REPORTED_NOT_INDEPENDENTLY_VERIFIED"
        source_description = source_statement
        source_license = record.get("source_license", UNKNOWN)
    else:
        problem, implementation, anchors = UNKNOWN, UNKNOWN, {"problem": [], "implementation": []}
        context = "; ".join([record.get("publisher", "출처 미확인"), SCOPE_LABELS[scope]])
        source_description = meaningful(record.get("source_description_excerpt"))
        if not source_description and audit:
            source_description = meaningful(audit.get("source_description_excerpt"))
        source_description = limited_text(source_description, max(0, 25 - len(title.split())))
        kind = "SOURCE_REFERENCE" if audit and audit.get("access", {}).get("status") == "FETCHED" else "SOURCE_LINK"
        content_status = audit.get("check_status", "PAGE_CHECK_NOT_COMPLETED") if audit else "PAGE_CHECK_NOT_COMPLETED"
        review_status = "AUTOMATED_PAGE_CHECK_NOT_WORKFLOW_FACT_VERIFICATION"
        source_license = "PUBLIC_SOURCE_METADATA; REDISTRIBUTION_OF_FULL_TEXT_NOT_GRANTED"
    if is_malformed:
        problem, implementation, context, source_description = UNKNOWN, UNKNOWN, UNKNOWN, ""
        kind = "SOURCE_ROW_WITH_PARSE_ERROR"
        content_status = "MALFORMED_ROW_CHECKED_PRESERVED_WITHOUT_SHIFTING_COLUMNS"
        review_status = "SOURCE_FIELDS_NOT_RELIABLY_ALIGNED"
        source_license = "CC BY 4.0; SOURCE_ROW_PARSE_UNRESOLVED"
        if record.get("prior_parser_issue_resolved"):
            kind = "PRIOR_PARSER_ARTIFACT"
            content_status = "PRIOR_PARSER_ARTIFACT_RETAINED_CORRECT_SOURCE_ROWS_AVAILABLE"
            review_status = "PRIOR_READER_DOUBLEQUOTE_ERROR_CORRECTED_IN_RAW_SOURCE_PARSE"
            source_license = "CC BY 4.0; HISTORICAL_PARSER_ARTIFACT"
    stage = record.get("development_stage", "UNKNOWN")
    ai_status = record.get("ai_status") or ("AI_SIGNAL_IN_PAGE_NOT_VERIFIED" if audit and audit.get("contains_ai_signal") else "UNKNOWN")
    source_url = record.get("url") or record.get("source_url") or UNKNOWN
    factors = factor_labels_from_problem(problem) if is_inventory else []
    strategies = strategy_labels_from_report(source_statement) if is_inventory and ai_status == "SOURCE_CLASSIFIED_AI" else []
    organization = meaningful(record.get("organization")) or UNKNOWN
    task = title if title and not title.startswith("출처 링크") else UNKNOWN
    eligible = bool(meaningful(task)) and kind not in {"SOURCE_ROW_WITH_PARSE_ERROR", "PRIOR_PARSER_ARTIFACT"}
    if audit and audit.get("access", {}).get("status") != "FETCHED" and not is_inventory:
        eligible = False
    if audit and audit.get("check_status") in {"PAGE_READABLE_CONTENT_INSUFFICIENT", "CHECK_FAILED"}:
        eligible = False
    if audit and re.search(r"access denied|just a moment|page not found|page cannot be found|403 forbidden|404 not found|找不到|페이지를 찾을 수", audit.get("source_title", ""), re.I):
        eligible = False
        kind = "SOURCE_LINK"
        content_status = "ERROR_OR_CHALLENGE_PAGE_CHECKED_NOT_CASE_CONTENT"
    return {"case_id": "AXALL_" + identifier, "candidate_id": identifier, "source_record_id": source_id or UNKNOWN,
            "source_publisher": record.get("publisher", UNKNOWN),
            "analysis_unit": "SOURCE_REPORTED_PROJECT_OR_USE_CASE" if is_inventory else "MALFORMED_ROW_OR_FRAGMENT" if is_malformed else "SOURCE_PAGE_OR_LINK",
            "source_audit_locator": "collections/ax-expansion-2026-10-25/portals/malformed_rows_quarantine.json#source_row=" + str(record.get("source_row")) if is_malformed else "collections/ax-review-all-2026-10-26/page_audits/" + identifier + ".json" if audit else "data/v2_5/structured_row_audits.json#candidate_id=" + identifier,
            "source_input_locator": "collections/ax-review-all-2026-10-26/all_inputs.json#candidate_id=" + identifier,
            "raw_collection_record_sha256": hashlib.sha256(json.dumps(record, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
            "recovered_from_prior_parser": record.get("recovered_from_prior_parser", False), "prior_parser_issue_resolved": record.get("prior_parser_issue_resolved", False),
            "source_parse_error_details": {field: record[field] for field in ("raw_field_count", "expected_field_count", "raw_values_sha256") if field in record},
            "source_dataset_id": record.get("source_dataset_id", "ENTERPRISE_OR_CASE_PORTAL"),
            "origin": record["collection_kind"], "record_kind": kind, "organization": organization,
            "industry": meaningful(record.get("context")) or UNKNOWN, "problem": problem, "task": task, "context": context,
            "implementation": implementation, "outcome": "UNKNOWN; 원천의 기대효과와 별도 관측 성과는 구분해야 합니다.",
            "reported_benefits": meaningful(record.get("reported_benefits")) or UNKNOWN,
            "source_description": source_description, "source_url": source_url, "source_row": record.get("source_row"),
            "supporting_source_urls": record.get("supporting_source_urls", []), "organization_source_url": record.get("organization_source_url", ""),
            "source_license": source_license, "source_attribution": record.get("source_attribution", record.get("publisher", UNKNOWN)),
            "business_scope": scope, "business_scope_tags": tags, "business_scope_ko": SCOPE_LABELS[scope],
            "scope_assignment_method": "SOURCE_CATEGORY_AND_KEYWORD_RULE_NOT_HUMAN_JUDGMENT",
            "organization_type": "PUBLIC_AGENCY" if is_inventory or record.get("source_dataset_id") == "UK_ATRS" else "UNKNOWN",
            "deployment_stage": stage, "deployment_stage_ko": STAGE_LABELS.get(stage, "단계 미확인"),
            "deployment_stage_reported": record.get("development_stage_reported", UNKNOWN),
            "ai_status": ai_status, "ai_technology": meaningful(record.get("ai_technology_reported")) or UNKNOWN,
            "factor_labels": factors, "strategy_labels": strategies, "factor_label": factors[0] if factors else UNKNOWN, "strategy_label": strategies[0] if strategies else UNKNOWN,
            "factor_annotation_method": "PROBLEM_TEXT_ONLY_REGEX_NOT_INDEPENDENT_BLIND_RCA", "strategy_annotation_method": "EXPLICIT_FUNCTION_KEYWORD_RULE_NOT_HUMAN_GROUND_TRUTH",
            "annotation_status": review_status, "content_check_status": content_status, "human_ground_truth_approved": False,
            "eligible_for_wald_confirmatory_analysis": False, "quantitative_outcome_approved": False,
            "retrieval_eligible": eligible, "retrieval_text_basis": "STRUCTURED_SOURCE_FIELDS_RULE_SEPARATED_NOT_BLIND_VALIDATED" if is_inventory else "SOURCE_TITLE_REFERENCE_NOT_A_STRUCTURED_PROBLEM_CASE",
            "source_statement_sentence_indices": anchors, "sampling_group_id": "SOURCE_" + hashlib.sha256((organization if organization != UNKNOWN else source_url).casefold().encode()).hexdigest()[:16],
            "evidence": {"problem_anchor": f"원천 {source_id or identifier}; 원문 문장 번호 {anchors['problem']}; 의미 분리는 자동 규칙이며 정답 아님"},
            "uncertainty": "전체 목록에 포함한 원천 기록입니다. 운영 단계·AI 여부·미확인 필드를 표시하며 성공 사례나 검증된 원인·전략으로 확정하지 않습니다.",
            "dataset_release": VERSION}


def inherited_metadata(case):
    surrogate = {"collection_kind": "ENTERPRISE_SOURCE", "organization": case["organization"], "context": case["context"]}
    scope, tags = classify_scope(surrogate, case["task"])
    return {"business_scope": scope, "business_scope_tags": tags, "business_scope_ko": SCOPE_LABELS[scope],
            "analysis_unit": "PRIOR_REVIEWED_WORKFLOW",
            "organization_type": "UNKNOWN", "record_kind": "REVIEWED_WORKFLOW", "retrieval_eligible": True,
            "ai_status": "SOURCE_REVIEWED_AI_WORKFLOW", "deployment_stage_ko": "원문 검토: 실제 운영",
            "content_check_status": "PRIOR_SOURCE_REVIEW_PRESERVED", "source_description": ""}


def audit_structured_rows(records):
    records_by_source = defaultdict(list)
    for record in records:
        if record["collection_kind"] == "PUBLIC_SECTOR_INVENTORY":
            records_by_source[record["source_dataset_id"]].append(record)
    audits = []
    for source_id, source_records in records_by_source.items():
        payload = (ROOT / "collections/ax-expansion-2026-10-25/portals/source_datasets" / (source_id + ".csv")).read_bytes()
        header, valid, malformed = parse_csv(payload)
        snapshot_hash = hashlib.sha256(payload).hexdigest()
        raw_rows = dict(valid)
        if len(source_records) != len(raw_rows):
            raise ValueError("Structured source coverage mismatch")
        for record in source_records:
            raw = raw_rows[record["source_row"]]
            title_field = "use_case_name" if source_id == "US_OMB_2025" else "Name"
            identifier_field = "id" if source_id == "US_OMB_2025" else "PSTW ID"
            if clean(raw.get(title_field)) != record["title"] or clean(raw.get(identifier_field)) != record["source_record_id"]:
                raise ValueError("Normalized source identity/content mismatch")
            audits.append({"candidate_id": record["candidate_id"], "source_row": record["source_row"], "source_record_id": record["source_record_id"],
                           "source_identity_and_title_match": True, "original_field_count": len(raw), "expected_field_count": len(header),
                           "source_snapshot_sha256": snapshot_hash,
                           "check_status": "RAW_CSV_ROW_PARSED_AND_NORMALIZED_IDENTITY_VERIFIED", "independent_fact_verification": False})
    write_json(RELEASE / "structured_row_audits.json", audits)
    return audits


def build(require_complete=True):
    RELEASE.mkdir(parents=True, exist_ok=True)
    records = all_inputs()
    expected = {record["candidate_id"] for record in records if record.get("url")}
    audits = {path.stem: read_json(path) for path in (DESTINATION / "page_audits").glob("*.json")}
    if require_complete and not expected <= set(audits):
        raise ValueError(f"All collected pages must be checked before release: {len(expected - set(audits))} remaining")
    if digest(FROZEN) != EXPECTED_FROZEN_HASH:
        raise ValueError("Frozen corpus changed")
    inherited = read_json(ROOT / "data/v2_4/main_cases_v2_4.json")["cases"]
    metadata = {case["case_id"]: inherited_metadata(case) for case in inherited}
    cases = [*inherited, *(source_to_case(record, audits.get(record["candidate_id"])) for record in records)]
    source_children = defaultdict(list)
    for case in inherited:
        if case.get("candidate_id"):
            source_children[case["candidate_id"]].append(case["case_id"])
    identities = {}
    for case in cases[len(inherited):]:
        case["covered_by_reviewed_workflows"] = source_children.get(case["candidate_id"], [])
        if case["covered_by_reviewed_workflows"]:
            case["retrieval_eligible"] = False
            case["search_representation"] = "REVIEWED_CHILD_WORKFLOWS; SOURCE_ROW_RETAINED"
        identity = json.dumps([case[field] for field in ("organization", "task", "problem", "context", "implementation", "source_description", "record_kind", "deployment_stage", "ai_status", "ai_technology", "reported_benefits")], ensure_ascii=False)
        if identity in identities and case["retrieval_eligible"]:
            case["exact_duplicate_of"] = identities[identity]
            case["retrieval_eligible"] = False
        elif case["retrieval_eligible"]:
            identities[identity] = case["case_id"]
    if len({case["case_id"] for case in cases}) != len(cases):
        raise ValueError("Duplicate case identity")
    corpus = {"dataset_release": VERSION, "status": "ALL_COLLECTED_RECORDS_INCLUDED_WITH_SCOPE_AND_EVIDENCE_LABELS_NOT_GROUND_TRUTH",
              "baseline_sha256": EXPECTED_FROZEN_HASH, "prior_release": "2.4.0-expansion.1", "cases": cases,
              "prior_v24_corpus_sha256": digest(ROOT / "data/v2_4/main_cases_v2_4.json"),
              "inherited_case_metadata": metadata, "counts": {"inherited_workflows": len(inherited), "new_input_records": len(records),
              "total_records": len(cases), "retrievable_records": sum(case.get("retrieval_eligible", True) for case in cases)}}
    return corpus, records, audits


def main():
    corpus, records, audits = build()
    row_audits = audit_structured_rows(records)
    write_json(RELEASE / "main_cases_v2_5.json", corpus)
    flat = []
    for case in corpus["cases"]:
        meta = {**case, **corpus["inherited_case_metadata"].get(case["case_id"], {})}
        flat.append({"case_id": case["case_id"], "candidate_id": case.get("candidate_id", ""), "record_kind": meta["record_kind"],
            "analysis_unit": meta["analysis_unit"], "source_publisher": case.get("source_publisher", "REFER_TO_ORIGINAL_SOURCE"),
            "business_scope": meta["business_scope"], "업무구분": meta["business_scope_ko"], "business_scope_tags": meta["business_scope_tags"],
            "organization_type": meta["organization_type"], "organization": case["organization"], "industry": case["industry"],
            "business_problem": case["problem"], "ax_target_task": case["task"], "business_context": case["context"],
            "implementation": case["implementation"], "outcome": case["outcome"], "reported_benefits": case.get("reported_benefits", UNKNOWN),
            "source_description": meta["source_description"], "ai_status": meta["ai_status"], "deployment_stage": case.get("deployment_stage", "UNKNOWN"),
            "운영단계": meta["deployment_stage_ko"], "root_cause_factor": "|".join(case["factor_labels"]), "strategy": "|".join(case["strategy_labels"]),
            "source_url": case["source_url"], "source_record_id": case.get("source_record_id", ""), "source_license": case.get("source_license", "REFER_TO_ORIGINAL_SOURCE"),
            "annotation_status": case["annotation_status"], "content_check_status": meta["content_check_status"], "retrieval_eligible": meta["retrieval_eligible"],
            "dataset_release": VERSION, "human_ground_truth_approved": False})
    export_csv(RELEASE / "main_cases_v2_5.csv", flat, list(flat[0]))
    export_csv(RELEASE / "retrieval_cases_v2_5.csv", [row for row in flat if row["retrieval_eligible"]], list(flat[0]))
    coverage = [{"candidate_id": record["candidate_id"], "case_id": "AXALL_" + record["candidate_id"], "origin": record["collection_kind"],
                 "included_in_dataset": True, "scope_exclusion": False,
                 "check_status": audits[record["candidate_id"]]["check_status"] if record.get("url") else "SOURCE_ROW_SCHEMA_AND_CONTENT_CHECKED"} for record in records]
    export_csv(RELEASE / "all_input_coverage.csv", coverage, list(coverage[0]))
    summary = {"dataset_release": VERSION, **corpus["counts"], "scope_exclusions": 0,
               "collected_record_checks": len(coverage), "page_access_checks": len(audits),
               "structured_rows_checked_against_raw_csv": len(row_audits),
               "structured_source_counts": dict(Counter(record["source_dataset_id"] for record in records if record["collection_kind"] == "PUBLIC_SECTOR_INVENTORY")),
               "recovered_structured_records_from_prior_parser": sum(record.get("recovered_from_prior_parser", False) for record in records),
               "source_origin_counts": dict(Counter(record["collection_kind"] for record in records)),
               "business_scope_counts": dict(Counter(row["business_scope"] for row in flat)),
               "record_kind_counts": dict(Counter(row["record_kind"] for row in flat)),
               "page_check_statuses": dict(Counter(audit["check_status"] for audit in audits.values())),
               "all_collected_inputs_included": len(coverage) == len(records), "human_ground_truth_approved": False,
               "review_method": "ALL_RECORDS_PROGRAMMATIC_SCHEMA_CONTENT_AND_SOURCE_ACCESS_AUDIT; NO_CLAIM_OF_MANUAL_FACT_REVIEW_FOR_ALL_RECORDS", "paid_api_calls": 0}
    write_json(RELEASE / "review_summary.json", summary)
    write_json(RELEASE / "release_manifest.json", {"dataset_release": VERSION, "baseline_sha256": EXPECTED_FROZEN_HASH,
               "sha256": {filename: digest(RELEASE / filename) for filename in ["main_cases_v2_5.json", "main_cases_v2_5.csv", "retrieval_cases_v2_5.csv", "all_input_coverage.csv", "review_summary.json", "structured_row_audits.json"]},
               "source_snapshots_sha256": {filename: digest(ROOT / filename) for filename in [
                   "collections/ax-expansion-2026-10-25/candidates.json", "collections/ax-expansion-2026-10-25/case_portals/candidates.json",
                   "collections/ax-expansion-2026-10-25/portals/use_cases.json", "collections/ax-expansion-2026-10-25/discovered_sources.json",
                   "collections/ax-expansion-2026-10-25/portals/malformed_rows_quarantine.json",
                   "collections/ax-expansion-2026-10-25/portals/source_datasets/US_OMB_2025.csv",
                   "collections/ax-expansion-2026-10-25/portals/source_datasets/EU_PSTW_202609.csv",
                   "data/v2_3/main_cases_v2_3.json", "data/v2_4/main_cases_v2_4.json"]},
               "inclusion_policy": "ALL_SCOPES_ALL_STAGES_ALL_AI_STATUSES_INCLUDED_WITH_LABELS", "prior_qrels_transferred": False})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
