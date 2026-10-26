from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import threading
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "collections/ax-expansion-2026-10-25"
USER_AGENT = "AXResearchCollector/1.0 (public customer-story metadata; no authentication)"
AI_PATTERN = re.compile(r"\b(?:AI|ML|LLM|GPT|RAG|OCR|NLP|Copilot|Claude|Gemini|ChatGPT|watsonx|Agentforce)\b|artificial intelligence|machine learning|generative|deep learning|computer vision|predictive|인공지능|생성형|머신러닝", re.I)
AUTOMATION_PATTERN = re.compile(r"\b(?:automation|RPA|robotic|analytics|data integration|data platform|process mining)\b|자동화|데이터 통합|예측|분석", re.I)
TASK_RULES = {
    "고객상담·서비스": r"customer (?:service|support)|contact cent|call cent|chatbot|고객상담|고객 지원",
    "문서·지식업무": r"document|knowledge|invoice|contract|문서|지식|계약|송장",
    "개발·IT운영": r"developer|software develop|coding|code review|debug|IT operation|개발|코딩",
    "데이터·분석": r"data (?:integration|platform|pipeline)|analytics|데이터|분석",
    "제조·현장·설비": r"manufactur|factory|maintenance|industrial|제조|설비|공장",
    "의료·생명과학": r"healthcare|hospital|clinical|patient|pharma|의료|병원|환자",
    "금융·보험": r"bank|insurance|fraud|financial|금융|보험|은행",
    "유통·영업·마케팅": r"retail|sales|marketing|commerce|영업|유통|마케팅",
    "물류·교통": r"logistic|supply chain|transport|warehouse|물류|공급망|창고",
    "인사·교육": r"human resources|recruit|education|student|learning experience|인사|교육|채용",
    "에너지·환경": r"energy|utility|utilities|climate|sustainab|에너지|환경",
    "공공·행정": r"government|public sector|municipal|공공|행정|정부"
}


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_url(url):
    try:
        parts = urlsplit(html.unescape(url.strip()))
    except ValueError:
        return ""
    if parts.scheme not in {"http", "https"} or parts.username or parts.password:
        return ""
    return urlunsplit(("https", parts.netloc.lower(), re.sub(r"/+", "/", parts.path).rstrip("/") or "/", "", ""))


def source_key(url, publisher):
    path = unquote(urlsplit(url).path).lower().rstrip("/")
    if publisher == "Microsoft":
        identifier = re.search(r"/story/(\d+)", path)
        if identifier:
            return publisher + ":" + identifier.group(1)
    path = re.sub(r"^/(?:ko|kr|ko-kr|en|en-us)(?=/)", "", path)
    return publisher + ":" + path


def limited_text(value, words):
    return " ".join(re.sub(r"\s+", " ", value).strip().split()[:max(0, words)])


class PublicFetcher:
    def __init__(self):
        self.policies = {}
        self.locks = defaultdict(threading.Lock)
        self.last_request = defaultdict(float)
        self.audit = []

    def policy(self, host):
        with self.locks[host]:
            if host not in self.policies:
                robots_url = f"https://{host}/robots.txt"
                parser = RobotFileParser(robots_url)
                try:
                    response = requests.get(robots_url, timeout=(8, 20), headers={"User-Agent": USER_AGENT})
                    parser.parse(response.text.splitlines() if response.status_code == 200 else [])
                    available = response.status_code in {200, 404, 410}
                    self.policies[host] = (parser, available, response.status_code)
                except requests.RequestException:
                    self.policies[host] = (parser, False, None)
            return self.policies[host]

    def get(self, url):
        host = urlsplit(url).netloc
        parser, available, robots_status = self.policy(host)
        result = {"url": url, "accessed_at": timestamp(), "robots_status": robots_status, "status": "", "http_status": None}
        if not available or not parser.can_fetch(USER_AGENT, url):
            result["status"] = "ROBOTS_DENIED_OR_UNAVAILABLE"
            return result, b""
        with self.locks[host]:
            delay = max(0.6, parser.crawl_delay(USER_AGENT) or 0)
            time.sleep(max(0, delay - (time.monotonic() - self.last_request[host])))
            try:
                response = requests.get(url, timeout=(8, 25), headers={"User-Agent": USER_AGENT}, stream=True)
                payload = bytearray()
                truncated = False
                for chunk in response.iter_content(65536):
                    payload.extend(chunk)
                    if len(payload) > 8_000_000:
                        truncated = True
                        break
                response.close()
                result.update(http_status=response.status_code, final_url=response.url, content_type=response.headers.get("Content-Type", ""),
                              payload_sha256=hashlib.sha256(payload).hexdigest(), bytes_read=len(payload), truncated=truncated,
                              status="FETCHED" if response.status_code == 200 and not truncated else "HTTP_ERROR_OR_TRUNCATED")
                return result, bytes(payload)
            except requests.RequestException as error:
                result.update(status="ACCESS_FAILED", error_type=type(error).__name__)
                return result, b""
            finally:
                self.last_request[host] = time.monotonic()


