from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from scripts.collect_ax_expansion import OUTPUT, PublicFetcher, export_csv, limited_text, parse_story, timestamp


SOURCES = [
    {"id": "NIA_AI_CASES", "name": "한국지능정보사회진흥원 AI활용사례", "kind": "PUBLIC_AI_APPLICATION_CANDIDATE", "language": "ko",
     "pages": [f"https://www.nia.or.kr/site/nia_kor/ex/bbs/List.do?cbIdx=99953&pageIndex={page}" for page in range(1, 6)]},
    {"id": "AIHUB_SUCCESS", "name": "AI-Hub 활용성과 우수사례", "kind": "AI_DATA_APPLICATION_CANDIDATE", "language": "ko",
     "pages": [f"https://www.aihub.or.kr/aihubnews/exclnccase/list.do?currMenu=142&topMenu=103&pageIndex={page}" for page in range(1, 18)]},
    {"id": "DATA_GO_USE_CASES", "name": "공공데이터포털 활용사례", "kind": "DATA_APPLICATION_AI_NOT_ASSUMED", "language": "ko",
     "pages": [f"https://www.data.go.kr/tcs/puc/selectPublicUseCaseListView.do?pageIndex={page}" for page in range(1, 11)]},
    {"id": "EU_EDIH", "name": "European Digital Innovation Hubs success stories", "kind": "SME_AND_PUBLIC_DIGITAL_TRANSFORMATION_CANDIDATE", "language": "en",
     "pages": [f"https://european-digital-innovation-hubs.ec.europa.eu/knowledge-hub/success-stories?page={page}" for page in range(25)]},
    {"id": "UK_ATRS", "name": "GOV.UK Algorithmic Transparency Records", "kind": "PUBLIC_ALGORITHMIC_SYSTEM_AI_NOT_ASSUMED", "language": "en",
     "pages": [f"https://www.gov.uk/algorithmic-transparency-records?page={page}" for page in range(1, 5)]}
]


def preserve_identity_url(url):
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if not key.startswith("utm_")]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(sorted(query)), ""))


def extract_candidates(payload, page_url, source):
    soup = BeautifulSoup(payload, "html.parser")
    rows = {}
    for anchor in soup.find_all("a"):
        href = anchor.get("href", "")
        action = anchor.get("onclick", "") + " " + href
        title = anchor.get_text(" ", strip=True) or anchor.get("title", "")
        candidate_url = ""
        if source["id"] == "NIA_AI_CASES":
            match = re.search(r"doBbsFView\('(\d+)','(\d+)','\d+','(\d+)'\)", action)
            if match:
                candidate_url = f"https://www.nia.or.kr/site/nia_kor/ex/bbs/View.do?cbIdx={match.group(1)}&bcIdx={match.group(2)}&parentSeq={match.group(3)}"
                title = anchor.get("title", title).replace("-첨부파일 있음", "")
            elif "/View.do?cbIdx=99953" in href:
                candidate_url = urljoin(page_url, href)
                image = anchor.find("img")
                if not title and image:
                    title = image.get("alt", "")
        elif source["id"] == "AIHUB_SUCCESS" and anchor.get("data-key", "").isdigit():
            candidate_url = f"https://www.aihub.or.kr/aihubnews/exclnccase/view.do?currMenu=142&topMenu=103&nttSn={anchor['data-key']}"
        elif source["id"] == "DATA_GO_USE_CASES":
            match = re.search(r"fn_view\(['\"]?(\d+)", action)
            if match:
                candidate_url = f"https://www.data.go.kr/tcs/puc/selectPublicUseCaseView.do?prcuseCaseSn={match.group(1)}"
                heading = anchor.find(["strong", "h3", "h4"])
                title = heading.get_text(" ", strip=True) if heading else title
        elif source["id"] == "EU_EDIH" and re.match(r"^/knowledge-hub/success-stories/[^/?]+/?$", href):
            candidate_url = urljoin(page_url, href)
        elif source["id"] == "UK_ATRS" and re.match(r"^/algorithmic-transparency-records/[^/?]+/?$", href):
            candidate_url = urljoin(page_url, href)
        if candidate_url:
            candidate_url = preserve_identity_url(candidate_url)
            identifier = source["id"] + "_" + hashlib.sha256(candidate_url.encode()).hexdigest()[:14]
            rows[identifier] = {"candidate_id": identifier, "source_dataset_id": source["id"], "publisher": source["name"],
                                "record_kind": source["kind"], "language": source["language"], "url": candidate_url,
                                "source_title_hint": limited_text(title, 25), "discovered_from": page_url}
    return list(rows.values())


