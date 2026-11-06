"""Fail-closed, attestable publication for prospective D006 v2 (no engine calls).

The mini-plan helper is for synthetic CI fault injection; freeze_a is the only
public A entrypoint, and is NOT authorized by existence of this code.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

from exogenous_v2 import (
    HOLDOUT_NAMESPACE,
    JOBS_SCHEMA,
    POLICY_SEED,
    PYTHON_FREEZE_VERSION,
    RHO,
    SCHEMA,
    Cell,
    arrival_diagnostics,
    arrival_rate,
    canonical,
    exogenous_cell,
    jobs_bytes,
    make_jobs_v2,
    payload_bytes,
    plan_a,
    realized_load,
    sha256,
    validate_seed_partitions,
    validate_workload_seed,
)

from genesis.simulation.core import JobSpecPrivate

DETERMINANT_PATHS = (
    "benchmarks/d006/exogenous_v2.py",
    "benchmarks/d006/freeze_v2.py",
    "src/genesis/simulation/core.py",
    "pyproject.toml",
    "requirements/ci-py311-ubuntu24.04-x86_64.txt",
    "benchmarks/d006/EXOGENOUS_V2.md",
)
MANIFEST_SCHEMA = "D006_Exogenous_v2_FreezeManifest_2"
INTEGRITY_STATUS = "INTEGRITY_COMPLETE_NOT_REVIEWED_NOT_AUTHORIZED"


def assert_freeze_runtime() -> None:
    if sys.implementation.name != "cpython" or sys.version_info[:3] != PYTHON_FREEZE_VERSION:
        raise RuntimeError("freeze requires pinned CPython 3.11.18")
    if sys.platform != "linux":
        raise RuntimeError("no-replace atomic publication requires Linux renameat2")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True,
    ).stdout.strip()


def source_provenance() -> dict[str, object]:
    """Git commit/tree and SHA256 of every byte-determinant; reject dirty tracked files."""
    root = Path(__file__).resolve().parents[2]
    if Path(_git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise RuntimeError("generator not in expected Git checkout")
    files = {}
    for relative in DETERMINANT_PATHS:
        raw = (root / relative).read_bytes()
        blob = _git(root, "rev-parse", f"HEAD:{relative}")
        # Git object SHA1 is an identity check, not the payload integrity digest.
        current = hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()
        if current != blob:
            raise RuntimeError(f"uncommitted or mismatched determinant: {relative}")
        files[relative] = {"git_blob_sha1": blob, "sha256": sha256(raw), "bytes": len(raw)}
    return {
        "git_commit": _git(root, "rev-parse", "--verify", "HEAD^{commit}"),
        "git_tree": _git(root, "rev-parse", "--verify", "HEAD^{tree}"),
        "files": files,
    }


def _write_bytes(path: Path, data: bytes) -> None:
    with path.open("xb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    if path.read_bytes() != data:
        raise OSError(f"write/readback mismatch: {path.name}")


def _verify_staging(stage: Path, records: list[dict[str, object]]) -> None:
    expected = {record["file"] for record in records} | {"manifest.json", "manifest.sha256"}
    if {entry.name for entry in stage.iterdir()} != expected:
        raise RuntimeError("staging file set incomplete or contains extras")
    manifest_bytes = (stage / "manifest.json").read_bytes()
    checksum = (stage / "manifest.sha256").read_bytes()
    if checksum != (sha256(manifest_bytes) + "\n").encode("ascii"):
        raise RuntimeError("manifest checksum mismatch")
    manifest = json.loads(manifest_bytes)
    if canonical(manifest) != manifest_bytes or manifest["records"] != records:
        raise RuntimeError("manifest serialization or records mismatch")
    if manifest["status"] != INTEGRITY_STATUS:
        raise RuntimeError("manifest not integrity-complete")
    for record in records:
        raw = (stage / record["file"]).read_bytes()
        if sha256(raw) != record["payload_sha256"]:
            raise RuntimeError(f"payload checksum mismatch: {record['file']}")
        payload = json.loads(raw)
        cell = Cell(**record["cell"])
        if raw != canonical(payload) or payload["schema"] != SCHEMA:
            raise RuntimeError("noncanonical payload or schema")
        if (payload["cell"] != exogenous_cell(cell)
                or payload["workload_seed"] != record["workload_seed"]
                or payload["cutoff_tick"] is not None
                or len(payload["jobs"]) != cell.n):
            raise RuntimeError("payload envelope/count mismatch")
        jobs = tuple(JobSpecPrivate(**job) for job in payload["jobs"])
        if sha256(jobs_bytes(jobs)) != record["jobs_sha256"]:
            raise RuntimeError("jobs-only checksum mismatch")
        if arrival_diagnostics(cell, jobs) != record["arrivals"]:
            raise RuntimeError("tie/burst diagnostics mismatch")
        if realized_load(cell, jobs) != record["realized"]:
            raise RuntimeError("realized offered load mismatch")


def _atomic_publish_dir(stage: Path, destination: Path) -> None:
    """Linux renameat2(RENAME_NOREPLACE), never replace an existing name."""
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise RuntimeError("renameat2(RENAME_NOREPLACE) unavailable")
    renameat2.argtypes = (
        ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    if renameat2(-100, os.fsencode(stage), -100, os.fsencode(destination), 1) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))
    parent_fd = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)


def _freeze_plan(
    directory: Path,
    entries: tuple[tuple[Cell, int, int], ...],
    provenance: dict[str, object],
) -> Path:
    """Internal entrypoint to exercise small synthetic fixtures, never full A in tests."""
    validate_seed_partitions()
    if not entries or len({(cell.id, seed) for cell, seed, _ in entries}) != len(entries):
        raise ValueError("entries must be nonempty and unique")
    for _, seed, order in entries:
        validate_workload_seed(seed)
        if order in {seed, POLICY_SEED} or HOLDOUT_NAMESPACE[0] <= order <= HOLDOUT_NAMESPACE[1]:
            raise ValueError("order seed collision or reserved namespace")
    if directory.exists() or directory.is_symlink():
        raise FileExistsError(directory)
    if not directory.parent.is_dir():
        raise FileNotFoundError(directory.parent)
    stage = Path(tempfile.mkdtemp(prefix=f".{directory.name}.staging-", dir=directory.parent))
    try:
        records = []
        for cell, seed, order_seed in entries:
            jobs = make_jobs_v2(cell, seed)
            raw = payload_bytes(cell, seed, jobs)
            filename = f"{cell.id}_{seed}.json"
            _write_bytes(stage / filename, raw)
            records.append({
                "cell": asdict(cell), "workload_seed": seed,
                "order_seed": order_seed, "policy_seed": POLICY_SEED,
                "file": filename, "jobs_sha256": sha256(jobs_bytes(jobs)),
                "payload_sha256": sha256(raw), "expected_rho": RHO[cell.load],
                "lambda": arrival_rate(cell),
                "oversize_count": sum(
                    j.cpu_units > cell.cpu or j.memory_units > cell.memory for j in jobs
                ),
                "arrivals": arrival_diagnostics(cell, jobs),
                "realized": realized_load(cell, jobs),
            })
        manifest = {
            "schema": MANIFEST_SCHEMA, "status": INTEGRITY_STATUS,
            "source_provenance": provenance,
            "runtime": {
                "implementation": sys.implementation.name, "python": sys.version,
                "python_version": list(sys.version_info[:3]),
                "python_build": list(platform.python_build()),
                "platform": platform.platform(), "machine": platform.machine(),
            },
            "serialization": {
                "schema": SCHEMA, "jobs_schema": JOBS_SCHEMA,
                "encoding": "utf-8", "sort_keys": True,
                "separators": [",", ":"], "ensure_ascii": False, "allow_nan": False,
                "digest": "SHA-256", "seed_endianness": "big",
                "rng": "CPython MT19937 Random.random/randint",
                "gap": "-log1p(-u)/rate", "arrival_tick": "floor(cumulative_gap)",
            },
            "records": records, "holdout_reserved": list(HOLDOUT_NAMESPACE),
            "holdout_confidential": False,
        }
        manifest_bytes = canonical(manifest)
        _write_bytes(stage / "manifest.json", manifest_bytes)
        _write_bytes(stage / "manifest.sha256", (sha256(manifest_bytes) + "\n").encode())
        _verify_staging(stage, records)
        if source_provenance() != provenance:
            raise RuntimeError("source provenance changed during freeze")
        stage_fd = os.open(stage, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(stage_fd)
        finally:
            os.close(stage_fd)
        _atomic_publish_dir(stage, directory)
        return directory / "manifest.json"
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def verify_freeze(directory: Path) -> dict[str, object]:
    """Readback and environment verification; not independent scientific approval."""
    raw = (directory / "manifest.json").read_bytes()
    manifest = json.loads(raw)
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise RuntimeError("unsupported manifest schema")
    _verify_staging(directory, manifest["records"])
    assert_freeze_runtime()
    if source_provenance() != manifest["source_provenance"]:
        raise RuntimeError("Git tree/files differ from manifest")
    runtime = manifest["runtime"]
    if (runtime["implementation"] != sys.implementation.name
            or runtime["python"] != sys.version
            or runtime["python_version"] != list(sys.version_info[:3])
            or runtime["python_build"] != list(platform.python_build())
            or runtime["platform"] != platform.platform()
            or runtime["machine"] != platform.machine()):
        raise RuntimeError("runtime differs from frozen environment")
    return manifest


def freeze_a(directory: Path) -> Path:
    """Only produces proposed A inputs after separate authorization; never run by CI."""
    assert_freeze_runtime()
    return _freeze_plan(directory, plan_a(), source_provenance())
