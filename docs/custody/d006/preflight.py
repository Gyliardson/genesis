"""Read-only D006 A preflight. It NEVER creates inputs or invokes a generator.

Run this tool from a separately reviewed checkout, with two *distinct* pinned
checkouts (custody PR28 and generator PR27). A PASS is NOT execution approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Pins:
    custody_head: str
    custody_tree: str
    generator_head: str
    generator_tree: str
    plan_digest: str
    lock_digest: str


PINS = Pins(
    custody_head="b9f25b0fe4fd9390be05deec396ea1c799d5e83b",
    custody_tree="b4f7b47720fc98fccbaec03782cb8811dc11cac7",
    generator_head="0399e842722e9bffe3063308e622830816744dc3",
    generator_tree="e692edb46a4fd7e0689c83e621c8b1346d4f3fe7",
    plan_digest="77934cf30e3937a9f339f3f6cc4144b9fa67ae2531c0185a8565acd5d0e789ba",
    lock_digest="06614427b37e336407e8e82b1dd235b405232df0f50ee4115b96cf7aa970b5a0",
)

GENERATOR_FILES = (
    "benchmarks/d006/exogenous_v2.py",
    "benchmarks/d006/freeze_v2.py",
    "src/genesis/simulation/core.py",
    "pyproject.toml",
    "requirements/ci-py311-ubuntu24.04-x86_64.txt",
    "benchmarks/d006/EXOGENOUS_V2.md",
)
CUSTODY_FILES = (
    "docs/custody/d006/expected_plan_A_v1.json",
    "docs/custody/d006/lock.json",
    "docs/custody/d006/verify_plan.py",
)
# Screening headroom only, NOT an experimentally validated freeze budget.
MIN_FREE_DISK_BYTES = 1 << 30
MIN_FREE_INODES = 32


class PreflightError(RuntimeError):
    """Any missing/incorrect evidence fails closed before input generation."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value = {}
    for key, item in pairs:
        if key in value:
            raise PreflightError("duplicate JSON key")
        value[key] = item
    return value


def _parse_canonical(raw: bytes) -> object:
    def reject_constant(value: str) -> object:
        raise PreflightError(f"non-JSON constant: {value}")

    try:
        obj = json.loads(raw, object_pairs_hook=_unique, parse_constant=reject_constant)
        if _canonical(obj) != raw:
            raise PreflightError("noncanonical JSON bytes")
    except (ValueError, TypeError, UnicodeError, OverflowError) as exc:
        raise PreflightError("invalid JSON bytes") from exc
    return obj


def _git(root: Path, *args: str) -> bytes:
    try:
        # Even read-only 'git status' can execute a configured fsmonitor hook.
        # Override executable Git hooks and avoid optional index writes.
        safe_env = os.environ.copy()
        safe_env["GIT_OPTIONAL_LOCKS"] = "0"
        process = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null",
             "-C", str(root), *args],
            capture_output=True, check=True, timeout=15, env=safe_env,
        )
        return process.stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise PreflightError(f"Git evidence unavailable: {args[0]}") from exc


def verify_checkout(root: Path, head: str, tree: str, paths: tuple[str, ...]) -> Path:
    """Attest checked-out Git objects and actual tracked bytes, without imports."""
    if root.is_symlink() or not root.is_dir():
        raise PreflightError("checkout must be a real directory, not a symlink")
    resolved = root.resolve(strict=True)
    top = Path(_git(resolved, "rev-parse", "--show-toplevel").decode().strip())
    if top.resolve() != resolved:
        raise PreflightError("checkout path is not the Git top-level directory")
    if _git(resolved, "rev-parse", "HEAD").decode().strip() != head:
        raise PreflightError("wrong checkout commit")
    if _git(resolved, "rev-parse", "HEAD^{tree}").decode().strip() != tree:
        raise PreflightError("wrong checkout tree")
    if _git(resolved, "status", "--porcelain", "--untracked-files=all").strip():
        raise PreflightError("checkout dirty or contains untracked files")
    for relative in paths:
        file = resolved / relative
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(resolved):
            raise PreflightError(f"determinant missing or unsafe: {relative}")
        if file.read_bytes() != _git(resolved, "show", f"HEAD:{relative}"):
            raise PreflightError(f"determinant differs from Git object: {relative}")
    return resolved


def verify_locked_identity(custody: Path, pins: Pins) -> dict[str, object]:
    """The lock's SHA and plan SHA are hard-pinned, never caller-provided."""
    raw_plan = (custody / CUSTODY_FILES[0]).read_bytes()
    raw_lock = (custody / CUSTODY_FILES[1]).read_bytes()
    if len(raw_plan) != 3305 or _sha(raw_plan) != pins.plan_digest:
        raise PreflightError("plan bytes changed")
    if len(raw_lock) != 926 or _sha(raw_lock) != pins.lock_digest:
        raise PreflightError("custody lock bytes changed")
    plan = _parse_canonical(raw_plan)
    lock = _parse_canonical(raw_lock)
    if type(plan) is not dict or type(lock) is not dict:
        raise PreflightError("plan/lock schema mismatch")
    if plan.get("schema") != "D006_ExpectedFreezePlan_v1":
        raise PreflightError("unexpected plan schema")
    if type(plan.get("slots")) is not list or len(plan["slots"]) != 16:
        raise PreflightError("not the 16-slot A plan")
    if lock.get("schema") != "D006_A_SoloCustodyLock_v1":
        raise PreflightError("unexpected lock schema")
    if lock.get("plan") != {
        "schema": "D006_ExpectedFreezePlan_v1", "sha256": pins.plan_digest,
        "bytes": 3305, "slots": 16, "file": "expected_plan_A_v1.json",
    }:
        raise PreflightError("lock does not identify plan")
    code = lock.get("code")
    if type(code) is not dict or code.get("repository") != "Gyliardson/genesis":
        raise PreflightError("unexpected generator repository")
    if (code.get("head") != pins.generator_head
            or code.get("tree") != pins.generator_tree
            or code.get("base_head") != "d2f07a08c470fa7104c09909809f7c0d84aa82e3"):
        raise PreflightError("generator identity not locked")
    authority = lock.get("authority")
    if (type(authority) is not dict
            or authority.get("scope") != "D1-D3_METHOD_ONLY"
            or authority.get("freeze_authorized") is not False
            or authority.get("s1_authorized") is not False):
        raise PreflightError("unauthorized scope in custody lock")
    if lock.get("custody", {}).get("holdout_confidential") is not False:
        raise PreflightError("public holdout may not be marked blind")
    return lock


