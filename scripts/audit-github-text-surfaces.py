"""Read-only confidential GitHub Issues/PR text audit; never prints source data.

Usage:
  python scripts/audit-github-text-surfaces.py --selftest
  python scripts/audit-github-text-surfaces.py --live

Does not audit Actions logs, attachments, LFS, forks, hidden refs or other APIs.
Raw findings and source records stay under a new private directory in $HOME.
"""
import hashlib
import json
import os
import re
import secrets
import stat
import string
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "Gyliardson/genesis"
SCANNER = Path.home() / ".local/share/genesis-audit/gitleaks-v8.30.1/gitleaks"
SCANNER_HASH = "88f91962aa2f93ac6ab281d553b9e125f5197bbbce38f9f2437f7299c32e5509"
MAX_API_BYTES = 16 * 1024 * 1024
MAX_PAGES = 50
ATTACHMENTS = re.compile(r"(?:user-attachments|user-images|private-user-images|/assets/)", re.IGNORECASE)


class AuditError(Exception):
    pass


def private_dir(path):
    path.mkdir(mode=0o700)
    if not path.is_dir() or stat.S_IMODE(path.stat().st_mode) != 0o700:
        raise AuditError("private directory mode mismatch")


def private_write(path, data):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "wb") as stream:
        if stat.S_IMODE(os.fstat(stream.fileno()).st_mode) != 0o600:
            raise AuditError("private file mode mismatch")
        stream.write(data.encode("utf-8") if isinstance(data, str) else data)


def run_private(args, env, cwd=None, timeout=120):
    # No source data, API errors or detector stdout/stderr is ever relayed to terminal.
    try:
        return subprocess.run(args, env=env, cwd=cwd, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise AuditError("private subprocess failed") from None


def gh_get(endpoint, env):
    result = run_private(["gh", "api", "--method", "GET", endpoint], env)
    if result.returncode != 0 or len(result.stdout) > MAX_API_BYTES:
        raise AuditError("GitHub API unavailable, incomplete or oversized")
    try:
        return json.loads(result.stdout)
    except (ValueError, UnicodeDecodeError):
        raise AuditError("invalid GitHub API JSON") from None


def paginated(endpoint, env):
    items = []
    for page in range(1, MAX_PAGES + 1):
        sep = "&" if "?" in endpoint else "?"
        batch = gh_get(f"{endpoint}{sep}per_page=100&page={page}", env)
        if not isinstance(batch, list) or not all(isinstance(x, dict) for x in batch):
            raise AuditError("invalid GitHub pagination")
        items.extend(batch)
        if len(batch) < 100:
            return items
    raise AuditError("GitHub pagination limit reached")


def verify_scanner():
    if not SCANNER.is_file() or not os.access(SCANNER, os.X_OK):
        raise AuditError("scanner unavailable")
    with SCANNER.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != SCANNER_HASH:
        raise AuditError("scanner integrity invalid")
    # No GitHub authentication tokens are forwarded to the scanner.
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(Path.home()), "LC_ALL": "C"}
    version = run_private([str(SCANNER), "version"], env)
    if version.returncode != 0 or version.stdout.strip() != b"8.30.1":
        raise AuditError("scanner version invalid")
    return env


