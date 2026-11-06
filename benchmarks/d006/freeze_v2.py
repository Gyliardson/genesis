"""Fail-closed, attestable publication for prospective D006 v2 (no engine calls).

The mini-plan helper is for synthetic CI fault injection; freeze_a is the only
public A entrypoint, and is NOT authorized by existence of this code.
"""
from __future__ import annotations

import ctypes
import hashlib
import inspect
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

import exogenous_v2 as imported_generator
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
EXPECTED_PLAN_SCHEMA = "D006_ExpectedFreezePlan_v1"


def _plan_slots(entries: tuple[tuple[Cell, int, int], ...]) -> list[dict[str, object]]:
    """Complete, ordered identity independent of any received freeze manifest."""
    return [
        {
            "cell": asdict(cell), "workload_seed": seed,
            "order_seed": order, "policy_seed": POLICY_SEED,
            "file": f"{cell.id}_{seed}.json",
        }
        for cell, seed, order in entries
    ]


def expected_plan_sha256(entries: tuple[tuple[Cell, int, int], ...]) -> str:
    """Candidate identity, NOT approval/ratification of a proposed plan."""
    return sha256(canonical({"schema": EXPECTED_PLAN_SCHEMA, "slots": _plan_slots(entries)}))


def _require_external_plan_identity(
    entries: tuple[tuple[Cell, int, int], ...], external_sha256: str | None,
) -> None:
    if not isinstance(external_sha256, str) or re.fullmatch(r"[0-9a-f]{64}", external_sha256) is None:
        raise RuntimeError("external expected-plan SHA256 required (64 lowercase hex digits)")
    if expected_plan_sha256(entries) != external_sha256:
        raise RuntimeError("external expected-plan SHA256 differs from prescribed plan")


def _a_entries() -> tuple[tuple[Cell, int, int], ...]:
    entries = plan_a()
    expected_ids = [f"A{i:02d}" for i in range(1, 9) for _ in range(2)]
    if (len(entries) != 16
            or [cell.id for cell, _, _ in entries] != expected_ids
            or any(entries[i][1] == entries[i + 1][1] for i in range(0, 16, 2))):
        raise RuntimeError("proposed A plan must have 16 slots, 8 cells, 2 seeds per cell")
    return entries



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
    # The tracked generator file alone does not prove imported symbols came
    # from it: PYTHONPATH can shadow the module (even with identical bytes).
    generator_path = (root / "benchmarks/d006/exogenous_v2.py").resolve()
    imported_path = Path(inspect.getfile(imported_generator)).resolve()
    if imported_path != generator_path:
        raise RuntimeError("imported generator does not originate from tracked source")
    for name in (
        "Cell", "arrival_diagnostics", "arrival_rate", "canonical",
        "exogenous_cell", "jobs_bytes", "make_jobs_v2", "payload_bytes",
        "plan_a", "realized_load", "sha256", "validate_seed_partitions",
        "validate_workload_seed",
    ):
        symbol = globals()[name]
        if getattr(imported_generator, name) is not symbol:
            raise RuntimeError(f"imported generator symbol binding differs: {name}")
        if (inspect.isfunction(symbol) or inspect.isclass(symbol)) and (
            Path(inspect.getfile(symbol)).resolve() != generator_path
        ):
            raise RuntimeError(f"imported generator symbol has foreign origin: {name}")
    if sha256(imported_path.read_bytes()) != files["benchmarks/d006/exogenous_v2.py"]["sha256"]:
        raise RuntimeError("imported generator bytes differ from tracked source")
    # A wheel-installed Core may differ from the checked-out Core. Attest
    # the actually imported class implementation, not only a source filename.
    imported_core = Path(inspect.getfile(JobSpecPrivate)).resolve()
    if sha256(imported_core.read_bytes()) != files["src/genesis/simulation/core.py"]["sha256"]:
        raise RuntimeError("imported Core bytes differ from tracked Core")
    return {
        "git_commit": _git(root, "rev-parse", "--verify", "HEAD^{commit}"),
        "git_tree": _git(root, "rev-parse", "--verify", "HEAD^{tree}"),
        "files": files,
        "imported_generator_sha256": sha256(imported_path.read_bytes()),
        "imported_core_sha256": sha256(imported_core.read_bytes()),
    }


