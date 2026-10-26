import argparse
import hashlib
import importlib.metadata
import json
import re
import subprocess
import sys
import urllib.request
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.build_ax_expansion_release import EXPECTED_FROZEN_HASH, FROZEN, ROOT, digest, read_json, write_json


EXACT = {".gitignore", ".gitattributes", "README.md", "HANDOFF.md", "requirements-prototype.txt", "run_prototype.py"}
PREFIXES = ("collections/", "data/v2_4/", "data/v2_5/", "experiments/v24_expansion/", "prototype/",
            "docs/prototype-", "docs/handoff-", "docs/ax-expansion-", "docs/inclusive-data-policy-",
            "scripts/build_ax_", "scripts/collect_ax_", "scripts/finalize_ax_", "scripts/index_ax_",
            "scripts/retry_ax_", "scripts/review_ax_", "scripts/review_all_ax_", "scripts/run_v24_",
            "scripts/validate_ax_", "scripts/prepare_ax_handoff", "scripts/PrototypeLauncher",
            "scripts/install_prototype_desktop", "scripts/prepare_prototype_model", "scripts/validate_prototype_delivery",
            "scripts/validate_strategy_demo", "tests/test_ax_", "tests/test_prototype", "tests/prototype_research_ui")
PATTERNS = {
    "OpenAI_key": re.compile(rb"\bsk-(?:(?:proj|svcacct)-)?[A-Za-z0-9_-]{20,}"),
    "GitHub_token": re.compile(rb"\b(?:ghp_|gho_|ghu_|ghs_|ghr_|github_pat_)[A-Za-z0-9_]{20,}"),
    "AWS_access_key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")}


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT)


def nul_paths(payload):
    return [entry.decode("utf-8") for entry in payload.split(b"\0") if entry]


def secret_scan(paths):
    findings = []
    for filename in paths:
        if filename == ".env" or filename.startswith((".local/", ".venv/", "dist/")) or filename.endswith((".sqlite3", ".sqlite")):
            raise ValueError("Private runtime path must not be published: " + filename)
        payload = (ROOT / filename).read_bytes()
        for kind, pattern in PATTERNS.items():
            for match in pattern.finditer(payload):
                token = match.group(0)
                if kind == "OpenAI_key" and token.startswith(b"sk-test-"):
                    continue
                if kind == "OpenAI_key" and filename.startswith("tests/") and re.fullmatch(rb"sk-(?:[a-z]+-)+[0-9]{10,}", token):
                    continue
                if kind == "OpenAI_key" and re.fullmatch(rb"sk-[a-z]+(?:-[a-z]+){3,}", token):
                    is_public_story_slug = False
                    for url in re.finditer(rb'https?://[^\s"<>,]+', payload[max(0, match.start() - 300):match.end() + 300]):
                        parsed = urlsplit(url.group().decode("utf-8", errors="replace"))
                        if parsed.hostname == "www.microsoft.com" and "/customers/story/" in parsed.path and token.decode() in parsed.path:
                            is_public_story_slug = True
                            break
                    if is_public_story_slug:
                        continue
                findings.append({"path": filename, "kind": kind, "line": payload[:match.start()].count(b"\n") + 1})
    if findings:
        print(json.dumps({"credential_pattern_findings_without_values": findings}, ensure_ascii=False))
        raise ValueError("Recognized credential-like content requires removal before publication")
    return {"scanned_files": len(paths), "credential_pattern_findings": 0, "private_runtime_paths_included": False}