def scan_records(root, records, name, scanner_env):
    ignore = root / f"{name}.ignore.private"
    report = root / f"{name}.report.private.json"
    stdout = root / f"{name}.stdout.private"
    stderr = root / f"{name}.stderr.private"
    for path in (ignore, report, stdout, stderr):
        private_write(path, "")
    command = [
        str(SCANNER), "dir", "--redact=100", "--ignore-gitleaks-allow",
        "--gitleaks-ignore-path", str(ignore), "--report-format=json",
        "--report-path", str(report), str(records),
    ]
    # Capture process output to existing 0600 files, not Bash-created redirects.
    with stdout.open("wb") as output, stderr.open("wb") as errors:
        try:
            result = subprocess.run(command, cwd=root, env=scanner_env, stdout=output, stderr=errors, timeout=180, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise AuditError("scanner execution failed") from None
    # Native scanner report writers may replace/chmod their report even when
    # the initial placeholder was created as 0600. Do not trust final mode.
    # The report always stays inside root mode 0700: no outside-user exposure
    # while the scanner is running. Normalize on the file descriptor after it
    # exits; verify regular file, owner, link count and final 0600.
    if root.is_symlink() or stat.S_IMODE(root.stat().st_mode) != 0o700:
        raise AuditError("private scanner directory permissions invalid")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(report, flags)
    try:
        details = os.fstat(fd)
        if not stat.S_ISREG(details.st_mode) or details.st_uid != os.geteuid() or details.st_nlink != 1:
            raise AuditError("scanner report identity invalid")
        if stat.S_IMODE(details.st_mode) != 0o600:
            # On Codespaces, new file creation may ignore expected umask.
            # Read-only fd supports fchmod; do not chmod a pathname/symlink.
            os.fchmod(fd, 0o600)
        if stat.S_IMODE(os.fstat(fd).st_mode) != 0o600:
            raise AuditError("scanner report private mode invalid")
    finally:
        os.close(fd)
    for label, path in (("ignore", ignore), ("report", report),
                        ("stdout", stdout), ("stderr", stderr)):
        if path.is_symlink() or not path.is_file() or stat.S_IMODE(path.stat().st_mode) != 0o600:
            raise AuditError(f"scanner output permissions invalid: {label}")
    try:
        raw = report.read_text(encoding="utf-8")
        findings = json.loads(raw) if raw.strip() else []
    except (ValueError, UnicodeDecodeError):
        raise AuditError("invalid scanner report") from None
    if not isinstance(findings, list):
        raise AuditError("unexpected scanner report")
    if result.returncode == 0 and not findings:
        return "PASS", 0, findings
    if result.returncode == 1 and findings:
        return "FINDINGS", len(findings), findings
    raise AuditError(
        f"scanner/report mismatch (exit={result.returncode}, "
        f"findings={len(findings)}, fixture={name})"
    )


def write_records(root, records):
    corpus = root / "records"
    private_dir(corpus)
    index = []
    links = 0
    for kind, item, fields in records:
        if not isinstance(item, dict):
            raise AuditError("invalid source record")
        content = "\n".join(str(item.get(field) or "") for field in fields)
        links += len(ATTACHMENTS.findall(content))
        if not content.strip():
            continue
        if len(content.encode("utf-8")) > MAX_API_BYTES:
            raise AuditError("record too large")
        private_write(corpus / f"{len(index):07d}.txt", content)
        index.append({"kind": kind, "id": item.get("id"), "number": item.get("number")})
    private_write(root / "index.private.json", json.dumps(index, ensure_ascii=False))
    return corpus, len(index), links


def collect(env):
    info = gh_get(f"repos/{REPO}", env)
    if not isinstance(info, dict) or info.get("full_name") != REPO or info.get("private") is not True:
        raise AuditError("repository identity/private-state mismatch")
    issues_and_prs = paginated(f"repos/{REPO}/issues?state=all", env)
    pulls = paginated(f"repos/{REPO}/pulls?state=all", env)
    comments = paginated(f"repos/{REPO}/issues/comments", env)
    inline = paginated(f"repos/{REPO}/pulls/comments", env)
    reviews = []
    for item in pulls:
        number = item.get("number")
        if not isinstance(number, int) or number <= 0:
            raise AuditError("invalid PR identifier")
        reviews.extend(paginated(f"repos/{REPO}/pulls/{number}/reviews", env))
    issue_count = sum("pull_request" not in item for item in issues_and_prs)
    pr_count = sum("pull_request" in item for item in issues_and_prs)
    if pr_count != len(pulls) or issue_count == 0:
        raise AuditError("issue and pull-request inventory mismatch")
    records = [
        *[("issue-or-pr", item, ("title", "body")) for item in issues_and_prs],
        *[("pull", item, ("title", "body")) for item in pulls],
        *[("issue-comment", item, ("body",)) for item in comments],
        *[("review-comment", item, ("body",)) for item in inline],
        *[("review", item, ("body",)) for item in reviews],
    ]
    counts = {
        "ISSUES": issue_count, "PULL_REQUESTS": len(pulls),
        "ISSUE_COMMENTS": len(comments),
        "REVIEW_COMMENTS": len(inline), "REVIEWS": len(reviews),
    }
    return records, counts


def selftest(root, scanner_env):
    # Real Gitleaks is used only against generated synthetic material.
    alphabet = string.ascii_letters + string.digits
    fake = "ghp_" + "".join(secrets.choice(alphabet) for _ in range(36))
    pos, _, _ = write_records(root / "positive", [("synthetic", {"id": 1, "body": "token=" + fake}, ("body",))])
    neg, _, _ = write_records(root / "negative", [("synthetic", {"id": 2, "body": "ordinary clean content"}, ("body",))])
    print("GITHUB_TEXT_SELFTEST_STAGE=positive", flush=True)
    state1, count1, findings = scan_records(root / "positive", pos, "test-positive", scanner_env)
    if state1 != "FINDINGS" or count1 < 1 or not any(f.get("RuleID") == "github-pat" for f in findings):
        raise AuditError("synthetic positive validation failed")
    print("GITHUB_TEXT_SELFTEST_POSITIVE=PASS", flush=True)

    print("GITHUB_TEXT_SELFTEST_STAGE=negative", flush=True)
    state0, count0, _ = scan_records(root / "negative", neg, "test-negative", scanner_env)
    if state0 != "PASS" or count0 != 0:
        raise AuditError("synthetic negative validation failed")
    print("GITHUB_TEXT_SELFTEST_NEGATIVE=PASS", flush=True)
    print("GITHUB_TEXT_AUDIT_SELFTEST=PASS")


def main():
    mode = sys.argv[1:] if len(sys.argv) > 1 else []
    if mode not in (["--selftest"], ["--live"]):
        print("Usage: python scripts/audit-github-text-surfaces.py --selftest | --live")
        return 64
    try:
        if mode == ["--selftest"]:
            print("GITHUB_TEXT_SELFTEST_STAGE=scanner_preflight", flush=True)
        scanner_env = verify_scanner()
        if mode == ["--selftest"]:
            print("GITHUB_TEXT_SELFTEST_SCANNER=PASS", flush=True)
            with tempfile.TemporaryDirectory(prefix="genesis-gh-text-fixture-") as path:
                root = Path(path)
                private_dir(root / "positive")
                private_dir(root / "negative")
                selftest(root, scanner_env)
            return 0
        root = Path(tempfile.mkdtemp(prefix="genesis-gh-text-audit-", dir=Path.home()))
        if stat.S_IMODE(root.stat().st_mode) != 0o700:
            raise AuditError("private evidence directory mode invalid")
        private_write(root / "status.private.env", "COLLECTION_STATUS=STARTED\nPREPUBLIC_GATE=FAIL\n")
        env = os.environ.copy()
        env["GH_PAGER"] = "cat"
        records, counts = collect(env)
        corpus, text_count, links = write_records(root, records)
        state, finding_count, _ = scan_records(root, corpus, "github-text", scanner_env)
        private_write(root / "results.private.json", json.dumps({
            **counts, "TEXT_RECORDS": text_count, "ATTACHMENT_LINKS": links,
            "SCAN_STATUS": state, "FINDINGS": finding_count,
            "ACTIONS_LOGS": "NOT_RUN", "ATTACHMENTS": "UNVERIFIED",
            "COVERAGE_STATUS": "PARTIAL", "PREPUBLIC_GATE": "FAIL",
        }))
        status_path = root / "status.private.env"
        if stat.S_IMODE(status_path.stat().st_mode) != 0o600 or status_path.is_symlink():
            raise AuditError("status file permissions invalid")
        with status_path.open("w", encoding="utf-8") as status_stream:
            status_stream.write(
                f"COLLECTION_STATUS=PASS\nSCAN_STATUS={state}\n"
                "COVERAGE_STATUS=PARTIAL\nPREPUBLIC_GATE=FAIL\n"
            )
        print("COLLECTION_STATUS=PASS")
        for key, value in counts.items():
            print(f"{key}={value}")
        print(f"TEXT_RECORDS={text_count}")
        print(f"ATTACHMENT_LINKS_POSSIBLE={links}")
        print(f"SCAN_STATUS={state}")
        print(f"FINDINGS_COUNT={finding_count}")
        print("EXTERNAL_COVERAGE=PARTIAL")
        print("PREPUBLIC_GATE=FAIL")
        print("PRIVATE_EVIDENCE_PRESERVED=YES")
        return 66 if state == "PASS" else 1
    except AuditError as exc:
        # Error strings above are fixed or numerical diagnostics only; never
        # include source record contents, API stderr or detector stdout.
        print("GITHUB_TEXT_AUDIT=INCOMPLETE")
        print(f"SAFE_CAUSE={exc}")
        print("PREPUBLIC_GATE=FAIL")
        return 70
    except (OSError, ValueError, TypeError, KeyError):
        print("GITHUB_TEXT_AUDIT=INCOMPLETE")
        print("SAFE_CAUSE=internal_io_or_data_error")
        print("PREPUBLIC_GATE=FAIL")
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