def fetch_listing(source):
    fetcher = PublicFetcher()
    records = {}
    audits = []
    for page_url in source["pages"]:
        audit, payload = fetcher.get(page_url)
        audits.append({"source_dataset_id": source["id"], **audit})
        if audit["status"] == "FETCHED":
            for record in extract_candidates(payload, page_url, source):
                previous = records.get(record["candidate_id"])
                if previous is None or not previous["source_title_hint"]:
                    records[record["candidate_id"]] = record
    return list(records.values()), audits


def fetch_case(record, fetcher):
    audit, payload = fetcher.get(record["url"])
    result = {**record, "access": audit, "collection_status": audit["status"], "collected_at": timestamp(),
              "active_in_prototype": False, "human_ground_truth_approved": False,
              "development_stage": "UNKNOWN_REQUIRES_REVIEW", "semantic_verification": "NOT_INDEPENDENTLY_VERIFIED"}
    if audit["status"] == "FETCHED":
        result.update(parse_story(payload, audit.get("final_url", record["url"])))
        result["canonical_url"] = record["url"]
        if record["source_title_hint"]:
            result["source_title"] = record["source_title_hint"]
            result["source_description_excerpt"] = limited_text(result.get("source_description_excerpt", ""), 25 - len(result["source_title"].split()))
            result["source_quote_word_count"] = len(result["source_title"].split()) + len(result["source_description_excerpt"].split())
        soup = BeautifulSoup(payload, "html.parser")
        result["attachment_urls_unreviewed"] = sorted({urljoin(record["url"], anchor["href"]) for anchor in soup.find_all("a", href=True)
                                                      if re.search(r"(?:download|fileDown|\.pdf(?:\?|$))", anchor["href"], re.I) and not anchor["href"].startswith("javascript:")})[:12]
    return result


def main():
    directory = OUTPUT / "case_portals"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "sources.json").write_text(json.dumps(SOURCES, ensure_ascii=False, indent=2), encoding="utf-8")
    discoveries = []
    audits = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(fetch_listing, source): source for source in SOURCES}
        for future in as_completed(futures):
            try:
                records, source_audits = future.result()
            except Exception as error:
                records, source_audits = [], [{"source_dataset_id": futures[future]["id"], "status": "DISCOVERY_ERROR", "error_type": type(error).__name__}]
            discoveries.extend(records)
            audits.extend(source_audits)
            (directory / "discovered_sources.json").write_text(json.dumps(discoveries, ensure_ascii=False, indent=2), encoding="utf-8")
            (directory / "listing_access_audit.json").write_text(json.dumps(audits, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"portal": futures[future]["name"], "discovered": len(records)}, ensure_ascii=False), flush=True)
    records_directory = directory / "records"
    records_directory.mkdir(exist_ok=True)
    records = []
    pending = []
    for discovery in discoveries:
        path = records_directory / (discovery["candidate_id"] + ".json")
        if path.exists():
            try:
                records.append(json.loads(path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                pending.append((discovery, path))
        else:
            pending.append((discovery, path))
    grouped = defaultdict(list)
    for discovery, path in pending:
        grouped[discovery["source_dataset_id"]].append((discovery, path))
    pending = []
    while any(grouped.values()):
        for source_id in sorted(grouped):
            if grouped[source_id]:
                pending.append(grouped[source_id].pop(0))
    fetcher = PublicFetcher()
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_case, discovery, fetcher): (discovery, path) for discovery, path in pending}
        for future in as_completed(futures):
            discovery, path = futures[future]
            try:
                record = future.result()
            except Exception as error:
                record = {**discovery, "collection_status": "PARSER_ERROR", "error_type": type(error).__name__, "active_in_prototype": False}
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(path)
            records.append(record)
            if len(records) % 50 == 0:
                print(json.dumps({"portal_processed": len(records), "total": len(discoveries)}), flush=True)
    records.sort(key=lambda row: row["candidate_id"])
    (directory / "candidates.json").write_text(json.dumps({"status": "PORTAL_PAGE_CANDIDATES_NOT_VERIFIED_CASES", "candidates": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    export_csv(directory / "candidates.csv", records, ["candidate_id", "source_dataset_id", "publisher", "record_kind", "language", "source_title", "source_title_hint", "url", "collection_status", "triage_status", "ai_keyword_signals", "task_tags_automatic_not_gold", "attachment_urls_unreviewed"])
    summary = {"discovered_page_records": len(discoveries), "processed_page_records": len(records),
               "collection_status_counts": dict(Counter(row["collection_status"] for row in records)),
               "portal_counts": dict(Counter(row["source_dataset_id"] for row in records)),
               "triage_status_counts": dict(Counter(row.get("triage_status", "NOT_FETCHED") for row in records)),
               "automatically_added_to_prototype": 0, "paid_api_calls": 0}
    (directory / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
