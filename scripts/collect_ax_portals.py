from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests

from scripts.collect_ax_expansion import OUTPUT, export_csv


PORTALS = OUTPUT / "portals"
SOURCES = [
    {"id": "US_OMB_2025", "publisher": "U.S. Office of Management and Budget", "kind": "PUBLIC_SECTOR_REPORTED_AI_USE_CASE",
     "landing_url": "https://github.com/ombegov/2025-Federal-Agency-AI-Use-Case-Inventory",
     "download_url": "https://raw.githubusercontent.com/ombegov/2025-Federal-Agency-AI-Use-Case-Inventory/main/Data/2025_individually_reported_AI_use_cases.csv",
     "license": "U.S. federal public inventory; no separate repository LICENSE found; retain source attribution and review redistribution conditions",
     "license_url": "https://github.com/ombegov/2025-Federal-Agency-AI-Use-Case-Inventory/blob/main/README.md"},
    {"id": "EU_PSTW_202609", "publisher": "European Commission Joint Research Centre", "kind": "PUBLIC_SECTOR_TECH_USE_CASE",
     "landing_url": "https://interoperable-europe.ec.europa.eu/collection/public-sector-tech-watch/pstw-cases-viewer-data-download",
     "download_url": "https://interoperable-europe.ec.europa.eu/sites/default/files/custom-page/attachment/2026-09/pstw_dataset.csv",
     "license": "CC BY 4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
     "attribution": "European Commission, Joint Research Centre (2026), PSTW: Public Sector Tech Watch latest dataset of selected cases, doi:10.2905/JRC.J1MWC9R; September 2026 snapshot. Fields selected and normalized; no endorsement implied."}
]


def parse_csv(payload):
    text = payload.decode("utf-8-sig")
    delimiter = csv.Sniffer().sniff(text.splitlines()[0], delimiters=",;\t").delimiter
    reader = csv.reader(io.StringIO(text), delimiter=delimiter, doublequote=True)
    header = next(reader)
    valid = []
    malformed = []
    for source_row, values in enumerate(reader, 2):
        if not any(values):
            continue
        if len(values) != len(header):
            malformed.append({"source_row": source_row, "expected_fields": len(header), "actual_fields": len(values), "values": values})
        else:
            valid.append((source_row, dict(zip(header, values))))
    return header, valid, malformed


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_stage(value):
    value = clean(value).lower()
    return {"deployed": "DEPLOYED", "implemented": "DEPLOYED", "pilot": "PILOT", "pre-deployment": "PRE_DEPLOYMENT",
            "in development": "IN_DEVELOPMENT", "planned": "PLANNED", "retired": "RETIRED", "not in use": "NOT_IN_USE"}.get(value, "UNKNOWN")


def common_record(source, source_row, source_id, title):
    return {"candidate_id": f"{source['id']}_{source_row:05d}", "source_dataset_id": source["id"], "source_record_id": source_id,
            "source_row": source_row, "publisher": source["publisher"], "record_kind": source["kind"], "title": clean(title),
            "source_url": source["landing_url"], "download_url": source["download_url"], "source_license": source["license"],
            "license_url": source["license_url"], "source_attribution": source.get("attribution", source["publisher"]),
            "review_status": "SOURCE_REPORTED_NOT_INDEPENDENTLY_VALIDATED", "human_ground_truth_approved": False,
            "active_in_prototype": False, "strategy_labels": [], "factor_labels": [],
            "outcome_verification": "REPORTED_OR_EXPECTED_BENEFITS_NOT_VERIFIED_CAUSAL_EFFECT", "language": "en"}


def normalize_us(source, source_row, row):
    record = common_record(source, source_row, clean(row.get("id")), row.get("use_case_name"))
    stage = clean(row.get("development_stage"))
    record.update(organization=clean(row.get("agency_name")), organization_unit=clean(row.get("agency_bureau")),
                  problem=clean(row.get("problem_solved")) or "UNKNOWN", task=clean(row.get("use_case_name")),
                  context=clean(row.get("topic_area")), implementation=clean(row.get("system_outputs")) or "UNKNOWN",
                  ai_technology_reported=clean(row.get("classification")), vendor_reported=clean(row.get("vendor_name")),
                  reported_benefits=clean(row.get("benefits")) or "UNKNOWN", outcome="UNKNOWN_REQUIRES_SEPARATE_OUTCOME_REVIEW",
                  development_stage_reported=stage, development_stage=normalize_stage(stage), ai_status="SOURCE_CLASSIFIED_AI",
                  country="United States", operational_date_reported=clean(row.get("operational_date")),
                  high_impact_reported=clean(row.get("is_high_impact")), quality_flags=[])
    if not record["title"]:
        record["quality_flags"].append("MISSING_TITLE")
    if record["problem"] == "UNKNOWN":
        record["quality_flags"].append("MISSING_PROBLEM")
    if record["development_stage"] == "UNKNOWN":
        record["quality_flags"].append("UNREPORTED_STAGE")
    return record