def find_story_links(payload, page_url, source):
    found = set()
    soup = BeautifulSoup(payload, "html.parser")
    raw_links = [anchor["href"] for anchor in soup.find_all("a", href=True)]
    raw_links.extend(re.findall(r'https?://[^\s"<>\\]+', payload.decode("utf-8", errors="replace").replace("\\/", "/")))
    for raw_url in raw_links:
        try:
            url = normalize_url(urljoin(page_url, raw_url))
        except ValueError:
            continue
        parts = urlsplit(url)
        if parts.netloc == source["host"] and re.search(source["path_pattern"], parts.path, re.I):
            if parts.path.rstrip("/").split("/")[-1] not in {"search", "all-customers", "gen-ai", "your-ai", "featured", "champions-program", "solutions-accelerator-general"}:
                found.add(url)
    return found


def discover_source(source):
    fetcher = PublicFetcher()
    candidates = {}
    audits = []
    queue = [(url, 0) for url in source["sitemaps"]]
    visited = set()
    while queue and len(visited) < 10:
        url, depth = queue.pop(0)
        if url in visited or urlsplit(url).netloc != source["host"]:
            continue
        visited.add(url)
        audit, payload = fetcher.get(url)
        audits.append({"publisher": source["name"], "kind": "sitemap", **audit})
        if audit["status"] != "FETCHED":
            continue
        try:
            root = ET.fromstring(payload)
        except ET.ParseError:
            continue
        locations = [item.text for item in root.iter() if item.tag.rsplit("}", 1)[-1] == "loc" and item.text]
        if root.tag.rsplit("}", 1)[-1] == "sitemapindex" and depth < 2:
            queue.extend((child, depth + 1) for child in locations[:8])
            continue
        for location in locations:
            candidate = normalize_url(location)
            if urlsplit(candidate).netloc == source["host"] and re.search(source["path_pattern"], urlsplit(candidate).path, re.I):
                key = source_key(candidate, source["name"])
                row = candidates.setdefault(key, {"key": key, "publisher": source["name"], "url": candidate, "discovered_from": [], "url_aliases": []})
                row["discovered_from"].append(url)
                if candidate != row["url"]:
                    row["url_aliases"].append(candidate)
    for hub in source["hubs"]:
        audit, payload = fetcher.get(hub)
        audits.append({"publisher": source["name"], "kind": "hub", **audit})
        if audit["status"] == "FETCHED":
            for candidate in find_story_links(payload, audit.get("final_url", hub), source):
                key = source_key(candidate, source["name"])
                row = candidates.setdefault(key, {"key": key, "publisher": source["name"], "url": candidate, "discovered_from": [], "url_aliases": []})
                row["discovered_from"].append(hub)
    return list(candidates.values()), audits