def _write_bytes(path: Path, data: bytes) -> None:
    with path.open("xb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    if path.read_bytes() != data:
        raise OSError(f"write/readback mismatch: {path.name}")



def _serialization_metadata() -> dict[str, object]:
    """Versioned byte-level serializer contract shared by writer and verifier."""
    return {
        "schema": SCHEMA, "jobs_schema": JOBS_SCHEMA,
        "encoding": "utf-8", "sort_keys": True,
        "separators": [",", ":"], "ensure_ascii": False, "allow_nan": False,
        "digest": "SHA-256", "seed_endianness": "big",
        "rng": "CPython MT19937 Random.random/randint",
        "gap": "-log1p(-u)/rate", "arrival_tick": "floor(cumulative_gap)",
    }


def _runtime_metadata() -> dict[str, object]:
    return {
        "implementation": sys.implementation.name, "python": sys.version,
        "python_version": list(sys.version_info[:3]),
        "python_build": list(platform.python_build()),
        "platform": platform.platform(), "machine": platform.machine(),
    }


def _canonical_json(raw: bytes, label: str) -> object:
    """Forbid repeated keys, noncanonical numeric encodings, and non-JSON constants."""
    def unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result = {}
        for key, value in pairs:
            if key in result:
                raise RuntimeError(f"duplicate JSON key in {label}: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=unique_pairs)
        serialized = canonical(value)
    except (ValueError, UnicodeError, TypeError, OverflowError) as exc:
        raise RuntimeError(f"invalid canonical JSON in {label}") from exc
    if serialized != raw:
        raise RuntimeError(f"noncanonical JSON in {label}")
    return value


def _exact_fields(value: object, names: tuple[str, ...], label: str) -> dict:
    if type(value) is not dict or set(value) != set(names):
        raise RuntimeError(f"{label} schema/fields mismatch")
    return value


def _exact_type(value: object, kind: type, label: str) -> None:
    if type(value) is not kind:
        raise RuntimeError(f"{label} must have JSON type {kind.__name__}")


def _digest(value: object, label: str, length: int = 64) -> None:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{" + str(length) + r"}", value) is None:
        raise RuntimeError(f"{label} invalid lowercase hex digest")


def _cell_from_record(value: object) -> Cell:
    cell = _exact_fields(
        value, ("id", "n", "cpu", "memory", "load", "family", "policy"), "record.cell",
    )
    for name in ("id", "load", "family", "policy"):
        _exact_type(cell[name], str, f"record.cell.{name}")
    for name in ("n", "cpu", "memory"):
        _exact_type(cell[name], int, f"record.cell.{name}")
    try:
        return Cell(**cell)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("invalid record.cell configuration") from exc


def _record_schema(record: object) -> Cell:
    data = _exact_fields(record, (
        "cell", "workload_seed", "order_seed", "policy_seed", "file",
        "jobs_sha256", "payload_sha256", "expected_rho", "lambda",
        "oversize_count", "arrivals", "realized",
    ), "record")
    cell = _cell_from_record(data["cell"])
    for name in ("workload_seed", "order_seed", "policy_seed", "oversize_count"):
        _exact_type(data[name], int, f"record.{name}")
    for name in ("expected_rho", "lambda"):
        _exact_type(data[name], float, f"record.{name}")
    _exact_type(data["file"], str, "record.file")
    for name in ("jobs_sha256", "payload_sha256"):
        _digest(data[name], f"record.{name}")
    try:
        validate_workload_seed(data["workload_seed"])
    except ValueError as exc:
        raise RuntimeError("invalid record.workload_seed") from exc
    order = data["order_seed"]
    if (order < 0 or order in (data["workload_seed"], POLICY_SEED)
            or HOLDOUT_NAMESPACE[0] <= order <= HOLDOUT_NAMESPACE[1]):
        raise RuntimeError("invalid record.order_seed")
    if data["policy_seed"] != POLICY_SEED:
        raise RuntimeError("record.policy_seed differs from versioned implementation")
    if data["file"] != f"{cell.id}_{data['workload_seed']}.json":
        raise RuntimeError("record.file differs from versioned filename")
    arrivals = _exact_fields(data["arrivals"], (
        "arrival_ties", "simultaneous_arrival_ticks", "max_simultaneous_arrivals",
        "burst_group_count", "last_burst_size",
    ), "record.arrivals")
    for name, value in arrivals.items():
        _exact_type(value, int, f"record.arrivals.{name}")
    realized = _exact_fields(data["realized"], (
        "arrival_window_ticks", "cpu_work_ticks", "memory_work_ticks",
        "rho_cpu_realized", "rho_memory_realized", "rho_max_realized",
    ), "record.realized")
    for name in ("arrival_window_ticks", "cpu_work_ticks", "memory_work_ticks"):
        _exact_type(realized[name], int, f"record.realized.{name}")
    for name in ("rho_cpu_realized", "rho_memory_realized", "rho_max_realized"):
        _exact_type(realized[name], float, f"record.realized.{name}")
    return cell


def _manifest_schema(manifest: object) -> list:
    data = _exact_fields(manifest, (
        "schema", "status", "source_provenance", "runtime", "serialization",
        "records", "holdout_reserved", "holdout_confidential",
    ), "manifest")
    if data["schema"] != MANIFEST_SCHEMA or type(data["schema"]) is not str:
        raise RuntimeError("unsupported manifest schema")
    if data["status"] != INTEGRITY_STATUS or type(data["status"]) is not str:
        raise RuntimeError("manifest not integrity-complete")
    serialization = _exact_fields(
        data["serialization"], tuple(_serialization_metadata()), "serialization",
    )
    if canonical(serialization) != canonical(_serialization_metadata()):
        raise RuntimeError("serialization differs from versioned implementation")
    reserved = data["holdout_reserved"]
    if (type(reserved) is not list or len(reserved) != len(HOLDOUT_NAMESPACE)
            or any(type(value) is not int for value in reserved)
            or reserved != list(HOLDOUT_NAMESPACE)):
        raise RuntimeError("holdout_reserved differs from versioned implementation")
    if data["holdout_confidential"] is not False:
        raise RuntimeError("holdout_confidential must be boolean false (public)")
    runtime = _exact_fields(data["runtime"], tuple(_runtime_metadata()), "runtime")
    if canonical(runtime) != canonical(_runtime_metadata()):
        raise RuntimeError("runtime differs from frozen environment")
    provenance = _exact_fields(data["source_provenance"], (
        "git_commit", "git_tree", "files",
        "imported_generator_sha256", "imported_core_sha256",
    ), "source_provenance")
    for name in ("git_commit", "git_tree"):
        _digest(provenance[name], f"source_provenance.{name}", 40)
    for name in ("imported_generator_sha256", "imported_core_sha256"):
        _digest(provenance[name], f"source_provenance.{name}")
    files = _exact_fields(provenance["files"], DETERMINANT_PATHS, "source_provenance.files")
    for name, file_info in files.items():
        file_info = _exact_fields(
            file_info, ("git_blob_sha1", "sha256", "bytes"), f"provenance.files.{name}",
        )
        _digest(file_info["git_blob_sha1"], f"provenance.{name}.git_blob_sha1", 40)
        _digest(file_info["sha256"], f"provenance.{name}.sha256")
        _exact_type(file_info["bytes"], int, f"provenance.{name}.bytes")
        if file_info["bytes"] < 0:
            raise RuntimeError("negative provenance file size")
    records = data["records"]
    if type(records) is not list or not records:
        raise RuntimeError("manifest records must be a nonempty JSON array")
    for record in records:
        _record_schema(record)
    filenames = [record["file"] for record in records]
    if len(set(filenames)) != len(filenames):
        raise RuntimeError("duplicate record filename")
    return records


def _verify_staging(stage: Path, records: list[dict[str, object]]) -> None:
    expected = {record["file"] for record in records} | {"manifest.json", "manifest.sha256"}
    if {entry.name for entry in stage.iterdir()} != expected:
        raise RuntimeError("staging file set incomplete or contains extras")
    manifest_bytes = (stage / "manifest.json").read_bytes()
    checksum = (stage / "manifest.sha256").read_bytes()
    if checksum != (sha256(manifest_bytes) + "\n").encode("ascii"):
        raise RuntimeError("manifest checksum mismatch")
    manifest = _canonical_json(manifest_bytes, "manifest")
    validated_records = _manifest_schema(manifest)
    if canonical(validated_records) != canonical(records):
        raise RuntimeError("manifest serialization or records mismatch")
    for record in validated_records:
        raw = (stage / record["file"]).read_bytes()
        if sha256(raw) != record["payload_sha256"]:
            raise RuntimeError(f"payload checksum mismatch: {record['file']}")
        payload = _canonical_json(raw, f"payload {record['file']}")
        _exact_fields(payload, ("schema", "cell", "workload_seed", "cutoff_tick", "jobs"),
                      "payload")
        cell = _cell_from_record(record["cell"])
        if payload["schema"] != SCHEMA:
            raise RuntimeError("noncanonical payload or schema")
        if (payload["cell"] != exogenous_cell(cell)
                or payload["workload_seed"] != record["workload_seed"]
                or payload["cutoff_tick"] is not None
                or len(payload["jobs"]) != cell.n):
            raise RuntimeError("payload envelope/count mismatch")
        jobs = tuple(JobSpecPrivate(**job) for job in payload["jobs"])
        if sha256(jobs_bytes(jobs)) != record["jobs_sha256"]:
            raise RuntimeError("jobs-only checksum mismatch")
        # A self-consistent manifest/payload rewrite must still fail replay.
        expected = payload_bytes(cell, record["workload_seed"], make_jobs_v2(
            cell, record["workload_seed"],
        ))
        if raw != expected:
            raise RuntimeError("workload replay bytes mismatch")
        if canonical(arrival_diagnostics(cell, jobs)) != canonical(record["arrivals"]):
            raise RuntimeError("tie/burst diagnostics mismatch")
        if canonical(realized_load(cell, jobs)) != canonical(record["realized"]):
            raise RuntimeError("realized offered load mismatch")
        if (record["expected_rho"] != RHO[cell.load]
                or canonical(record["expected_rho"]) != canonical(RHO[cell.load])):
            raise RuntimeError("expected_rho differs from cell load")
        if canonical(record["lambda"]) != canonical(arrival_rate(cell)):
            raise RuntimeError("lambda differs from cell arrival rate")
        oversize = sum(
            job.cpu_units > cell.cpu or job.memory_units > cell.memory for job in jobs
        )
        if record["oversize_count"] != oversize:
            raise RuntimeError("oversize_count differs from effective jobs")


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
            "runtime": _runtime_metadata(),
            "serialization": _serialization_metadata(),
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
    """Generic fixture integrity/replay only; NEVER sufficient for A-plan coverage."""
    raw = (directory / "manifest.json").read_bytes()
    manifest = _canonical_json(raw, "manifest")
    _manifest_schema(manifest)
    _verify_staging(directory, manifest["records"])
    assert_freeze_runtime()
    if canonical(source_provenance()) != canonical(manifest["source_provenance"]):
        raise RuntimeError("Git tree/files differ from manifest")
    return manifest


def verify_expected_plan(
    directory: Path,
    expected_entries: tuple[tuple[Cell, int, int], ...],
    external_sha256: str | None = None,
) -> dict[str, object]:
    """Strict coverage gate; external lock must precede the future freeze.

    Synthetic test plans may use this without generating a single A workload.
    """
    _require_external_plan_identity(expected_entries, external_sha256)
    manifest = _canonical_json((directory / "manifest.json").read_bytes(), "manifest")
    received = manifest.get("records") if type(manifest) is dict else None
    expected = _plan_slots(expected_entries)
    if type(received) is not list or len(received) != len(expected):
        raise RuntimeError("expected plan records mismatch: wrong slot count")
    fields = ("cell", "workload_seed", "order_seed", "policy_seed", "file")
    if any(type(record) is not dict or any(field not in record for field in fields)
           for record in received):
        raise RuntimeError("expected plan records mismatch: missing descriptor fields")
    slots = [{field: record[field] for field in fields} for record in received]
    # Authenticate received bytes, not just the expected identity. Dict equality
    # treats JSON integer 820111 and float 820111.0 as equal; SHA256 does not.
    received_sha256 = sha256(canonical({"schema": EXPECTED_PLAN_SCHEMA, "slots": slots}))
    if received_sha256 != external_sha256 or canonical(slots) != canonical(expected):
        raise RuntimeError("expected plan records mismatch: cells/seeds/files/order")
    return verify_freeze(directory)


def verify_a(directory: Path, external_sha256: str | None = None) -> dict[str, object]:
    """Strict 16-slot proposed A plan; not scientific review or S0 ratification."""
    return verify_expected_plan(directory, _a_entries(), external_sha256)


def freeze_a(directory: Path, external_sha256: str | None = None) -> Path:
    """Only produce proposed A inputs after external lock and separate authority."""
    assert_freeze_runtime()
    entries = _a_entries()
    _require_external_plan_identity(entries, external_sha256)
    destination = _freeze_plan(directory, entries, source_provenance())
    verify_a(directory, external_sha256)
    return destination