def prepare():
    summary = read_json(ROOT / "data/v2_5/review_summary.json")
    pages = read_json(ROOT / "collections/ax-review-all-2026-10-26/page_check_summary.json")
    assert pages["completed_page_checks"] == pages["expected_page_checks"] == 5686
    assert summary["scope_exclusions"] == 0 and summary["all_collected_inputs_included"] is True
    assert digest(FROZEN) == EXPECTED_FROZEN_HASH
    xml = ET.parse(ROOT / "docs/prototype-validation/handoff-tests.xml").getroot()
    suites = [xml] if xml.tag == "testsuite" else list(xml.iter("testsuite"))
    test_result = {field: sum(int(suite.get(field, "0")) for suite in suites) for field in ("tests", "failures", "errors", "skipped")}
    active = {"reachable": False}
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/api/health", timeout=2) as response:
            health = json.load(response)
        active = {"reachable": True, "case_count": health.get("cases"), "corpus_version": health.get("corpus_version")}
    except Exception:
        pass
    versions = {}
    for package in ("numpy", "torch", "sentence-transformers", "openai", "pydantic", "requests", "pytest"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "NOT_INSTALLED"
    state = {"as_of_kst": datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
             "branch": git("branch", "--show-current").decode().strip(),
             "source_base_commit": "000b7f42f594bd4b57aa55df1661d7ff3750353c",
             "state": "ALL_INPUT_REGISTRY_PREPARED_INCLUSIVE_DENSE_INDEX_AND_ACTIVATION_PENDING",
             "dataset_summary": summary, "source_access_summary": pages, "python_tests": test_result,
             "python_version": sys.version.split()[0], "package_versions": versions, "local_http_observation": active,
             "inclusive_npz_present": (ROOT / "data/v2_5/inclusive_bge_m3.npz").exists(),
             "inclusive_index_manifest_present": (ROOT / "data/v2_5/index_manifest.json").exists(),
             "frozen_sha256": digest(FROZEN), "paid_api_calls_for_collection_and_registration": 0,
             "not_in_git": [".env", ".local", ".venv", "dist", "user feedback DB", "model weights", "private full-text cache"],
             "next_commands": ["python -m scripts.index_ax_inclusive_release --threads 8 --batch-size 32",
                               "python -m scripts.validate_ax_inclusive_release",
                               "python run_prototype.py --corpus inclusive --port 8766 --no-browser"]}
    write_json(ROOT / "docs/handoff-state-2026-10-26.json", state)
    changed = nul_paths(git("diff", "--name-only", "-z"))
    new = nul_paths(git("ls-files", "--others", "--exclude-standard", "-z"))
    paths = sorted({path for path in changed + new if (path in EXACT or path.startswith(PREFIXES))
                    and not path.endswith((".tmp", ".finalizing", ".pyc")) and (ROOT / path).is_file()})
    if any((ROOT / path).stat().st_size >= 100 * 1024 * 1024 for path in paths):
        raise ValueError("File exceeds ordinary GitHub blob size limit")
    scan = secret_scan(paths)
    local = ROOT / ".local/ax-handoff"
    local.mkdir(parents=True, exist_ok=True)
    (local / "stage-paths.bin").write_bytes(b"\0".join(path.encode("utf-8") for path in paths) + b"\0")
    print(json.dumps({**scan, "selected_megabytes": round(sum((ROOT / path).stat().st_size for path in paths) / 1048576, 2),
                      "state_file": "docs/handoff-state-2026-10-26.json"}, ensure_ascii=False))


def index_manifest():
    staged = set(nul_paths(git("diff", "--cached", "--name-only", "-z")))
    scan = secret_scan(sorted(staged))
    files = []
    for entry in git("ls-files", "--stage", "-z").split(b"\0"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
        filename = path.decode("utf-8")
        if filename in staged:
            mode, blob, stage = metadata.decode().split()
            files.append({"path": filename, "git_blob_sha": blob, "mode": mode, "local_bytes": (ROOT / filename).stat().st_size})
    write_json(ROOT / "docs/handoff-files-2026-10-26.json", {"source_base_commit": "000b7f42f594bd4b57aa55df1661d7ff3750353c",
               "files": files, "scan": scan, "note": "Manifest lists the staged snapshot before this manifest itself is added; Git blob hashes are independent of checkout newline conversion."})
    print(json.dumps({"snapshot_files": len(files), **scan}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-manifest", action="store_true")
    arguments = parser.parse_args()
    index_manifest() if arguments.index_manifest else prepare()


if __name__ == "__main__":
    main()