def parse_story(payload, url):
    soup = BeautifulSoup(payload, "html.parser")
    canonical_tag = soup.find("link", rel="canonical")
    canonical = normalize_url(urljoin(url, canonical_tag.get("href", ""))) if canonical_tag else normalize_url(url)
    title_tag = soup.find("meta", property="og:title") or soup.find("h1") or soup.find("title")
    description_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
    title = title_tag.get("content", "") if title_tag and title_tag.name == "meta" else title_tag.get_text(" ", strip=True) if title_tag else ""
    description = description_tag.get("content", "") if description_tag else ""
    published_tag = soup.find("meta", property="article:published_time")
    for hidden in soup.select("script, style, nav, footer, header, noscript, form, [role=navigation], [role=banner]"):
        hidden.decompose()
    body = soup.find("main") or soup.find("article") or soup.body or soup
    paragraphs = [item.get_text(" ", strip=True) for item in body.find_all(["p", "h1", "h2", "h3", "li"])]
    paragraphs = [paragraph for paragraph in paragraphs if len(paragraph) > 35]
    text = " ".join(paragraphs)
    focused = title + " " + description + " " + text
    ai_signals = sorted({match.group(0).lower() for match in AI_PATTERN.finditer(focused)})[:25]
    automation_signals = sorted({match.group(0).lower() for match in AUTOMATION_PATTERN.finditer(focused)})[:15]
    title = limited_text(title, 25)
    description = limited_text(description, 25 - len(title.split()))
    relevance = "AI_SIGNAL_FOUND_REVIEW_REQUIRED" if ai_signals else "AUTOMATION_OR_DATA_REVIEW_REQUIRED" if automation_signals else "NO_AI_SIGNAL_REVIEW_REQUIRED"
    if not title or len(text) < 200 or re.search(r"access denied|just a moment|page not found|page cannot be found|403 forbidden", title, re.I):
        relevance = "INSUFFICIENT_PAGE_CONTENT"
    return {"canonical_url": canonical, "source_title": title, "source_description_excerpt": description,
            "source_quote_word_count": len(title.split()) + len(description.split()), "visible_characters": len(text),
            "ai_keyword_signals": ai_signals, "automation_keyword_signals": automation_signals,
            "task_tags_automatic_not_gold": [label for label, pattern in TASK_RULES.items() if re.search(pattern, focused, re.I)],
            "published_time_unverified": published_tag.get("content", "") if published_tag and published_tag.attrs else "",
            "triage_status": relevance,
            "organization": "UNKNOWN_REQUIRES_REVIEW", "problem": "UNKNOWN_REQUIRES_REVIEW", "implementation": "UNKNOWN_REQUIRES_REVIEW", "outcome": "UNKNOWN_REQUIRES_REVIEW",
            "semantic_verification": "NOT_HUMAN_VERIFIED_NOT_TRAINING_GOLD", "active_in_prototype": False}


def enrich(candidate, fetcher, frozen_sources):
    result, payload = fetcher.get(candidate["url"])
    record = {"candidate_id": "AXC_" + hashlib.sha256(candidate["key"].encode()).hexdigest()[:14], **candidate,
              "collection_status": result["status"], "access": result, "first_collected_at": timestamp(),
              "existing_frozen_case_ids": frozen_sources.get(normalize_url(candidate["url"]), []),
              "review_status": "UNREVIEWED_CANDIDATE", "active_in_prototype": False}
    if result["status"] == "FETCHED" and "html" in result.get("content_type", "").lower():
        record.update(parse_story(payload, result.get("final_url", candidate["url"])))
        record["existing_frozen_case_ids"] = sorted(set(record["existing_frozen_case_ids"] + frozen_sources.get(record["canonical_url"], [])))
    return record