@dataclass(frozen=True)
class HostEvidence:
    implementation: str
    python: tuple[int, int, int]
    system: str
    machine: str
    os_id: str
    os_version: str
    pythonpath: str | None


def actual_host() -> HostEvidence:
    os_release = {}
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os_release[key] = value.strip().strip('"')
    except OSError as exc:
        raise PreflightError("cannot attest host OS") from exc
    return HostEvidence(
        sys.implementation.name, sys.version_info[:3], platform.system(),
        platform.machine(), os_release.get("ID", ""),
        os_release.get("VERSION_ID", ""), os.environ.get("PYTHONPATH"),
    )


def verify_host(evidence: HostEvidence, lock: dict[str, object]) -> None:
    runtime = lock.get("runtime")
    if type(runtime) is not dict or runtime != {
        "arch": "x86_64", "implementation": "CPython", "platform": "ubuntu-24.04",
        "requirements_path": "requirements/ci-py311-ubuntu24.04-x86_64.txt",
        "version": "3.11.18",
    }:
        raise PreflightError("runtime contract changed")
    if (evidence.implementation != "cpython"
            or evidence.python != (3, 11, 18)
            or evidence.system != "Linux"
            or evidence.machine != "x86_64"
            or evidence.os_id != "ubuntu"
            or evidence.os_version != "24.04"):
        raise PreflightError("host differs from pinned runtime")
    if evidence.pythonpath:
        raise PreflightError("PYTHONPATH must not shadow imported generator")


def verify_output_path(destination: Path, custody: Path, generator: Path,
                       *, available_bytes: int, available_inodes: int) -> None:
    """Read-only path/free-space checks; NOT reservation or quota enforcement."""
    if not destination.is_absolute() or destination.exists() or destination.is_symlink():
        raise PreflightError("destination must be absent and absolute")
    if not destination.name or destination.name in (".", ".."):
        raise PreflightError("invalid destination")
    parent = destination.parent
    if parent.is_symlink() or not parent.is_dir():
        raise PreflightError("destination parent missing or symlinked")
    parent = parent.resolve(strict=True)
    if parent.is_relative_to(custody) or parent.is_relative_to(generator):
        raise PreflightError("destination cannot overlap source checkouts")
    if available_bytes < MIN_FREE_DISK_BYTES or available_inodes < MIN_FREE_INODES:
        raise PreflightError("insufficient unreserved disk/inode headroom")


def verify_preflight(custody: Path, generator: Path, destination: Path, pins: Pins,
                     evidence: HostEvidence, *, disk_bytes: int, inodes: int) -> dict[str, object]:
    # Non-mutating. Race-free resource reservations and future process limits are
    # deliberately NOT claimed by this read-only function.
    custody_root = verify_checkout(custody, pins.custody_head, pins.custody_tree,
                                   CUSTODY_FILES)
    generator_root = verify_checkout(generator, pins.generator_head, pins.generator_tree,
                                     GENERATOR_FILES)
    if custody_root == generator_root:
        raise PreflightError("custody and generator require distinct checkouts")
    lock = verify_locked_identity(custody_root, pins)
    verify_host(evidence, lock)
    verify_output_path(destination, custody_root, generator_root,
                       available_bytes=disk_bytes, available_inodes=inodes)
    return {
        "status": "IDENTITY_AND_HOST_PREVIEW_PASS_ONLY",
        "lock_commit": pins.custody_head,
        "generator_commit": pins.generator_head,
        "plan_sha256": pins.plan_digest,
        "free_disk_bytes_observed": disk_bytes,
        "free_inodes_observed": inodes,
        "freeze_authorized": False,
        "memory_limit_verified": False,
        "wall_timeout_enforced": False,
        "N100000_feasibility_proven": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--custody-checkout", type=Path, required=True)
    parser.add_argument("--generator-checkout", type=Path, required=True)
    parser.add_argument("--output-destination", type=Path, required=True)
    args = parser.parse_args()
    try:
        parent = args.output_destination.parent
        stat = os.statvfs(parent)
        report = verify_preflight(
            args.custody_checkout, args.generator_checkout, args.output_destination,
            PINS, actual_host(), disk_bytes=stat.f_bavail * stat.f_frsize,
            inodes=stat.f_favail,
        )
    except (PreflightError, OSError, UnicodeError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc),
                          "freeze_authorized": False}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
