import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.test_stage1_api_connections import PROMPT, ROOT, RejectRedirects, read_key, summarize_response


OUTPUT = ROOT / "docs/gemini-connection-2026-10-27"
RESERVATIONS = ROOT / ".local/gemini-connection-2026-10-27"
PROFILE = json.loads((ROOT / "configs/gemini_connection_20261027.json").read_text(encoding="utf-8"))
CASES = {
    "legacy_original": {"model": "gemini-2.5-flash-lite", "max_output": 64, "thinking": "legacy", "input_price": 0.10, "output_price": 0.40},
    "legacy_minimal": {"model": "gemini-2.5-flash-lite", "max_output": 64, "thinking": None, "input_price": 0.10, "output_price": 0.40},
    "current_minimal": {"model": PROFILE["model"], "max_output": PROFILE["max_output_tokens"], "thinking": PROFILE["thinking_level"], "input_price": PROFILE["standard_input_usd_per_million_tokens"], "output_price": PROFILE["standard_output_usd_per_million_tokens"]},
    "current_extended_timeout": {"model": PROFILE["model"], "max_output": PROFILE["max_output_tokens"], "thinking": PROFILE["thinking_level"], "input_price": PROFILE["standard_input_usd_per_million_tokens"], "output_price": PROFILE["standard_output_usd_per_million_tokens"], "timeout": PROFILE["timeout_seconds"]},
}
ALLOWED_STATUSES = {"NOT_FOUND", "INVALID_ARGUMENT", "PERMISSION_DENIED", "RESOURCE_EXHAUSTED", "UNAUTHENTICATED", "FAILED_PRECONDITION", "UNAVAILABLE", "INTERNAL"}


def safe_error(body):
    try:
        error = json.loads(body).get("error", {})
    except (ValueError, AttributeError):
        error = {}
    message = str(error.get("message", "")).lower()
    status = error.get("status")
    return {
        "rpc_status": status if isinstance(status, str) and status in ALLOWED_STATUSES else "UNCLASSIFIED",
        "message_mentions_model_not_found": "not found" in message,
        "message_mentions_unsupported_method": "not supported" in message or "unsupported" in message,
        "message_mentions_api_version": "api version" in message,
        "message_mentions_api_key_problem": "key not valid" in message or "api_key_invalid" in message,
        "message_mentions_billing": "billing" in message or "credit" in message,
        "message_mentions_legacy_access_policy": "previously used" in message or "existing user" in message,
        "raw_error_body_saved": False,
    }


def build_case(case_name):
    case = CASES[case_name]
    if case_name == "legacy_original":
        return {"contents": [{"parts": [{"text": PROMPT}]}], "generationConfig": {"maxOutputTokens": 64, "thinkingConfig": {"thinkingBudget": 0}}}
    config = {"maxOutputTokens": case["max_output"]}
    if case["thinking"] == "minimal":
        config["thinkingConfig"] = {"thinkingLevel": "minimal"}
    return {"contents": [{"parts": [{"text": PROMPT}]}], "generationConfig": config}


def reserve(case_name, metadata):
    RESERVATIONS.mkdir(parents=True, exist_ok=True)
    prefix = "metadata_" if metadata else "generation_"
    try:
        with (RESERVATIONS / (prefix + case_name + ".json")).open("x", encoding="utf-8") as handle:
            json.dump({"reserved": True, "scope": "USER_AUTHORIZED_GEMINI_DIAGNOSIS_ONLY"}, handle)
    except FileExistsError:
        return False
    return True


def execute(case_name, key, metadata=False):
    case = CASES[case_name]
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + case["model"]
    body = None if metadata else build_case(case_name)
    if not metadata:
        url += ":generateContent"
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    request = urllib.request.Request(url, data=None if metadata else json.dumps(body).encode("utf-8"),
                                     headers=headers, method="GET" if metadata else "POST")
    result = {"case": case_name, "requested_model": case["model"], "api_version": "v1beta",
              "request_kind": "MODEL_METADATA_GET" if metadata else "TEXT_GENERATION_POST",
              "attempts": 1, "automatic_retries": 0, "time_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
              "max_output_tokens": None if metadata else case["max_output"],
              "request_body_sha256": None if metadata else hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()}
    start = time.monotonic()
    try:
        with urllib.request.build_opener(RejectRedirects()).open(request, timeout=case.get("timeout", 45)) as response:
            payload = json.loads(response.read(1_000_000))
            result["http_status"] = response.status
            if metadata:
                result.update(status="METADATA_SUCCESS", supports_generate_content="generateContent" in payload.get("supportedGenerationMethods", []))
            else:
                measured = summarize_response("gemini", payload)
                model = payload.get("modelVersion")
                measured["response_model"] = model if isinstance(model, str) and re.fullmatch(r"gemini-[A-Za-z0-9._-]{1,90}", model) else None
                input_tokens = measured["input_tokens"]
                output_tokens = measured["output_tokens_including_reported_thinking"]
                measured["estimated_standard_token_cost_usd"] = (input_tokens * case["input_price"] + output_tokens * case["output_price"]) / 1_000_000 if input_tokens is not None and output_tokens is not None else None
                result.update(measured)
                if result["status"] == "SUCCESS" and not result["response_matches_OK"]:
                    result["status"] = "GENERATED_TEXT_BUT_NOT_EXPECTED_OK"
    except urllib.error.HTTPError as error:
        result.update(status="GENERATION_HTTP_ERROR" if not metadata else "METADATA_HTTP_ERROR", http_status=error.code,
                      error=safe_error(error.read(65536).decode("utf-8", errors="replace")))
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        result.update(status="TRANSPORT_ERROR_NO_RETRY_POSSIBLY_BILLED", http_status=None,
                      transport_timeout=isinstance(error, TimeoutError) or isinstance(getattr(error, "reason", None), TimeoutError))
    except (ValueError, TypeError, KeyError, AttributeError):
        result.update(status="UNPARSEABLE_RESPONSE_NO_RETRY", http_status=None)
    result["elapsed_seconds"] = round(time.monotonic() - start, 3)
    result["timeout_seconds"] = case.get("timeout", 45)
    if key in json.dumps(result):
        raise RuntimeError("Report rejected because a sensitive value was detected")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--metadata", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    key = read_key("GEMINI_API_KEY")
    if not key:
        print(json.dumps({"status": "KEY_MISSING_NO_REQUEST"}))
        return 2
    if not args.execute:
        print(json.dumps({"status": "READY_NO_REQUEST", "case": args.case, "metadata": args.metadata}))
        return 0
    estimate = sum((1000 * case["input_price"] + case["max_output"] * case["output_price"]) / 1_000_000 for case in CASES.values())
    if estimate > 0.01:
        raise RuntimeError("Diagnostic budget estimate exceeds USD 0.01")
    if not reserve(args.case, args.metadata):
        print(json.dumps({"status": "ALREADY_RESERVED_NO_REQUEST", "case": args.case}))
        return 2
    result = execute(args.case, key, args.metadata)
    result["scope"] = "GEMINI_CONNECTION_ONLY_NO_FULL_LABELING_NO_TEST"
    result["maximum_generation_requests_in_this_diagnosis"] = len(CASES)
    result["estimated_cost_reservation_for_all_cases_usd"] = estimate
    OUTPUT.mkdir(parents=True, exist_ok=True)
    prefix = "metadata_" if args.metadata else "generation_"
    (OUTPUT / (prefix + args.case + ".json")).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in ("SUCCESS", "METADATA_SUCCESS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
