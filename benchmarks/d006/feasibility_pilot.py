"""D-006 bounded AB/BA feasibility runner; never the 96-cell confirmatory matrix.

Requires the exact remote PR SHA, isolated Python 3.11, and SHA-pinned
SimPy 4.1.2. Runs both scientific correctness suites before any measurement.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import random
import resource
import subprocess
import sys
import time
import unittest
from dataclasses import asdict
from pathlib import Path
from statistics import median

import simpy
from simpy_adapter_benchmark import ResourceFit, correctness, digest, make_jobs, simpy_adapter

from genesis.simulation.core import Capacity, FCFSScanningPolicy, JobSpecPrivate, simulate

VERSION = "D006_FEASIBILITY_V1"
BASE_SHA = "f39ed8a2cf10febc8affc0525c29e4a6a25b9be7"
SIMPY_WHEEL_SHA256 = "43071f84b6512c9b4fcb33ef057f240ccb1d1f3b263f9b4f9229d072e310b372"
TOTAL_S = 1800
ATTEMPT_S = 60
ADDRESS_LIMIT = 2 * 1024**3
POLICY_SEED = 93011
WARMUPS = 5
PAIRS = 20
SEEDS = (120101, 120211)
# Two small feasibility cells only. No claim about 96-cell coverage.
CELLS = (
    (100, "uniform", "light", (8, 16), "FCFSScanningPolicy"),
    (100, "heterogeneous", "saturated", (1, 1), "ResourceFit"),
)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def hash_data(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def policy_class(name: str):
    return {"FCFSScanningPolicy": FCFSScanningPolicy, "ResourceFit": ResourceFit}[name]


def git_head() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                            text=True, check=True, timeout=5)
    return result.stdout.strip()


def verify_runtime(expected: str) -> str:
    if sys.version_info[:2] != (3, 11) or simpy.__version__ != "4.1.2":
        raise RuntimeError("requires Python 3.11 and SimPy 4.1.2")
    observed = git_head()
    if observed != expected:
        raise RuntimeError(f"remote candidate SHA mismatch: {observed} != {expected}")
    if platform.system() != "Linux":
        raise RuntimeError("Linux-only RSS KiB contract")
    return observed


def machine_manifest(head: str) -> dict:
    model = "UNAVAILABLE"
    ram = None
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text().splitlines():
            if line.startswith("model name"):
                model = line.split(":", 1)[1].strip()
                break
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        for line in meminfo.read_text().splitlines():
            if line.startswith("MemTotal:"):
                ram = int(line.split()[1])
                break
    return {
        "type": "manifest", "protocol": VERSION, "head_sha": head,
        "reference_base_sha": BASE_SHA, "python": sys.version,
        "python_executable": sys.executable, "simpy": simpy.__version__,
        "simpy_wheel_sha256": SIMPY_WHEEL_SHA256,
        "platform": platform.platform(), "kernel": platform.release(),
        "cpu_model": model, "logical_cpus": os.cpu_count(), "ram_kib": ram,
        "gc_enabled": gc.isenabled(), "gc_thresholds": gc.get_threshold(),
        "rss_unit": "Linux child-process ru_maxrss KiB",
        "limit_total_s": TOTAL_S, "limit_per_invocation_s": ATTEMPT_S,
        "child_address_space_limit_bytes": ADDRESS_LIMIT,
        "workload_seeds": SEEDS, "policy_seed": POLICY_SEED,
        "warmups_per_engine_seed": WARMUPS, "pairs_per_seed": PAIRS,
        "cells": CELLS,
        "limitations": "Only 2 workload seeds per cell; technical repeats are not "
        "independent workloads; no confirmatory CI; no 96-cell extrapolation.",
    }


def child() -> None:
    # Fresh subprocess per engine invocation: RSS high-water is isolated.
    # Equal memory limits and GC mode apply to both engines.
    resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_LIMIT, ADDRESS_LIMIT))
    payload = json.loads(sys.stdin.buffer.read())
    cap = Capacity(*payload["capacity"])
    jobs = tuple(JobSpecPrivate(**row) for row in payload["jobs"])
    engine = {"custom": simulate, "simpy": simpy_adapter}[payload["engine"]]
    gc.enable()
    gc.collect()
    started_wall = time.perf_counter_ns()
    started_cpu = time.process_time_ns()
    result = engine(jobs, cap, policy_class(payload["policy"])(),
                    policy_seed=payload["policy_seed"])
    cpu_ns = time.process_time_ns() - started_cpu
    wall_ns = time.perf_counter_ns() - started_wall
    print(json.dumps({
        "wall_ns": wall_ns, "cpu_ns": cpu_ns, "events": len(result.events),
        "decisions": result.decisions, "run_status": result.run_status,
        "stop_reason": result.stop_reason,
        "result_hash": digest(result),
        "rss_peak_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }))


def one_attempt(payload: dict, deadline: float) -> dict:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return {"status": "TOTAL_BUDGET_EXCEEDED"}
    try:
        # Do not inherit GitHub/Codespace secrets or other unrelated env vars.
        env = {"PATH": os.environ.get("PATH", "/usr/bin"), "LANG": "C.UTF-8",
               "PYTHONHASHSEED": "0",
               "PYTHONPATH": os.pathsep.join(("src", "benchmarks/d006"))}
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--child"],
            input=canonical(payload), capture_output=True, check=False,
            timeout=min(ATTEMPT_S, remaining), env=env,
        )
        if proc.returncode:
            return {"status": "PROCESS_FAILED", "exit_code": proc.returncode,
                    "stderr_tail": proc.stderr.decode("utf-8", "replace")[-500:]}
        result = json.loads(proc.stdout)
        if result["result_hash"] != payload["expected_hash"]:
            result["status"] = "DIFF"
        elif result["run_status"] != "COMPLETED":
            result["status"] = "NONCOMPLETED"
        else:
            result["status"] = "PASS"
        result["exit_code"] = proc.returncode
        return result
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT"}
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "RUNNER_ERROR", "error_type": type(exc).__name__}


def enforce_correctness() -> None:
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromName("oracle_tests"))
    suite.addTests(loader.loadTestsFromName("dispatch_mutation_test"))
    if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
        raise RuntimeError("literal/tie mutation two-engine correctness FAILED")
    counts = correctness()
    if counts["golden_policy_cases"] != 16 or counts["negative_policy_cases"] != 4:
        raise RuntimeError("differential coverage mismatch")


def run_pilot(expected_sha: str, output: Path) -> dict:
    head = verify_runtime(expected_sha)
    if output.name == "pilot_results.json":
        raise ValueError("historical pilot cannot be overwritten")
    if output.resolve().parent != Path("benchmarks/d006").resolve():
        raise ValueError("raw data must remain under benchmarks/d006")
    # A strict create-exclusive output prevents erasing previous results.
    if output.exists():
        raise FileExistsError(output)
    enforce_correctness()
    deadline = time.monotonic() + TOTAL_S
    raw_count = 0
    measured = []
    with output.open("x", encoding="utf-8") as log:
        log.write(json.dumps(machine_manifest(head)) + "\n")
        for n, family, load, caps, policy_name in CELLS:
            cap = Capacity(*caps)
            for seed in SEEDS:
                jobs = make_jobs(n, family, load, cap, seed)
                job_data = [asdict(j) for j in jobs]
                workload_hash = hash_data({
                    "schema": "D006_Exogenous_v1", "jobs": job_data,
                    "capacity": caps, "seed": seed,
                })
                reference = simulate(jobs, cap, policy_class(policy_name)(),
                                     policy_seed=POLICY_SEED)
                expected_hash = digest(reference)
                common = {
                    "capacity": caps, "jobs": job_data, "policy": policy_name,
                    "policy_seed": POLICY_SEED, "expected_hash": expected_hash,
                }
                orders = ["AB"] * (PAIRS // 2) + ["BA"] * (PAIRS // 2)
                random.Random(6062026 + seed + n).shuffle(orders)
                repetitions = [(-i - 1, "AB") for i in range(WARMUPS)]
                repetitions += list(enumerate(orders))
                for rep, order in repetitions:
                    engine_order = ("custom", "simpy") if order == "AB" else (
                        "simpy", "custom"
                    )
                    for engine in engine_order:
                        attempt = one_attempt({**common, "engine": engine}, deadline)
                        row = {
                            "type": "attempt", "engine": engine, "n": n,
                            "family": family, "load": load, "capacity": caps,
                            "workload_seed": seed, "workload_hash": workload_hash,
                            "reference_hash": expected_hash, "policy": policy_name,
                            "policy_seed": POLICY_SEED, "rep": rep,
                            "warmup": rep < 0, "pair_order": order, **attempt,
                        }
                        log.write(json.dumps(row) + "\n")
                        log.flush()
                        raw_count += 1
                        if attempt["status"] != "PASS":
                            log.write(json.dumps({"type": "stopped",
                                                  "reason": attempt["status"]}) + "\n")
                            raise RuntimeError("pilot stopped: preserved all attempts")
                        if rep >= 0:
                            measured.append(row)
    return {
        "status": "FEASIBILITY_ONLY", "raw_attempts": raw_count,
        "measured_attempts": len(measured), "workload_clusters": len(CELLS) * len(SEEDS),
        "median_wall_ns": {
            engine: median(x["wall_ns"] for x in measured if x["engine"] == engine)
            for engine in ("custom", "simpy")
        }, "output": str(output),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--expected-head")
    parser.add_argument("--output", default="benchmarks/d006/feasibility_raw.jsonl")
    args = parser.parse_args()
    if args.child:
        child()
    elif not args.expected_head:
        parser.error("--expected-head must be the verified remote PR SHA")
    else:
        print(json.dumps(run_pilot(args.expected_head, Path(args.output))), flush=True)


if __name__ == "__main__":
    main()