def normalize_eu(source, source_row, row):
    record = common_record(source, source_row, clean(row.get("PSTW ID")), row.get("Name"))
    primary = clean(row.get("Primary Technology"))
    secondary = clean(row.get("Secondary Technology"))
    record.update(organization=clean(row.get("Responsible organisation")), organization_unit=clean(row.get("Responsible organisation category")),
                  problem="UNKNOWN_SEPARATE_REVIEW_REQUIRED", task=clean(row.get("Application type")),
                  context=clean(row.get("Functions of Government (COFOG level II)")), implementation="UNKNOWN_SEPARATE_REVIEW_REQUIRED",
                  source_description=clean(row.get("Description")), ai_technology_reported=primary + ("; " + secondary if secondary else ""),
                  vendor_reported=clean(row.get("Company name")), outcome="UNKNOWN_REQUIRES_SEPARATE_OUTCOME_REVIEW",
                  reported_benefits="UNKNOWN_SEPARATE_REVIEW_REQUIRED", development_stage_reported=clean(row.get(" Status")),
                  development_stage=normalize_stage(row.get(" Status")),
                  ai_status="SOURCE_CLASSIFIED_AI" if "Artificial Intelligence" in {primary, secondary} else "NON_AI_OR_UNCONFIRMED_TECHNOLOGY",
                  country=clean(row.get("Geographical coverage (country)")), organization_source_url=clean(row.get("Website")),
                  supporting_source_urls=[clean(row.get("Source")), clean(row.get("Link to the story"))], quality_flags=[])
    if record["development_stage"] == "UNKNOWN":
        record["quality_flags"].append("UNRECOGNIZED_SOURCE_STAGE")
    if primary not in {"Artificial Intelligence", "Blockchain", "Digital Twins", "AR/VR", "Other", "5G (Edge Computing)", "Quantum Computing", "Virtual Worlds"}:
        record["quality_flags"].append("UNRECOGNIZED_PRIMARY_TECHNOLOGY")
    return record


def main():
    PORTALS.mkdir(parents=True, exist_ok=True)
    raw_directory = PORTALS / "source_datasets"
    raw_directory.mkdir(exist_ok=True)
    records = []
    source_manifest = []
    malformed_rows = []
    for source in SOURCES:
        path = raw_directory / (source["id"] + ".csv")
        if path.exists():
            payload = path.read_bytes()
            retrieval = "LOCAL_SNAPSHOT_REUSED"
        else:
            response = requests.get(source["download_url"], timeout=(10, 60), headers={"User-Agent": "AXResearchCollector/1.0 public dataset download"})
            response.raise_for_status()
            payload = response.content
            path.write_bytes(payload)
            retrieval = "DOWNLOADED"
        header, valid, malformed = parse_csv(payload)
        normalizer = normalize_us if source["id"] == "US_OMB_2025" else normalize_eu
        normalized = [normalizer(source, source_row, row) for source_row, row in valid]
        records.extend(normalized)
        malformed_rows.extend({"source_dataset_id": source["id"], **row} for row in malformed)
        manifest = {**source, "retrieval": retrieval, "accessed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "snapshot_path": str(path.relative_to(OUTPUT)), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload),
                    "source_columns": header, "valid_rows": len(valid), "malformed_rows_quarantined": len(malformed),
                    "stages": dict(Counter(record["development_stage"] for record in normalized)),
                    "ai_statuses": dict(Counter(record["ai_status"] for record in normalized))}
        source_manifest.append(manifest)
        (PORTALS / (source["id"] + ".json")).write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        (PORTALS / "source_manifest.json").write_text(json.dumps(source_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"source": source["id"], "valid_rows": len(valid), "quarantined": len(malformed), "stages": manifest["stages"]}, ensure_ascii=False), flush=True)
    (PORTALS / "use_cases.json").write_text(json.dumps({"status": "SEPARATE_PUBLIC_SECTOR_CANDIDATE_POOL", "records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    fields = ["candidate_id", "source_dataset_id", "source_record_id", "source_row", "organization", "title", "task", "problem", "context", "implementation", "source_description", "reported_benefits", "outcome", "ai_technology_reported", "ai_status", "development_stage", "country", "source_url", "organization_source_url", "source_license", "review_status", "quality_flags"]
    export_csv(PORTALS / "use_cases.csv", records, fields)
    selected = [record for record in records if record["ai_status"] == "SOURCE_CLASSIFIED_AI" and record["development_stage"] in {"DEPLOYED", "PILOT"} and not record["quality_flags"]]
    export_csv(PORTALS / "ai_deployed_or_pilot_review_queue.csv", selected, fields)
    (PORTALS / "malformed_rows_quarantine.json").write_text(json.dumps(malformed_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    identity = {}
    duplicates = []
    for record in records:
        key = record["source_dataset_id"] + ":" + record["organization"].casefold() + ":" + record["title"].casefold()
        if key in identity:
            duplicates.append({"first_id": identity[key], "duplicate_id": record["candidate_id"]})
        else:
            identity[key] = record["candidate_id"]
    (PORTALS / "duplicate_review.json").write_text(json.dumps(duplicates, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {"total_valid_source_rows": len(records), "malformed_source_rows_quarantined": len(malformed_rows),
               "source_counts": dict(Counter(record["source_dataset_id"] for record in records)),
               "stages": dict(Counter(record["development_stage"] for record in records)),
               "source_classified_ai_rows": sum(record["ai_status"] == "SOURCE_CLASSIFIED_AI" for record in records),
               "ai_deployed_or_pilot_first_review_queue": len(selected), "exact_organization_title_duplicate_pairs": len(duplicates),
               "automatically_added_to_prototype": 0, "paid_api_calls": 0,
               "limitations": ["Reported inventory entries are not verified enterprise AX success cases.", "Public-sector records remain separate from enterprise frozen corpus.", "Planned, experimental, retired, non-AI and uncertain entries are retained and labeled.", "Descriptions are not automatically treated as observed outcomes or human Gold.", "Public business contact email columns are excluded from normalized records."]}
    (PORTALS / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
