"""Prospective D-006 exogenous workload generator v2 (no simulation or timings).

This is a distinct population from historical make_jobs/v1. Do not use v2
measurements to revise the original preregistration or pool with v1 pilots.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from random import Random

from genesis.simulation.core import JobSpecPrivate

SCHEMA = "D006_Exogenous_v2"
JOBS_SCHEMA = "D006_Jobs_v2"
PYTHON_FREEZE_VERSION = (3, 11, 18)
RHO = {"light": 0.4, "saturated": 1.2}
FAMILIES = {"uniform", "heterogeneous", "bursty"}
POLICIES = {"FCFSScanningPolicy", "ResourceFit"}


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True, slots=True)
class Cell:
    id: str
    n: int
    cpu: int
    memory: int
    load: str
    family: str
    policy: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Z][0-9]{2}", self.id):
            raise ValueError("cell id must be a letter followed by two digits")
        if type(self.n) is not int or not 1 <= self.n <= 100000:
            raise ValueError("n must be an integer in 1..100000")
        if any(type(x) is not int or x < 1 for x in (self.cpu, self.memory)):
            raise ValueError("capacity must be positive integers")
        if self.load not in RHO or self.family not in FAMILIES:
            raise ValueError("unknown load/family")
        if self.policy not in POLICIES:
            raise ValueError("unknown policy")


# S0 v2 (#6668170998), chosen after v1 pilot. Screening only: 8/96 cells.
A_CELLS = (
    Cell("A01", 100, 1, 1, "light", "uniform", "FCFSScanningPolicy"),
    Cell("A02", 100, 8, 16, "saturated", "bursty", "ResourceFit"),
    Cell("A03", 1000, 1, 1, "light", "heterogeneous", "ResourceFit"),
    Cell("A04", 1000, 8, 16, "saturated", "uniform", "FCFSScanningPolicy"),
    Cell("A05", 10000, 1, 1, "saturated", "uniform", "ResourceFit"),
    Cell("A06", 10000, 8, 16, "light", "heterogeneous", "FCFSScanningPolicy"),
    Cell("A07", 100000, 1, 1, "light", "bursty", "FCFSScanningPolicy"),
    Cell("A08", 100000, 8, 16, "saturated", "heterogeneous", "ResourceFit"),
)

S1_CELLS = (
    Cell("S01", 1000, 1, 1, "light", "heterogeneous", "FCFSScanningPolicy"),
    Cell("S02", 1000, 8, 16, "saturated", "bursty", "ResourceFit"),
    Cell("S03", 10000, 1, 1, "light", "uniform", "FCFSScanningPolicy"),
    Cell("S04", 10000, 8, 16, "saturated", "heterogeneous", "ResourceFit"),
    Cell("S05", 100000, 1, 1, "light", "bursty", "FCFSScanningPolicy"),
    Cell("S06", 100000, 8, 16, "saturated", "heterogeneous", "ResourceFit"),
)
S1_SEED_BY_N = {1000: 810011, 10000: 811011, 100000: 812011}
POLICY_SEED = 93011
HOLDOUT_NAMESPACE = (910000, 919999)  # PUBLIC reservation, not blinded holdout.
PILOT_SEEDS = (120101, 120211)



def a_seeds(index: int) -> tuple[int, int]:
    if type(index) is not int or not 1 <= index <= 8:
        raise ValueError("A cell index must be 1..8")
    return (710000 + index * 100 + 11, 710000 + index * 100 + 29)


def a_order_seeds(index: int) -> tuple[int, int]:
    if type(index) is not int or not 1 <= index <= 8:
        raise ValueError("A cell index must be 1..8")
    return (820000 + index * 100 + 11, 820000 + index * 100 + 29)


def plan_a() -> tuple[tuple[Cell, int, int], ...]:
    return tuple(
        (cell, seed, order)
        for index, cell in enumerate(A_CELLS, 1)
        for seed, order in zip(a_seeds(index), a_order_seeds(index), strict=True)
    )


def validate_workload_seed(seed: int) -> None:
    """Fail closed: reserved public seeds are not usable in development."""
    if type(seed) is not int or seed < 0:
        raise ValueError("workload seed must be a nonnegative integer")
    if HOLDOUT_NAMESPACE[0] <= seed <= HOLDOUT_NAMESPACE[1]:
        raise ValueError("reserved holdout seed is forbidden")


def validate_seed_partitions() -> None:
    seeds = (
        [seed for i in range(1, 9) for seed in a_seeds(i)]
        + [seed for i in range(1, 9) for seed in a_order_seeds(i)]
        + list(S1_SEED_BY_N.values()) + [POLICY_SEED] + list(PILOT_SEEDS)
    )
    if len(set(seeds)) != len(seeds):
        raise ValueError("cross-partition seed collision")
    for seed in seeds:
        validate_workload_seed(seed)


def arrival_diagnostics(cell: Cell, jobs: tuple[JobSpecPrivate, ...]) -> dict[str, int]:
    counts = Counter(job.arrival_tick for job in jobs)
    groups = (len(jobs) + 15) // 16 if cell.family == "bursty" else 0
    return {
        "arrival_ties": len(jobs) - len(counts),
        "simultaneous_arrival_ticks": sum(count > 1 for count in counts.values()),
        "max_simultaneous_arrivals": max(counts.values(), default=0),
        "burst_group_count": groups,
        "last_burst_size": len(jobs) - 16 * (groups - 1) if groups else 0,
    }


def offered_work_per_job(cell: Cell) -> float:
    if cell.family == "uniform":
        return max(2 / cell.cpu, 2 / cell.memory)
    expected_duration = 4.5 if cell.family == "heterogeneous" else 3.0
    return max(
        expected_duration * (cell.cpu + 1) / (2 * cell.cpu),
        expected_duration * (cell.memory + 1) / (2 * cell.memory),
    )


def arrival_rate(cell: Cell) -> float:
    return RHO[cell.load] / offered_work_per_job(cell)


def exogenous_cell(cell: Cell) -> dict[str, object]:
    # Experiment policy is deliberately excluded from workload-generation RNG.
    return {key: getattr(cell, key) for key in
            ("id", "n", "cpu", "memory", "load", "family")}


def substream(cell: Cell, workload_seed: int, domain: str, index: int) -> Random:
    validate_workload_seed(workload_seed)
    if type(index) is not int or index < 0:
        raise ValueError("substream index must be nonnegative")
    if domain not in {"arrival", "demands", "duration_true", "duration_est"}:
        raise ValueError("unrecognized PRNG domain")
    descriptor = {
        "schema": SCHEMA, "cell": exogenous_cell(cell),
        "workload_seed": workload_seed, "domain": domain, "index": index,
    }
    return Random(int.from_bytes(hashlib.sha256(canonical(descriptor)).digest(), "big"))


def exp_gap(cell: Cell, seed: int, index: int, rate: float) -> float:
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError("exponential rate must be positive and finite")
    # One 53-bit MT19937 uniform per job or burst, deterministic in pinned Python.
    u = substream(cell, seed, "arrival", index).random()
    return -math.log1p(-u) / rate


def make_jobs_v2(cell: Cell, workload_seed: int) -> tuple[JobSpecPrivate, ...]:
    validate_workload_seed(workload_seed)
    rate = arrival_rate(cell)
    elapsed = 0.0
    last_arrival = 0
    jobs = []
    for i in range(cell.n):
        if cell.family == "bursty":
            if i % 16 == 0:
                elapsed += exp_gap(cell, workload_seed, i // 16, rate / 16)
                last_arrival = math.floor(elapsed)
        else:
            elapsed += exp_gap(cell, workload_seed, i, rate)
            last_arrival = math.floor(elapsed)

        if cell.family == "uniform":
            cpu = memory = 1
            actual = estimate = 2
        else:
            demands = substream(cell, workload_seed, "demands", i)
            cpu = demands.randint(1, cell.cpu)
            memory = demands.randint(1, cell.memory)
            max_duration = 8 if cell.family == "heterogeneous" else 5
            actual = substream(cell, workload_seed, "duration_true", i).randint(
                1, max_duration
            )
            estimate = substream(cell, workload_seed, "duration_est", i).randint(
                1, max_duration
            )
        jobs.append(
            JobSpecPrivate(f"J{i:06d}", last_arrival, cpu, memory, estimate, actual)
        )
    return tuple(jobs)


def jobs_bytes(jobs: tuple[JobSpecPrivate, ...]) -> bytes:
    # Intentionally excludes seed/cell envelope: tests verify actual-job diversity.
    return canonical({"schema": JOBS_SCHEMA, "jobs": [asdict(j) for j in jobs]})


def payload_bytes(cell: Cell, seed: int, jobs: tuple[JobSpecPrivate, ...]) -> bytes:
    return canonical({
        "schema": SCHEMA, "cell": exogenous_cell(cell), "workload_seed": seed,
        "cutoff_tick": None, "jobs": [asdict(j) for j in jobs],
    })


def realized_load(cell: Cell, jobs: tuple[JobSpecPrivate, ...]) -> dict[str, float | int]:
    # Finite-input diagnostic, not stationary queue utilization or observed busy time.
    if not jobs:
        raise ValueError("realized load needs nonempty jobs")
    window = max(1, jobs[-1].arrival_tick + 1)
    cpu_work = sum(j.cpu_units * j.actual_duration_ticks for j in jobs)
    mem_work = sum(j.memory_units * j.actual_duration_ticks for j in jobs)
    return {
        "arrival_window_ticks": window, "cpu_work_ticks": cpu_work,
        "memory_work_ticks": mem_work,
        "rho_cpu_realized": cpu_work / (cell.cpu * window),
        "rho_memory_realized": mem_work / (cell.memory * window),
        "rho_max_realized": max(cpu_work / (cell.cpu * window),
                                mem_work / (cell.memory * window)),
    }


def freeze_a(directory: Path) -> Path:
    """Freeze proposed A inputs only if separately authorized (never in CI)."""
    from freeze_v2 import freeze_a as transactional_freeze_a

    return transactional_freeze_a(directory)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--plan", action="store_true")
    actions.add_argument("--freeze-a", type=Path)
    actions.add_argument("--verify-freeze", type=Path)
    args = parser.parse_args()
    if args.plan:
        print(json.dumps([
            {"cell": asdict(cell), "seed": seed, "order_seed": order}
            for cell, seed, order in plan_a()
        ], indent=2))
    elif args.verify_freeze is not None:
        from freeze_v2 import verify_freeze

        print(verify_freeze(args.verify_freeze)["status"])
    else:
        print(freeze_a(args.freeze_a))


if __name__ == "__main__":
    main()
