"""Independently calculated D006 v2 literal vectors and synthetic freeze faults.

Oracle constants were derived in a standalone Python script, without importing
the implementation under test. CI checks them on CPython 3.11.18.
No full A workload, engine, benchmarking or S1 execution is permitted here.
"""
from __future__ import annotations

import hashlib
import json
import math
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import freeze_v2
from exogenous_v2 import (
    HOLDOUT_NAMESPACE,
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

    def run_mini(self):
        return freeze_v2._freeze_plan(
            self.destination, self.entries, freeze_v2.source_provenance(),
        )

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


if __name__ == "__main__":
    unittest.main()