def export_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            safe = {}
            for field in fields:
                value = row.get(field, "")
                value = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
                safe[field] = "'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")) else value
            writer.writerow(safe)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["discover", "enrich", "all"], default="all")
    parser.add_argument("--limit", type=int, default=1800)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    sources = json.loads((OUTPUT / "sources.json").read_text(encoding="utf-8"))
    if args.phase in {"discover", "all"}:
        discoveries = []
        audits = []
        with ThreadPoolExecutor(max_workers=min(args.workers, 6)) as pool:
            futures = {pool.submit(discover_source, source): source for source in sources}
            for future in as_completed(futures):
                try:
                    rows, source_audit = future.result()
                except Exception as error:
                    rows = []
                    source_audit = [{"publisher": futures[future]["name"], "status": "DISCOVERY_ERROR", "error_type": type(error).__name__}]
                discoveries.extend(rows)
                audits.extend(source_audit)
                (OUTPUT / "discovered_sources.json").write_text(json.dumps(sorted(discoveries, key=lambda row: row["key"]), ensure_ascii=False, indent=2), encoding="utf-8")
                (OUTPUT / "discovery_access_audit.json").write_text(json.dumps(audits, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps({"publisher": futures[future]["name"], "discovered_sources": len(rows)}, ensure_ascii=False), flush=True)
        (OUTPUT / "discovered_sources.json").write_text(json.dumps(sorted(discoveries, key=lambda row: row["key"]), ensure_ascii=False, indent=2), encoding="utf-8")
        (OUTPUT / "discovery_access_audit.json").write_text(json.dumps(audits, ensure_ascii=False, indent=2), encoding="utf-8")
    discoveries = json.loads((OUTPUT / "discovered_sources.json").read_text(encoding="utf-8"))
    if args.phase in {"enrich", "all"}:
        frozen = json.loads((ROOT / "data/v2_3/main_cases_v2_3.json").read_text(encoding="utf-8"))["cases"]
        frozen_sources = defaultdict(list)
        for case in frozen:
            frozen_sources[normalize_url(case["source_url"])].append(case["case_id"])
        grouped = defaultdict(list)
        for row in discoveries:
            grouped[row["publisher"]].append(row)
        selected = []
        while len(selected) < args.limit and any(grouped.values()):
            for publisher in sorted(grouped):
                if grouped[publisher] and len(selected) < args.limit:
                    selected.append(grouped[publisher].pop(0))
        fetched_dir = OUTPUT / "records"
        fetched_dir.mkdir(exist_ok=True)
        fetcher = PublicFetcher()
        pending = []
        records = []
        for row in selected:
            record_path = fetched_dir / (hashlib.sha256(row["key"].encode()).hexdigest()[:14] + ".json")
            if record_path.exists():
                records.append(json.loads(record_path.read_text(encoding="utf-8")))
            else:
                pending.append((row, record_path))
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(enrich, row, fetcher, frozen_sources): path for row, path in pending}
            for future in as_completed(futures):
                try:
                    record = future.result()
                except Exception as error:
                    record = {"key": futures[future].stem, "url": "", "publisher": "PARSER_ERROR", "candidate_id": "AXC_" + futures[future].stem,
                              "collection_status": "PARSER_ERROR", "error_type": type(error).__name__, "existing_frozen_case_ids": []}
                futures[future].write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                records.append(record)
                if len(records) % 50 == 0:
                    print(json.dumps({"processed": len(records), "selected": len(selected), "fetched": sum(row["collection_status"] == "FETCHED" for row in records)}, ensure_ascii=False), flush=True)
        records.sort(key=lambda row: row["key"])
        (OUTPUT / "candidates.json").write_text(json.dumps({"status": "EXPANSION_DISCOVERY_NOT_FROZEN_CORPUS", "collected_at": timestamp(), "candidates": records}, ensure_ascii=False, indent=2), encoding="utf-8")
        fields = ["candidate_id", "publisher", "source_title", "source_description_excerpt", "url", "canonical_url", "collection_status", "triage_status", "ai_keyword_signals", "automation_keyword_signals", "task_tags_automatic_not_gold", "existing_frozen_case_ids", "review_status", "semantic_verification"]
        export_csv(OUTPUT / "candidates.csv", records, fields)
        export_csv(OUTPUT / "discovered_sources.csv", discoveries, ["publisher", "url", "url_aliases", "discovered_from"])
        canonical_groups = defaultdict(list)
        for record in records:
            canonical_groups[record.get("canonical_url", record["url"])].append(record["candidate_id"])
        (OUTPUT / "duplicate_review.json").write_text(json.dumps({key: values for key, values in canonical_groups.items() if len(values) > 1}, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = {"collected_at": timestamp(), "discovered_source_records": len(discoveries), "processed_sources": len(records),
                   "collection_status_counts": dict(Counter(row["collection_status"] for row in records)),
                   "triage_status_counts": dict(Counter(row.get("triage_status", "NOT_FETCHED") for row in records)),
                   "publisher_counts": dict(Counter(row["publisher"] for row in records)), "canonical_duplicate_groups": sum(len(values) > 1 for values in canonical_groups.values()),
                   "overlap_with_frozen_sources": sum(bool(row["existing_frozen_case_ids"]) for row in records),
                   "frozen_corpus_sha256": hashlib.sha256((ROOT / "data/v2_3/main_cases_v2_3.json").read_bytes()).hexdigest(),
                   "active_prototype_cases": 84, "automatically_added_to_prototype": 0, "paid_api_calls": 0,
                   "warning": "URL discovery and keyword signals are not verified AX cases. Full case decomposition, outcome checks and cross-publisher deduplication remain pending."}
        (OUTPUT / "collection_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
