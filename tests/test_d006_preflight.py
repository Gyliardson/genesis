"""D006 A-preflight gates use tiny fake Git checkouts, NEVER A payloads."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "docs/custody/d006/preflight.py"
spec = importlib.util.spec_from_file_location("d006_a_preflight_v1", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def commit(repo):
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True,
                   capture_output=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=d006@example.invalid",
                    "-c", "user.name=D006 test", "commit", "-qm", "synthetic"],
                   check=True, capture_output=True)
    return git(repo, "rev-parse", "HEAD"), git(repo, "rev-parse", "HEAD^{tree}")


def init_repo(path):
    path.mkdir()
    subprocess.run(["git", "init", "-q", str(path)], check=True,
                   capture_output=True)


@pytest.fixture
def synthetic(tmp_path):
    """Fake tiny source bytes/commits, not D006 jobs or simulator imports."""
    custody = tmp_path / "custody"
    generator = tmp_path / "generator"
    init_repo(custody)
    init_repo(generator)
    for source in mod.GENERATOR_FILES:
        file = generator / source
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("# tiny dummy, never imported\n")
    g_head, g_tree = commit(generator)
    custody_dir = custody / "docs/custody/d006"
    custody_dir.mkdir(parents=True)
    src = ROOT / "docs/custody/d006"
    plan = (src / "expected_plan_A_v1.json").read_bytes()
    # Construct a synthetic version of the real *approved=false* lock with
    # only generator HEAD/tree changed, retaining all other normative fields.
    locked = json.loads((src / "lock.json").read_bytes())
    locked["code"]["head"] = g_head
    locked["code"]["tree"] = g_tree
    lock = mod._canonical(locked)
    assert len(lock) == 926
    (custody_dir / "lock.json").write_bytes(lock)
    (custody_dir / "expected_plan_A_v1.json").write_bytes(plan)
    (custody_dir / "verify_plan.py").write_text("# pinned tiny stub, never executed\n")
    c_head, c_tree = commit(custody)
    pins = mod.Pins(c_head, c_tree, g_head, g_tree, hashlib.sha256(plan).hexdigest(),
                    hashlib.sha256(lock).hexdigest())
    fake = mod.HostEvidence("cpython", (3, 11, 18), "Linux", "x86_64",
                            "ubuntu", "24.04", None)
    return custody, generator, tmp_path / "future-A", pins, fake


def run_preview(specimen, *, disk_bytes=2 << 30, inodes=1000, host=None,
                destination=None):
    c, g, output, pins, fake = specimen
    return mod.verify_preflight(c, g, output if destination is None else destination,
                                pins, fake if host is None else host,
                                disk_bytes=disk_bytes, inodes=inodes)


def test_production_pins_are_exact_and_have_no_run_permission():
    result = mod.verify_locked_identity(ROOT, mod.PINS)
    assert result["authority"]["freeze_authorized"] is False
    assert result["authority"]["s1_authorized"] is False
    assert result["code"]["head"] == mod.PINS.generator_head


def test_positive_is_read_only_preview_not_execution_authorization(synthetic):
    result = run_preview(synthetic)
    assert result["status"] == "IDENTITY_AND_HOST_PREVIEW_PASS_ONLY"
    assert result["freeze_authorized"] is False
    assert result["wall_timeout_enforced"] is False
    assert result["memory_limit_verified"] is False
    assert result["N100000_feasibility_proven"] is False
    assert not synthetic[2].exists()


@pytest.mark.parametrize("rel", ["expected_plan_A_v1.json", "lock.json"])
def test_rehashing_local_manifest_cannot_override_pinned_bytes(synthetic, rel):
    path = synthetic[0] / "docs/custody/d006" / rel
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(mod.PreflightError):
        run_preview(synthetic)


def test_source_checkout_mutation_and_new_untracked_file_fail(synthetic):
    path = synthetic[1] / mod.GENERATOR_FILES[0]
    path.write_text("# changed outside Git\n")
    with pytest.raises(mod.PreflightError, match="dirty"):
        run_preview(synthetic)
    path.write_text("# tiny dummy, never imported\n")
    (synthetic[1] / "extra.txt").write_text("unexpected")
    with pytest.raises(mod.PreflightError, match="dirty"):
        run_preview(synthetic)


def test_future_commit_invalidates_pinned_head_even_with_valid_worktree(synthetic):
    repo = synthetic[1]
    path = repo / mod.GENERATOR_FILES[0]
    path.write_text("# other exact commit\n")
    commit(repo)
    with pytest.raises(mod.PreflightError, match="wrong checkout commit"):
        run_preview(synthetic)


@pytest.mark.parametrize("host", [
    mod.HostEvidence("cpython", (3, 13, 5), "Linux", "x86_64", "ubuntu", "24.04", None),
    mod.HostEvidence("cpython", (3, 11, 18), "Linux", "x86_64", "ubuntu", "22.04", None),
    mod.HostEvidence("cpython", (3, 11, 18), "Linux", "x86_64", "ubuntu", "24.04", "/tmp/shadow"),
    mod.HostEvidence("pypy", (3, 11, 18), "Linux", "x86_64", "ubuntu", "24.04", None),
])
def test_host_runtime_or_pythonpath_mismatch_fails(synthetic, host):
    with pytest.raises(mod.PreflightError, match="host differs|PYTHONPATH"):
        run_preview(synthetic, host=host)


@pytest.mark.parametrize("disk,inodes", [(0, 1000), (2 << 30, 0)])
def test_unavailable_disk_or_inodes_fails(synthetic, disk, inodes):
    with pytest.raises(mod.PreflightError, match="insufficient"):
        run_preview(synthetic, disk_bytes=disk, inodes=inodes)


def test_existing_output_or_destination_inside_checkout_fails(synthetic):
    output = synthetic[2]
    output.mkdir()
    with pytest.raises(mod.PreflightError, match="destination"):
        run_preview(synthetic)
    with pytest.raises(mod.PreflightError, match="overlap"):
        run_preview(synthetic, destination=synthetic[1] / "new-A")


def test_noncanonical_json_duplicate_key_rejected():
    with pytest.raises(mod.PreflightError, match="duplicate"):
        mod._parse_canonical(b'{"a":1,"a":1}')
    with pytest.raises(mod.PreflightError, match="noncanonical"):
        mod._parse_canonical(b' {"a":1}')


def test_cli_requires_distinct_checked_out_paths_not_workloads():
    result = subprocess.run([sys.executable, str(SCRIPT), "--help"],
                            capture_output=True, text=True, timeout=10, check=False)
    assert result.returncode == 0
    assert "--custody-checkout" in result.stdout
    assert "--generator-checkout" in result.stdout
    assert "--output-destination" in result.stdout
    assert "--freeze-a" not in result.stdout
