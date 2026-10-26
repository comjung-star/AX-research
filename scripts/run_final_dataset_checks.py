import json
import os
import subprocess
import sys
from datetime import datetime, timezone

from scripts.audit_final_dataset import BASE, OUTPUT, freeze_and_test_status
from scripts.build_ax_expansion_release import ROOT, digest, read_json, write_json
from scripts.validate_final_research_dataset import validate_release


def main():
    destination = ROOT / "docs/prototype-validation/final-dataset-checks"
    destination.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, PYTHONPATH="src;.", PYTHONIOENCODING="utf-8")
    protected = ["data/v2_2", "data/v2_3", "data/v2_4", "data/v2_5", "experiments", "src", "configs"]
    commands = {
        "python_tests": [sys.executable, "-m", "pytest", "-q"],
        "javascript_tests": ["node", "--test", "tests/prototype_research_ui.test.cjs"],
        "installed_dependencies": [sys.executable, "-m", "pip", "check"],
        "protected_paths": ["git", "diff", "--exit-code", BASE, "--", *protected],
        "whitespace": ["git", "-c", "core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol", "diff", "--check"]}
    results = {}
    for name, command in commands.items():
        completed = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, encoding="utf-8", errors="replace")
        log_path = destination / (name + ".txt")
        log_path.write_text(completed.stdout + completed.stderr, encoding="utf-8")
        results[name] = {"passed": completed.returncode == 0, "exit_code": completed.returncode, "command": command,
                         "log": log_path.relative_to(ROOT).as_posix(), "log_sha256": digest(log_path)}
        print(name + ": " + ("PASS" if completed.returncode == 0 else "FAIL"), flush=True)
    release = validate_release()
    frozen, heldout = freeze_and_test_status()
    if not frozen[0] or not heldout[0]:
        raise ValueError("Frozen inputs or heldout qrels failed: " + repr((frozen, heldout)))
    report = {"status": "PASS" if all(result["passed"] for result in results.values()) else "FAIL", "executed_at": datetime.now(timezone.utc).isoformat(),
              "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
              "source_commit_before_check_report": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "checks": results, "release_validation": release, "freeze_validation": frozen, "heldout_validation": heldout,
              "individual_fact_verification_claimed_by_these_checks": False}
    write_json(destination / "report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
