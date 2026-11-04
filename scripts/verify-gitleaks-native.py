"""Verify genuine Gitleaks against disposable synthetic Git histories only.

Usage: python scripts/verify-gitleaks-native.py
Does not clone, open, or scan the GENESIS repository.
"""
import hashlib
import json
import os
import secrets
import string
import subprocess
import tempfile
from pathlib import Path

BINARY = Path.home() / ".local/share/genesis-audit/gitleaks-v8.30.1/gitleaks"
EXPECTED_SHA256 = "88f91962aa2f93ac6ab281d553b9e125f5197bbbce38f9f2437f7299c32e5509"


def git(repo, *args, expected=0, env=None):
    result = subprocess.run(
        ["git", "-C", str(repo), *args], env=env,
        capture_output=True, text=True, check=False,
    )
    if result.returncode != expected:
        raise RuntimeError(f"synthetic Git setup failed (exit={result.returncode})")
    return result.stdout


def new_repo(root, name, env):
    repo = root / name
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main", env=env)
    git(repo, "config", "user.name", "Synthetic QA", env=env)
    git(repo, "config", "user.email", "qa@example.invalid", env=env)
    (repo / "config.txt").write_text("mode=base\n", encoding="utf-8")
    git(repo, "add", ".", env=env)
    git(repo, "commit", "-qm", "initial", env=env)
    return repo


def create_private_file(path):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        if (os.fstat(fd).st_mode & 0o777) != 0o600:
            raise RuntimeError("private fixture output permissions not 0600")
    finally:
        os.close(fd)


def main():
    if not BINARY.is_file():
        raise RuntimeError("SCANNER_NOT_FOUND")
    with BINARY.open("rb") as handle:
        actual = hashlib.file_digest(handle, "sha256").hexdigest()
    if actual != EXPECTED_SHA256:
        raise RuntimeError("SCANNER_SHA256_MISMATCH")
    env = os.environ.copy()
    for key in ("GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML", "GITLEAKS_BASELINE_PATH"):
        env.pop(key, None)
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_TERMINAL_PROMPT="0")
    version = subprocess.run([str(BINARY), "version"], env=env, capture_output=True, text=True, check=False)
    if version.returncode != 0 or version.stdout.strip() != "8.30.1":
        raise RuntimeError("SCANNER_VERSION_MISMATCH")
    print("GITLEAKS_BINARY=PASS")

    with tempfile.TemporaryDirectory(prefix="genesis-real-gitleaks-fixtures-") as dirname:
        root = Path(dirname)
        if (root.stat().st_mode & 0o777) != 0o700:
            raise RuntimeError("fixture directory not private")
        alphabet = string.ascii_letters + string.digits
        # Entirely synthetic string matching the default github-pat rule.
        fake = "ghp_" + "".join(secrets.choice(alphabet) for _ in range(36))

        clean = new_repo(root, "clean", env)
        positive = new_repo(root, "positive", env)
        (positive / "config.txt").write_text("token=" + fake + "\n", encoding="utf-8")
        git(positive, "commit", "-qam", "synthetic positive", env=env)

        merge = new_repo(root, "merge", env)
        git(merge, "checkout", "-qb", "feature", env=env)
        (merge / "config.txt").write_text("mode=feature\n", encoding="utf-8")
        git(merge, "commit", "-qam", "feature edit", env=env)
        git(merge, "checkout", "-q", "main", env=env)
        (merge / "config.txt").write_text("mode=main\n", encoding="utf-8")
        git(merge, "commit", "-qam", "main edit", env=env)
        git(merge, "merge", "--no-commit", "--no-ff", "feature", expected=1, env=env)
        (merge / "config.txt").write_text("mode=resolved\ntoken=" + fake + "\n", encoding="utf-8")
        git(merge, "add", "config.txt", env=env)
        git(merge, "commit", "-qm", "synthetic merge resolution", env=env)
        old = git(merge, "log", "-p", "--all", "--full-history", env=env)
        expanded = git(merge, "log", "-p", "-m", "--all", "--full-history", env=env)
        if fake in old or fake not in expanded:
            raise RuntimeError("MERGE_ONLY_GIT_FIXTURE=FAIL")
        print("MERGE_ONLY_GIT_FIXTURE=PASS")

        ignore = root / "empty.ignore"
        create_private_file(ignore)
        for name, repo, expected_exit in (("POSITIVE", positive, 1), ("MERGE", merge, 1), ("CLEAN", clean, 0)):
            report = root / (name.lower() + ".private.json")
            create_private_file(report)
            result = subprocess.run([
                str(BINARY), "git", "--redact=100", "--ignore-gitleaks-allow",
                "--gitleaks-ignore-path", str(ignore),
                "--log-opts=--all --full-history -m",
                "--report-format=json", "--report-path", str(report), str(repo),
            ], cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            contents = report.read_text(encoding="utf-8")
            findings = json.loads(contents) if contents.strip() else []
            if not isinstance(findings, list):
                raise TypeError(f"{name}: unexpected report structure")
            count = sum(f.get("RuleID") == "github-pat" for f in findings)
            passed = (
                result.returncode == expected_exit and
                (count >= 1 if expected_exit else len(findings) == 0) and
                fake not in contents
            )
            print(f"{name}={'PASS' if passed else 'FAIL'} (exit={result.returncode}, recognized={count})")
            if not passed:
                raise RuntimeError(f"{name}_FIXTURE_FAILED")
    print("GITLEAKS_REAL_FIXTURES=PASS")


if __name__ == "__main__":
    main()
