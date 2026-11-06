"""Independently calculated D006 v2 literal vectors and synthetic freeze faults.

Oracle constants were derived in a standalone Python script, without importing
the implementation under test. CI checks them on CPython 3.11.18.
No full A workload, engine, benchmarking or S1 execution is permitted here.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import freeze_v2
from exogenous_v2 import (
    HOLDOUT_NAMESPACE,
    JOBS_SCHEMA,
    S1_SEED_BY_N,
    Cell,
    arrival_diagnostics,
    canonical,
    exp_gap,
    jobs_bytes,
    make_jobs_v2,
    payload_bytes,
    sha256,
    substream,
    validate_seed_partitions,
    validate_workload_seed,
)

UNIFORM = Cell("T09", 4, 1, 1, "saturated", "uniform", "FCFSScanningPolicy")
BURST = Cell("T10", 19, 8, 16, "light", "bursty", "ResourceFit")
HETERO = Cell("T11", 4, 8, 16, "light", "heterogeneous", "ResourceFit")
DESC_UNIFORM_ARRIVAL0 = (
    b'{"cell":{"cpu":1,"family":"uniform","id":"T09","load":"saturated",'
    b'"memory":1,"n":4},"domain":"arrival","index":0,'
    b'"schema":"D006_Exogenous_v2","workload_seed":17}'
)
DIGEST_UNIFORM_ARRIVAL0 = "2999a83dbd092e690ea172c1222f229296e823b7bca807c2d8c9be05b433bae6"
SEED_UNIFORM_ARRIVAL0 = (
    18816315550675822325853593400002311983185368713982748901345109327395975052006
)
# Fixed from an independently serialized tiny T09/T10 descriptor, NOT an A lock.
SYNTHETIC_EXPECTED_PLAN_SHA256 = (
    "c9e54db8dc3c41c2996c21df1cca545971fa6816d9edcd13cc11e5bbb89b7666"
)


class LiteralOracleTests(unittest.TestCase):
    def test_literal_utf8_canonical_sha_seed_and_mt19937(self):
        self.assertEqual(canonical({"z": "á", "a": 1}), b'{"a":1,"z":"\xc3\xa1"}')
        self.assertEqual(sha256(b"abc"),
                         "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
        self.assertEqual(hashlib.sha256(DESC_UNIFORM_ARRIVAL0).hexdigest(),
                         DIGEST_UNIFORM_ARRIVAL0)
        self.assertEqual(int.from_bytes(bytes.fromhex(DIGEST_UNIFORM_ARRIVAL0), "big"),
                         SEED_UNIFORM_ARRIVAL0)
        self.assertEqual(substream(UNIFORM, 17, "arrival", 0).random(),
                         0.08507624281979154)
        self.assertEqual(substream(UNIFORM, 17, "arrival", 1).random(),
                         0.7279990047350852)
        demand = substream(HETERO, 17, "demands", 0)
        self.assertEqual((demand.randint(1, 8), demand.randint(1, 16)), (3, 11))
        self.assertEqual(substream(HETERO, 17, "duration_true", 0).randint(1, 8), 1)
        self.assertEqual(substream(HETERO, 17, "duration_est", 0).randint(1, 8), 8)

    def test_literal_gaps_floor_tie_hashes_and_mutation_failures(self):
        self.assertAlmostEqual(exp_gap(UNIFORM, 17, 0, 0.6), 0.14819090444081315,
                               delta=1e-12)
        self.assertAlmostEqual(exp_gap(UNIFORM, 17, 1, 0.6), 2.1699159227177454,
                               delta=1e-12)
        jobs = make_jobs_v2(UNIFORM, 17)
        self.assertEqual(tuple(job.arrival_tick for job in jobs), (0, 2, 2, 4))
        self.assertEqual(sha256(jobs_bytes(jobs)),
                         "bdc7cf3b1fcc354e484028d55f5e2d67307535a9c676761387e9cec4e6f634df")
        self.assertEqual(sha256(payload_bytes(UNIFORM, 17, jobs)),
                         "c4c5a92b7d797bea79c7c8ede42360b2282f500bad6e8cfc7245aee6540e08e1")
        self.assertEqual(len(payload_bytes(UNIFORM, 17, jobs)), 640)
        self.assertEqual(arrival_diagnostics(UNIFORM, jobs), {
            "arrival_ties": 1, "simultaneous_arrival_ticks": 1,
            "max_simultaneous_arrivals": 2, "burst_group_count": 0,
            "last_burst_size": 0,
        })
        tampered = (replace(jobs[0], arrival_tick=1),) + jobs[1:]
        self.assertNotEqual(sha256(jobs_bytes(tampered)), sha256(jobs_bytes(jobs)))
        self.assertNotEqual(sha256(jobs_bytes(tuple(reversed(jobs)))),
                            sha256(jobs_bytes(jobs)))
        # Negative mutants: endian swap, noncompact JSON, wrong gap transform,
        # nearest-integer instead of floor (the first arrival would be zero vs one).
        self.assertNotEqual(int.from_bytes(bytes.fromhex(DIGEST_UNIFORM_ARRIVAL0), "little"),
                            SEED_UNIFORM_ARRIVAL0)
        self.assertNotEqual(
            hashlib.sha256(json.dumps({"x": 1}).encode()).hexdigest(),
            sha256(canonical({"x": 1})),
        )
        wrong_gap = -math.log(substream(UNIFORM, 17, "arrival", 0).random()) / 0.6
        self.assertNotAlmostEqual(wrong_gap, 0.14819090444081315)
        self.assertNotEqual(math.floor(2.6552158465336935), round(2.6552158465336935))
        # An independent literal byte descriptor must match exactly; this is
        # not a roundtrip oracle constructed using the implementation's canonical().
        manual = {
            "cell": {"id": "T09", "n": 4, "cpu": 1, "memory": 1,
                     "load": "saturated", "family": "uniform"},
            "domain": "arrival", "index": 0, "schema": "D006_Exogenous_v2",
            "workload_seed": 17,
        }
        self.assertEqual(canonical(manual), DESC_UNIFORM_ARRIVAL0)

    def test_literal_partial_burst_and_heterogeneous_digests(self):
        burst = make_jobs_v2(BURST, 17)
        self.assertEqual(len(burst), 19)
        self.assertEqual(tuple(job.arrival_tick for job in burst), (5,) * 16 + (44,) * 3)
        self.assertEqual((burst[0].cpu_units, burst[0].memory_units,
                          burst[0].estimated_duration_ticks,
                          burst[0].actual_duration_ticks), (1, 5, 3, 3))
        self.assertEqual((burst[-1].cpu_units, burst[-1].memory_units,
                          burst[-1].estimated_duration_ticks,
                          burst[-1].actual_duration_ticks), (7, 4, 5, 4))
        self.assertEqual(arrival_diagnostics(BURST, burst), {
            "arrival_ties": 17, "simultaneous_arrival_ticks": 2,
            "max_simultaneous_arrivals": 16, "burst_group_count": 2,
            "last_burst_size": 3,
        })
        self.assertEqual(sha256(jobs_bytes(burst)),
                         "af9cbc8756de483117f4e33bebe46c3780eb3b6e808be06c4ea716a00d42257a")
        self.assertEqual(sha256(payload_bytes(BURST, 17, burst)),
                         "6602abdaa624159bdd067730e77c6a40c521080351202b0a2b912d5b18bbf59f")
        hetero = make_jobs_v2(HETERO, 17)
        self.assertEqual(tuple(job.arrival_tick for job in hetero), (7, 17, 21, 25))
        self.assertEqual((hetero[0].cpu_units, hetero[0].memory_units,
                          hetero[0].estimated_duration_ticks,
                          hetero[0].actual_duration_ticks), (3, 11, 8, 1))
        self.assertEqual(sha256(jobs_bytes(hetero)),
                         "13c0e5416b7b4f96c3cc02ffafab6c315bfc4d03c60bd5fc0c1fc20c42aee797")
        self.assertEqual(sha256(payload_bytes(HETERO, 17, hetero)),
                         "1697201e244d6198d6d2fe362622af671f0cf3dc6aaf531c2f39266478827d24")

    def test_holdout_and_cross_partition_collision_guard(self):
        validate_seed_partitions()
        for seed in (*HOLDOUT_NAMESPACE, 915001):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                validate_workload_seed(seed)
            with self.assertRaises(ValueError):
                make_jobs_v2(UNIFORM, seed)
            with self.assertRaises(ValueError):
                substream(UNIFORM, seed, "arrival", 0)
        with (
            patch.dict(S1_SEED_BY_N, {1000: 710111}),
            self.assertRaisesRegex(ValueError, "collision"),
        ):
            validate_seed_partitions()


class SyntheticFreezeTests(unittest.TestCase):
    """Only N=4/N=19 synthetic T-cells, never any A input or S1 workflow."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.destination = self.parent / "frozen"
        self.entries = ((UNIFORM, 17, 21), (BURST, 23, 27))

    def run_mini(self, entries=None):
        return freeze_v2._freeze_plan(
            self.destination, self.entries if entries is None else entries,
            freeze_v2.source_provenance(),
        )

    def _rewrite_manifest(self, manifest):
        path = self.destination / "manifest.json"
        raw = canonical(manifest)
        path.write_bytes(raw)
        (self.destination / "manifest.sha256").write_text(sha256(raw) + "\n")

    def strict_mini(self):
        return freeze_v2.verify_expected_plan(
            self.destination, self.entries, SYNTHETIC_EXPECTED_PLAN_SHA256,
        )

    def test_strict_synthetic_positive_and_a_topology_without_a_generation(self):
        self.assertEqual(
            freeze_v2.expected_plan_sha256(self.entries), SYNTHETIC_EXPECTED_PLAN_SHA256,
        )
        plan_slots = freeze_v2._plan_slots(freeze_v2._a_entries())
        self.assertEqual(len(plan_slots), 16)
        self.assertEqual(len({row["cell"]["id"] for row in plan_slots}), 8)
        self.run_mini()
        self.assertEqual(len(self.strict_mini()["records"]), 2)
        # A gate requires the full A plan even if a synthetic lock exists.
        with self.assertRaisesRegex(RuntimeError, "expected plan records mismatch"):
            freeze_v2.verify_a(
                self.destination, freeze_v2.expected_plan_sha256(freeze_v2._a_entries()),
            )

    def test_subset_rebuilt_checksums_pass_generic_but_fail_strict(self):
        self.run_mini()
        manifest = json.loads((self.destination / "manifest.json").read_bytes())
        missing = manifest["records"].pop()
        (self.destination / missing["file"]).unlink()
        self._rewrite_manifest(manifest)
        # R27-09 first cause: the surviving record and checksum are fully valid.
        self.assertEqual(len(freeze_v2.verify_freeze(self.destination)["records"]), 1)
        with self.assertRaisesRegex(RuntimeError, "wrong slot count"):
            self.strict_mini()

    def test_extra_duplicate_and_wrong_workload_seed_rejected(self):
        for entries in (
            self.entries + ((HETERO, 31, 33),),
            ((UNIFORM, 19, 21), self.entries[1]),
        ):
            with self.subTest(entries=entries):
                self.run_mini(entries)
                self.assertEqual(len(freeze_v2.verify_freeze(self.destination)["records"]),
                                 len(entries))
                with self.assertRaisesRegex(RuntimeError, "expected plan records mismatch"):
                    self.strict_mini()
                shutil.rmtree(self.destination)

        self.run_mini()
        manifest = json.loads((self.destination / "manifest.json").read_bytes())
        extra = manifest["records"].pop()
        (self.destination / extra["file"]).unlink()
        manifest["records"].append(dict(manifest["records"][0]))
        self._rewrite_manifest(manifest)
        # A generic integrity verifier must reject duplicate filenames too.
        with self.assertRaisesRegex(RuntimeError, "duplicate record filename"):
            freeze_v2.verify_freeze(self.destination)
        with self.assertRaisesRegex(RuntimeError, "cells/seeds/files/order"):
            self.strict_mini()

    def test_order_policy_cell_filename_and_stable_order_tampering(self):
        self.run_mini()
        baseline = json.loads((self.destination / "manifest.json").read_bytes())
        for field, value in (
            ("order_seed", 99), ("policy_seed", 99),
            ("cell_policy", "ResourceFit"), ("reverse_order", None),
            ("filename", "renamed.json"),
        ):
            with self.subTest(field=field):
                manifest = json.loads(canonical(baseline))
                if field == "cell_policy":
                    manifest["records"][0]["cell"]["policy"] = value
                elif field == "reverse_order":
                    manifest["records"].reverse()
                elif field == "filename":
                    (self.destination / "T09_17.json").rename(
                        self.destination / "renamed.json",
                    )
                    manifest["records"][0]["file"] = value
                else:
                    manifest["records"][0][field] = value
                self._rewrite_manifest(manifest)
                if field in ("policy_seed", "filename"):
                    # New generic versioned schema also rejects impossible producer fields.
                    with self.assertRaises(RuntimeError):
                        freeze_v2.verify_freeze(self.destination)
                else:
                    self.assertEqual(len(freeze_v2.verify_freeze(self.destination)["records"]), 2)
                with self.assertRaisesRegex(RuntimeError, "cells/seeds/files/order"):
                    self.strict_mini()
                if field == "filename":
                    (self.destination / "renamed.json").rename(
                        self.destination / "T09_17.json",
                    )


    def test_received_plan_exact_json_type_and_schema_regressions(self):
        """F1: self-consistent checksums cannot launder int/float or bool aliases."""
        self.run_mini()
        baseline = json.loads((self.destination / "manifest.json").read_bytes())
        from copy import deepcopy

        mutations = (
            (("records", 0, "order_seed"), 21.0),
            (("records", 0, "policy_seed"), 93011.0),
            (("records", 0, "workload_seed"), 17.0),
            (("records", 0, "order_seed"), True),
            (("records", 0, "workload_seed"), True),
            (("records", 0, "policy_seed"), True),
            (("records", 0, "cell", "n"), 4.0),
            (("records", 0, "cell", "cpu"), 1.0),
            (("records", 0, "cell", "memory"), True),
            (("records", 0, "cell", "load"), False),
            (("records", 0, "file"), True),
        )
        for path, value in mutations:
            with self.subTest(path=path, value=value):
                manifest = deepcopy(baseline)
                obj = manifest
                for part in path[:-1]:
                    obj = obj[part]
                obj[path[-1]] = value
                self._rewrite_manifest(manifest)
                # Exact expected plan hash remains external, not recomputed on mutation.
                with self.assertRaisesRegex(RuntimeError, "expected plan records mismatch"):
                    self.strict_mini()
                with self.assertRaises(RuntimeError):
                    freeze_v2.verify_freeze(self.destination)

        for target, field in (
            ("record", "order_seed"), ("record", "unexpected"),
            ("cell", "policy"), ("cell", "unexpected"),
        ):
            for delete in (True, False):
                if field == "unexpected" and delete:
                    continue
                with self.subTest(target=target, field=field, delete=delete):
                    manifest = deepcopy(baseline)
                    obj = manifest["records"][0]
                    if target == "cell":
                        obj = obj["cell"]
                    if delete:
                        del obj[field]
                    else:
                        obj[field] = 42
                    self._rewrite_manifest(manifest)
                    with self.assertRaisesRegex(RuntimeError, "expected plan records mismatch"):
                        self.strict_mini()
                    with self.assertRaises(RuntimeError):
                        freeze_v2.verify_freeze(self.destination)

        # Duplicate JSON keys: even if the checksum is recomputed, parsing fails closed.
        raw = canonical(baseline)
        duplicate = raw.replace(b'"policy_seed":93011',
                                b'"policy_seed":93011,"policy_seed":93011', 1)
        self.assertNotEqual(raw, duplicate)
        (self.destination / "manifest.json").write_bytes(duplicate)
        (self.destination / "manifest.sha256").write_text(sha256(duplicate) + "\n")
        with self.assertRaisesRegex(RuntimeError, "duplicate JSON key"):
            freeze_v2.verify_freeze(self.destination)
        with self.assertRaisesRegex(RuntimeError, "duplicate JSON key"):
            self.strict_mini()

    def test_manifest_metadata_tampering_with_valid_payloads_is_rejected(self):
        """F2: recomputed manifest.sha256 cannot authenticate false scientific metadata."""
        from copy import deepcopy

        self.run_mini()
        baseline = json.loads((self.destination / "manifest.json").read_bytes())
        payloads = {
            record["file"]: (self.destination / record["file"]).read_bytes()
            for record in baseline["records"]
        }
        mutations = (
            (("records", 0, "expected_rho"), -1.0),
            (("records", 0, "expected_rho"), True),
            (("records", 0, "lambda"), -1.0),
            (("records", 0, "lambda"), "negative"),
            (("records", 0, "oversize_count"), 999),
            (("records", 0, "oversize_count"), 0.0),
            (("records", 0, "arrivals", "arrival_ties"), False),
            (("records", 0, "realized", "cpu_work_ticks"), 999),
            (("records", 0, "realized", "rho_cpu_realized"), 0),
            (("serialization", "seed_endianness"), "little"),
            (("serialization", "sort_keys"), 1),
            (("serialization", "separators"), [":", ","]),
            (("serialization", "extra"), "unrecognized"),
            (("holdout_reserved",), [910000, 920000]),
            (("holdout_reserved",), [910000.0, 919999]),
            (("holdout_confidential",), True),
            (("holdout_confidential",), 0),
            (("schema",), "D006_Exogenous_v2_FreezeManifest_1"),
            (("status",), "COMPLETE"),
            (("runtime", "python_version"), [3, 11, 18.0]),
            (("source_provenance", "files",
              freeze_v2.DETERMINANT_PATHS[0], "bytes"), 10.0),
            (("unexpected_top_level",), 42),
            (("records", 0, "unexpected_record"), 42),
        )
        for path, value in mutations:
            with self.subTest(path=path, value=value):
                manifest = deepcopy(baseline)
                obj = manifest
                for part in path[:-1]:
                    obj = obj[part]
                obj[path[-1]] = value
                self._rewrite_manifest(manifest)
                raw = (self.destination / "manifest.json").read_bytes()
                self.assertEqual(
                    (self.destination / "manifest.sha256").read_text(),
                    sha256(raw) + "\n",
                )
                for name, original in payloads.items():
                    self.assertEqual((self.destination / name).read_bytes(), original)
                with self.assertRaises(RuntimeError):
                    freeze_v2.verify_freeze(self.destination)
                with self.assertRaises(RuntimeError):
                    self.strict_mini()

        for path in (
            ("serialization", "gap"),
            ("records", 0, "expected_rho"),
            ("records", 0, "arrivals", "arrival_ties"),
            ("source_provenance", "git_tree"),
            ("holdout_reserved",),
        ):
            with self.subTest(missing=path):
                manifest = deepcopy(baseline)
                obj = manifest
                for part in path[:-1]:
                    obj = obj[part]
                del obj[path[-1]]
                self._rewrite_manifest(manifest)
                with self.assertRaises(RuntimeError):
                    freeze_v2.verify_freeze(self.destination)

    def test_external_plan_identity_missing_or_wrong_is_fail_closed(self):
        self.run_mini()
        for digest in (None, "", "0" * 64, "not-a-hash"):
            with (
                self.subTest(digest=digest),
                self.assertRaisesRegex(RuntimeError, "external expected-plan SHA256"),
            ):
                freeze_v2.verify_expected_plan(self.destination, self.entries, digest)
        with self.assertRaisesRegex(RuntimeError, "external expected-plan SHA256 required"):
            freeze_v2.verify_a(self.destination)
        with self.assertRaisesRegex(RuntimeError, "external expected-plan SHA256 required"):
            freeze_v2.freeze_a(self.parent / "not-created")
        self.assertFalse((self.parent / "not-created").exists())

    def test_pythonpath_shadowed_generator_provenance_rejected(self):
        root = Path(freeze_v2.__file__).resolve().parents[2]
        shadow = self.parent / "shadow"
        shadow.mkdir()
        # Identical bytes would have passed old tracked-file attestation.
        generator = root / "benchmarks/d006/exogenous_v2.py"
        (shadow / "exogenous_v2.py").write_bytes(generator.read_bytes())
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join((
            str(shadow), str(generator.parent), str(root / "src"),
        ))
        result = subprocess.run(
            [sys.executable, "-c", "import freeze_v2; freeze_v2.source_provenance()"],
            cwd=root, env=env, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("imported generator does not originate from tracked source",
                      result.stderr)

    def test_transactional_readback_and_provenance(self):
        manifest_path = self.run_mini()
        self.assertTrue(manifest_path.is_file())
        manifest = freeze_v2.verify_freeze(self.destination)
        self.assertEqual(manifest["schema"], freeze_v2.MANIFEST_SCHEMA)
        self.assertEqual(manifest["status"], freeze_v2.INTEGRITY_STATUS)
        self.assertFalse(manifest["holdout_confidential"])
        self.assertEqual(len(manifest["records"]), 2)
        self.assertEqual(manifest["records"][0]["arrivals"]["arrival_ties"], 1)
        self.assertEqual(manifest["records"][1]["arrivals"]["last_burst_size"], 3)
        self.assertEqual(len(manifest["source_provenance"]["git_commit"]), 40)
        self.assertEqual(len(manifest["source_provenance"]["git_tree"]), 40)
        self.assertEqual(len(manifest["source_provenance"]["imported_generator_sha256"]), 64)
        self.assertEqual(
            set(manifest["source_provenance"]["files"]), set(freeze_v2.DETERMINANT_PATHS),
        )
        self.assertEqual(len(list(self.parent.glob(".*.staging-*"))), 0)

    def test_existing_destination_and_atomic_rename_collision(self):
        self.destination.mkdir()
        (self.destination / "unrelated").write_text("keep")
        with self.assertRaises(FileExistsError):
            self.run_mini()
        self.assertEqual((self.destination / "unrelated").read_text(), "keep")
        self.assertFalse(list(self.parent.glob(".*.staging-*")))
        self.destination.rename(self.parent / "existing")
        original = freeze_v2._atomic_publish_dir

        def racing_publish(stage, destination):
            destination.mkdir()
            original(stage, destination)

        with (
            patch.object(freeze_v2, "_atomic_publish_dir", side_effect=racing_publish),
            self.assertRaises(FileExistsError),
        ):
            self.run_mini()
        self.assertTrue(self.destination.is_dir())
        self.assertEqual(list(self.destination.iterdir()), [])
        self.assertFalse(list(self.parent.glob(".*.staging-*")))

    def test_fault_injection_after_first_payload_manifest_and_checksum(self):
        original = freeze_v2._write_bytes
        for target in ("T10_23.json", "manifest.json", "manifest.sha256"):
            with self.subTest(target=target):
                def failing_write(path, data, target=target):
                    if path.name == target:
                        raise OSError("simulated IO fault")
                    return original(path, data)
                with (
                    patch.object(freeze_v2, "_write_bytes", side_effect=failing_write),
                    self.assertRaisesRegex(OSError, "simulated IO fault"),
                ):
                    self.run_mini()
                self.assertFalse(self.destination.exists())
                self.assertFalse(list(self.parent.glob(".*.staging-*")))

    def test_tampered_payload_and_manifest_checksum_are_rejected(self):
        self.run_mini()
        path = self.destination / "T09_17.json"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(RuntimeError, "payload checksum mismatch"):
            freeze_v2.verify_freeze(self.destination)
        path.write_bytes(path.read_bytes()[:-1])
        digest = self.destination / "manifest.sha256"
        digest.write_text("0" * 64 + "\n")
        with self.assertRaisesRegex(RuntimeError, "manifest checksum mismatch"):
            freeze_v2.verify_freeze(self.destination)

    def test_corrupted_staging_readback_never_publishes(self):
        original = freeze_v2._write_bytes

        def corrupt_after_write(path, data):
            original(path, data)
            if path.name == "T09_17.json":
                path.write_bytes(data + b"corrupt")
        with (
            patch.object(freeze_v2, "_write_bytes", side_effect=corrupt_after_write),
            self.assertRaisesRegex(RuntimeError, "payload checksum mismatch"),
        ):
            self.run_mini()
        self.assertFalse(self.destination.exists())
        self.assertFalse(list(self.parent.glob(".*.staging-*")))

    def test_runtime_version_implementation_and_manifest_provenance_negative(self):
        with (
            patch.object(freeze_v2.sys, "implementation", SimpleNamespace(name="pypy")),
            self.assertRaisesRegex(RuntimeError, "CPython"),
        ):
            freeze_v2.freeze_a(self.destination)
        with (
            patch.object(freeze_v2, "PYTHON_FREEZE_VERSION", (3, 11, 17)),
            self.assertRaisesRegex(RuntimeError, "3.11.18"),
        ):
            freeze_v2.freeze_a(self.destination)
        self.assertFalse(self.destination.exists())
        self.run_mini()
        target = self.destination / "manifest.json"
        manifest = json.loads(target.read_bytes())
        manifest["source_provenance"]["git_tree"] = "0" * 40
        target.write_bytes(canonical(manifest))
        (self.destination / "manifest.sha256").write_text(sha256(target.read_bytes()) + "\n")
        with self.assertRaisesRegex(RuntimeError, "Git tree/files differ"):
            freeze_v2.verify_freeze(self.destination)

    def test_consistent_checksum_rewrite_still_fails_literal_replay(self):
        self.run_mini()
        payload_path = self.destination / "T09_17.json"
        payload = json.loads(payload_path.read_bytes())
        payload["jobs"][0]["arrival_tick"] = 1
        raw = canonical(payload)
        payload_path.write_bytes(raw)
        manifest_path = self.destination / "manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        record = manifest["records"][0]
        record["payload_sha256"] = sha256(raw)
        record["jobs_sha256"] = sha256(
            canonical({"schema": JOBS_SCHEMA, "jobs": payload["jobs"]}),
        )
        # This mutation leaves tie counts and realized workload unchanged:
        # both payload and manifest hashes are internally self-consistent.
        manifest_raw = canonical(manifest)
        manifest_path.write_bytes(manifest_raw)
        (self.destination / "manifest.sha256").write_text(
            sha256(manifest_raw) + "\n",
        )
        with self.assertRaisesRegex(RuntimeError, "workload replay bytes mismatch"):
            freeze_v2.verify_freeze(self.destination)

    def test_imported_core_mismatch_is_rejected(self):
        class FakeJob:
            pass

        with (
            patch.object(freeze_v2, "JobSpecPrivate", FakeJob),
            self.assertRaisesRegex(RuntimeError, "imported Core bytes differ"),
        ):
            freeze_v2.source_provenance()




if __name__ == "__main__":
    unittest.main()
