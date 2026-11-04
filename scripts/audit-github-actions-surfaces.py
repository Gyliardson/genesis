"""Confidential, fail-closed audit of currently accessible GitHub Actions text.

Only authenticated GET requests. Run --selftest before --live.
All acquired content remains in private 0700/0600 files under $HOME.
No history/expired artifacts, edit history, attachments or LFS coverage claimed.
"""
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent / "audit-github-text-surfaces.py"
spec = importlib.util.spec_from_file_location("genesis_private_text_audit", BASE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
REPO = "Gyliardson/genesis"
MAX_PAGES = 50
SHA = re.compile(r"^[a-f0-9]{40}$")


def safe_counted_pages(path, key, env):
    items = []
    total = None
    for page in range(1, MAX_PAGES + 1):
        sep = "&" if "?" in path else "?"
        response = base.gh_get(f"{path}{sep}per_page=100&page={page}", env)
        if not isinstance(response, dict):
            raise base.AuditError("Actions API response invalid")
        batch = response.get(key)
        if not isinstance(batch, list) or not all(isinstance(x, dict) for x in batch):
            raise base.AuditError("Actions API batch invalid")
        seen_total = response.get("total_count")
        if not isinstance(seen_total, int) or seen_total < 0:
            raise base.AuditError("Actions API total invalid")
        if total is None:
            total = seen_total
        items.extend(batch)
        if len(batch) < 100:
            if len(items) != total:
                raise base.AuditError("Actions pagination incomplete")
            return items
    raise base.AuditError("Actions pagination limit reached")


def read_annotation_pages(check_id, env):
    return base.paginated(f"repos/{REPO}/check-runs/{check_id}/annotations", env)


def private_log(run_id, corpus, env):
    out = corpus / f"run-{run_id}.log.txt"
    err = corpus / f"run-{run_id}.log.stderr.txt"
    base.private_write(out, "")
    base.private_write(err, "")
    with out.open("wb") as dest, err.open("wb") as errors:
        try:
            result = subprocess.run(
                ["gh", "run", "view", str(run_id), "--repo", REPO, "--log"],
                cwd=corpus, env=env, stdout=dest, stderr=errors, timeout=240, check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
    for file in (out, err):
        if file.is_symlink() or not file.is_file() or stat.S_IMODE(file.stat().st_mode) != 0o600:
            raise base.AuditError("Actions log output privacy invalid")
    return result.returncode == 0 and out.stat().st_size > 0


def gather(root, env):
    info = base.gh_get(f"repos/{REPO}", env)
    if not isinstance(info, dict) or info.get("private") is not True or info.get("full_name") != REPO:
        raise base.AuditError("Actions repo identity/private check failed")
    corpus = root / "records"
    base.private_dir(corpus)
    runs = safe_counted_pages(f"repos/{REPO}/actions/runs", "workflow_runs", env)
    if not runs:
        raise base.AuditError("Actions run inventory empty")

    metrics = {
        "RUNS": len(runs), "JOBS": 0, "READABLE_RUN_LOGS": 0,
        "UNAVAILABLE_RUN_LOGS": 0, "CHECK_RUNS": 0,
        "ANNOTATIONS": 0, "ANNOTATION_FAILURES": 0,
        "API_GAPS": 0, "UNFINISHED_RUNS": 0,
    }
    seen_sha = set()
    seen_check = set()
    for run in runs:
        run_id = run.get("id")
        commit = run.get("head_sha")
        if not isinstance(run_id, int) or run_id <= 0 or not isinstance(commit, str) or not SHA.fullmatch(commit):
            raise base.AuditError("Actions run identity invalid")
        base.private_write(
            corpus / f"run-{run_id}.json",
            json.dumps(run, ensure_ascii=False),
        )
        if run.get("status") != "completed":
            metrics["UNFINISHED_RUNS"] += 1
        try:
            jobs = safe_counted_pages(f"repos/{REPO}/actions/runs/{run_id}/jobs", "jobs", env)
            metrics["JOBS"] += len(jobs)
            base.private_write(
                corpus / f"jobs-{run_id}.json",
                json.dumps(jobs, ensure_ascii=False),
            )
            if not jobs:
                metrics["API_GAPS"] += 1
        except base.AuditError:
            metrics["API_GAPS"] += 1
        if private_log(run_id, corpus, env):
            metrics["READABLE_RUN_LOGS"] += 1
        else:
            metrics["UNAVAILABLE_RUN_LOGS"] += 1

        if commit in seen_sha:
            continue
        seen_sha.add(commit)
        try:
            checks = safe_counted_pages(
                f"repos/{REPO}/commits/{commit}/check-runs", "check_runs", env
            )
            base.private_write(
                corpus / f"checks-{commit}.json", json.dumps(checks, ensure_ascii=False)
            )
            for check in checks:
                check_id = check.get("id")
                if not isinstance(check_id, int) or check_id <= 0:
                    raise base.AuditError("Actions check-run identity invalid")
                if check_id in seen_check:
                    continue
                seen_check.add(check_id)
                metrics["CHECK_RUNS"] += 1
                count = check.get("output", {}).get("annotations_count", 0)
                if not isinstance(count, int) or count < 0:
                    metrics["ANNOTATION_FAILURES"] += 1
                    continue
                if count == 0:
                    continue
                try:
                    items = read_annotation_pages(check_id, env)
                    base.private_write(
                        corpus / f"annotations-{check_id}.json",
                        json.dumps(items, ensure_ascii=False),
                    )
                    metrics["ANNOTATIONS"] += len(items)
                    if len(items) != count:
                        metrics["ANNOTATION_FAILURES"] += 1
                except base.AuditError:
                    metrics["ANNOTATION_FAILURES"] += 1
        except base.AuditError:
            metrics["API_GAPS"] += 1
    return corpus, metrics


def selftest():
    env = base.verify_scanner()
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    fake_token = "ghp_" + "".join(secrets.choice(alphabet) for _ in range(36))
    with tempfile.TemporaryDirectory(prefix="genesis-actions-audit-fixture-") as temp:
        root = Path(temp)
        for name, text, want in (
            ("positive", "token=" + fake_token, "FINDINGS"),
            ("negative", "ordinary synthetic Action log; no tokens", "PASS"),
        ):
            case = root / name
            base.private_dir(case)
            records = case / "records"
            base.private_dir(records)
            base.private_write(records / "synthetic.log.txt", text)
            state, count, _ = base.scan_records(case, records, name, env)
            if state != want or (count == 0) != (want == "PASS"):
                raise base.AuditError("Actions synthetic scanner case failed")
    print("ACTIONS_SELFTEST=PASS")


def main():
    args = sys.argv[1:]
    if args not in (["--selftest"], ["--live"]):
        print("Usage: python scripts/audit-github-actions-surfaces.py --selftest | --live")
        return 64
    try:
        if args == ["--selftest"]:
            selftest()
            return 0
        scanner_env = base.verify_scanner()
        root = Path(tempfile.mkdtemp(prefix="genesis-private-actions-", dir=Path.home()))
        if stat.S_IMODE(root.stat().st_mode) != 0o700:
            raise base.AuditError("Actions private root mode invalid")
        base.private_write(root / "status.private.env", "COLLECTION_STATUS=STARTED\nPREPUBLIC_GATE=FAIL\n")
        env = os.environ.copy()
        env.update(GH_PAGER="cat", PAGER="cat", GIT_TERMINAL_PROMPT="0")
        corpus, metrics = gather(root, env)
        state, findings, _ = base.scan_records(root, corpus, "actions", scanner_env)
        gaps = metrics["UNAVAILABLE_RUN_LOGS"] + metrics["ANNOTATION_FAILURES"] + metrics["API_GAPS"] + metrics["UNFINISHED_RUNS"]
        base.private_write(root / "results.private.json", json.dumps({
            **metrics, "SCAN_STATUS": state, "FINDINGS": findings, "GAPS": gaps,
            "COVERAGE_STATUS": "PARTIAL", "PREPUBLIC_GATE": "FAIL",
        }))
        with (root / "status.private.env").open("w", encoding="utf-8") as out:
            out.write(
                f"COLLECTION_STATUS=PASS\nSCAN_STATUS={state}\n"
                f"KNOWN_GAPS={gaps}\nCOVERAGE_STATUS=PARTIAL\nPREPUBLIC_GATE=FAIL\n"
            )
        print("ACTIONS_COLLECTION=PASS")
        for key, value in metrics.items():
            print(f"{key}={value}")
        print(f"SCAN_STATUS={state}")
        print(f"FINDINGS_COUNT={findings}")
        print(f"KNOWN_GAPS={gaps}")
        print("COVERAGE_STATUS=PARTIAL")
        print("PRIVATE_EVIDENCE_PRESERVED=YES")
        print("PREPUBLIC_GATE=FAIL")
        return 66 if state == "PASS" else 1
    except base.AuditError:
        print("ACTIONS_AUDIT=INCOMPLETE")
        print("PREPUBLIC_GATE=FAIL")
        return 70
    except (OSError, ValueError, TypeError, KeyError):
        print("ACTIONS_AUDIT=INCOMPLETE")
        print("PREPUBLIC_GATE=FAIL")
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
