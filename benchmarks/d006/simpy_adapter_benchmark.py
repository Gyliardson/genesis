"""D-006 isolated SimPy 4.1.2 adapter; exact ActionA_v0 reference semantics.

Prerequisite: SimPy installed only in the external isolated venv.
No production or existing core code is modified.
"""
from __future__ import annotations

import hashlib
import json
import platform
import resource
import sys
from dataclasses import asdict
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter_ns, process_time_ns

import simpy

from genesis.simulation.core import (
    Capacity,
    Event,
    FCFSScanningPolicy,
    JobOutcome,
    JobSpecPrivate,
    ObservationV0,
    PublicPolicyConfig,
    ReadyJobPublic,
    SimulationResult,
    StartA_v0,
    simulate,
)


def simpy_adapter(
    jobs: tuple[JobSpecPrivate, ...], capacity: Capacity, policy,
    *, policy_seed: int = 0, evaluation_cutoff_tick: int | None = None
) -> SimulationResult:
    """Use SimPy's event calendar; explicitly buffer and reorder same-tick phases."""
    if type(policy_seed) is not int or policy_seed < 0:
        raise ValueError("policy_seed must be an integer >= 0")
    if evaluation_cutoff_tick is not None and (
        type(evaluation_cutoff_tick) is not int or evaluation_cutoff_tick < 0
    ):
        raise ValueError("evaluation_cutoff_tick must be an integer >= 0")
    if type(capacity) is not Capacity:
        raise TypeError("capacity must be Capacity")
    if not isinstance(jobs, tuple) or any(type(j) is not JobSpecPrivate for j in jobs):
        raise TypeError("jobs must be a tuple of JobSpecPrivate")
    ordered = tuple(sorted(jobs, key=lambda j: (j.arrival_tick, j.id)))
    if len({j.id for j in ordered}) != len(ordered):
        raise ValueError("job IDs must be unique")
    if evaluation_cutoff_tick is not None and any(
        j.arrival_tick >= evaluation_cutoff_tick for j in ordered
    ):
        raise ValueError("fixed-H input cohort must arrive before evaluation cutoff")

    env = simpy.Environment()
    by_id = {j.id: j for j in ordered}
    states = {j.id: "FUTURE" for j in ordered}
    start: dict[str, int] = {}
    completed: dict[str, int] = {}
    arrived: list[str] = []
    finished: list[str] = []
    events: list[Event] = []
    cpu = memory = decisions = now = 0
    event_limit = 8 * len(ordered) + 16

    def record(kind: str, job_id: str | None = None) -> None:
        if len(events) >= event_limit:
            raise RuntimeError("event bound exceeded")
        events.append(Event(len(events), now, kind, job_id, cpu, memory))

    def invariants() -> None:
        running = [by_id[j] for j, state in states.items() if state == "RUNNING"]
        if cpu != sum(j.cpu_units for j in running) or memory != sum(j.memory_units for j in running):
            raise RuntimeError("resource conservation violated")
        if not (0 <= cpu <= capacity.cpu_units and 0 <= memory <= capacity.memory_units):
            raise RuntimeError("resource capacity violated")

    def result(status: str, reason: str) -> SimulationResult:
        invariants()
        record("TERMINATE")
        return SimulationResult(
            status, reason, now, tuple(events),
            tuple(JobOutcome(j.id, states[j.id], start.get(j.id), completed.get(j.id)) for j in ordered),
            decisions, cpu, memory,
        )

    def schedule(delay: int, buffer: list[str], name: str) -> None:
        trigger = env.timeout(delay)
        trigger.callbacks.append(lambda _event: buffer.append(name))

    for j in ordered:
        schedule(j.arrival_tick, arrived, j.id)

    config = PublicPolicyConfig("ActionA_v0", "ObservationV0", "ActionA_v0",
                                capacity.cpu_units, capacity.memory_units)
    try:
        policy.reset(policy_seed, config)
    except Exception:  # noqa: BLE001
        return result("ERROR", "DECIDE_EXCEPTION")

    while True:
        # Buffer every event due at current timestamp; never use SimPy's tie order.
        while env.peek() == now:
            env.step()
        for job_id in sorted(finished):
            if states[job_id] != "RUNNING":
                return result("ERROR", "SIMULATION_ERROR")
            j = by_id[job_id]
            states[job_id] = "COMPLETED"
            completed[job_id] = now
            cpu -= j.cpu_units
            memory -= j.memory_units
            invariants()
            record("COMPLETE", job_id)
        finished.clear()
        for job_id in sorted(arrived):
            j = by_id[job_id]
            if j.cpu_units > capacity.cpu_units or j.memory_units > capacity.memory_units:
                states[job_id] = "REJECTED_INFEASIBLE"
                record("REJECT_INFEASIBLE", job_id)
            else:
                states[job_id] = "READY"
                record("ARRIVE", job_id)
        arrived.clear()

        pending = any(st in ("FUTURE", "READY", "RUNNING") for st in states.values())
        if evaluation_cutoff_tick is not None and now == evaluation_cutoff_tick:
            return result("CENSORED_FIXED_H" if pending else "COMPLETED",
                          "EVALUATION_CUTOFF" if pending else "ALL_COMPLETED")

        ready = tuple(j for j in ordered if states[j.id] == "READY")
        eligible = tuple(j.id for j in ready if
                         j.cpu_units <= capacity.cpu_units - cpu and
                         j.memory_units <= capacity.memory_units - memory)
        if eligible:
            obs = ObservationV0(
                "ObservationV0", now, capacity.cpu_units, capacity.cpu_units - cpu,
                capacity.memory_units, capacity.memory_units - memory,
                tuple(ReadyJobPublic(j.id, j.arrival_tick, j.cpu_units, j.memory_units,
                                     j.estimated_duration_ticks, now-j.arrival_tick) for j in ready),
                eligible,
            )
            decisions += 1
            try:
                action = policy.decide(obs)
            except Exception:  # noqa: BLE001
                return result("ERROR", "DECIDE_EXCEPTION")
            if action is None:
                return result("ERROR", "NO_RETURN")
            if type(action) is not StartA_v0 or type(action.job_id) is not str or action.job_id not in eligible:
                return result("ERROR", "INVALID_ACTION")
            j = by_id[action.job_id]
            if (states[j.id] != "READY" or
                j.cpu_units > capacity.cpu_units-cpu or
                j.memory_units > capacity.memory_units-memory):
                return result("ERROR", "INVALID_ACTION")
            cpu += j.cpu_units
            memory += j.memory_units
            states[j.id] = "RUNNING"
            start[j.id] = now
            schedule(j.actual_duration_ticks, finished, j.id)
            invariants()
            record("START", j.id)
            continue

        future = env.peek()
        if future == float("inf"):
            if ready:
                return result("POLICY_STALL", "NO_EXOGENOUS_PROGRESS")
            return result("COMPLETED", "ALL_COMPLETED")
        next_tick = int(future)
        if evaluation_cutoff_tick is not None:
            next_tick = min(next_tick, evaluation_cutoff_tick)
        if next_tick <= now:
            return result("ERROR", "SIMULATION_ERROR")
        record("FORCED_ADVANCE")
        now = next_tick

class ResourceFit:
    def reset(self, policy_seed, public_config): pass
    def decide(self, observation):
        jobs = {j.id:j for j in observation.ready_jobs}
        return StartA_v0(min(observation.eligible_job_ids,
                            key=lambda id: (jobs[id].cpu_units+jobs[id].memory_units,
                                            jobs[id].arrival_tick, id)))

class BadAction:
    def reset(self, policy_seed, public_config): pass
    def decide(self, observation): return StartA_v0("UNKNOWN")

class NoReturn:
    def reset(self, policy_seed, public_config): pass
    def decide(self, observation): return None

class Throws:
    def reset(self, policy_seed, public_config): pass
    def decide(self, observation): raise RuntimeError("test sentinel")

class ResetThrows:
    def reset(self, policy_seed, public_config): raise RuntimeError("test sentinel")
    def decide(self, observation): raise AssertionError("never")

def make_jobs(n: int, family: str, load: str, cap: Capacity, seed: int):
    rng = Random(seed)
    out = []
    for i in range(n):
        arrival = (i*3 if load=="light" else i//5)
        if family=="bursty":
            arrival = (i//16)* (48 if load=="light" else 2)
        if family=="uniform":
            cpu = 1
            mem = 1
            d = 2
        elif family=="heterogeneous":
            cpu = rng.randint(1, cap.cpu_units)
            mem = rng.randint(1, cap.memory_units)
            d = rng.randint(1, 8)
        else:
            cpu = rng.randint(1, cap.cpu_units)
            mem = rng.randint(1, cap.memory_units)
            d = rng.randint(1, 5)
        out.append(JobSpecPrivate(f"J{i:06d}", arrival, cpu, mem, d+1, d))
    return tuple(out)

def digest(result):
    data = asdict(result)
    encoded = json.dumps({"schema":"D006_Result_v1","result":data},sort_keys=True,
                         separators=(",",":"),ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def assert_equal(jobs, capacity, policy_type=FCFSScanningPolicy, cutoff=None):
    kw = {"evaluation_cutoff_tick":cutoff}
    a = simulate(jobs, capacity, policy_type(), **kw)
    b = simpy_adapter(jobs, capacity, policy_type(), **kw)
    if a != b:
        raise AssertionError(f"DIFF reference={digest(a)} simpy={digest(b)} "
                             f"n={len(jobs)} cap={capacity} cutoff={cutoff} "
                             f"eventsA={a.events[:15]} eventsB={b.events[:15]}")
    return a, digest(a)

def correctness():
    J=JobSpecPrivate
    cases = [
        ("A",(J("J2",0,1,1,1,1), J("J1",0,2,1,3,3)),Capacity(2,2),None),
        ("B",(J("J1",0,1,1,2,2),J("J2",2,1,1,1,1)),Capacity(1,1),None),
        ("C",(J("J1",0,1,1,5,5),J("J2",0,1,1,1,1)),Capacity(1,1),3),
        ("HOL",(J("R",0,1,1,5,5),J("H",1,2,1,1,1),J("Z",1,1,1,1,1)),Capacity(2,2),None),
        ("empty",(), Capacity(1,1),None),
        ("infeasible",(J("U",0,2,2,1,1),), Capacity(1,1),None),
        ("tie",(J("X",0,1,1,1,1),J("Y",0,1,1,1,1),J("Z",1,1,1,1,1)),Capacity(2,2),None),
        ("edgeH",(J("Z",0,1,1,2,2),),Capacity(1,1),2),
    ]
    results=[]
    for name,jobs,cap,h in cases:
        for pol in (FCFSScanningPolicy,ResourceFit):
            _,hashval=assert_equal(jobs,cap,pol,h)
            results.append((name,pol.__name__,hashval))
            if jobs:
                assert_equal(tuple(reversed(jobs)),cap,pol,h)
    for typ in (BadAction,NoReturn,Throws,ResetThrows):
        assert_equal((J("X",0,1,1,1,1),),Capacity(1,1),typ)
    for seed in range(64):
        rng=Random(seed)
        cap=Capacity(rng.randint(1,4),rng.randint(1,5))
        jobs=tuple(J(f"J{i:04d}",rng.randint(0,12),rng.randint(1,cap.cpu_units+1),
                     rng.randint(1,cap.memory_units+1),rng.randint(1,9),rng.randint(1,9))
                   for i in range(rng.randint(0,20)))
        for pol in (FCFSScanningPolicy,ResourceFit):
            assert_equal(jobs,cap,pol)
            assert_equal(tuple(reversed(jobs)),cap,pol)
            if jobs:
                cutoff = max(j.arrival_tick for j in jobs)+1
                assert_equal(jobs,cap,pol,cutoff)
    return {"golden_policy_cases":len(results),"negative_policy_cases":4,
            "random_seeds":64,"random_variants_per_seed":6}

def pilot(output: Path):
    import gc
    records=[]
    # Bounded pilot only: full preregistered matrix remains future gate.
    for n in (100,1000):
        for family in ("uniform","heterogeneous","bursty"):
            for load in ("light","saturated"):
                cap=Capacity(8,16)
                seed=1000+n+(0 if family=="uniform" else 200 if family=="heterogeneous" else 400)+(0 if load=="light" else 700)
                jobs=make_jobs(n,family,load,cap,seed)
                ref,h=assert_equal(jobs,cap)
                for engine,fn in (("custom",simulate),("simpy",simpy_adapter)):
                    for rep in range(3):
                        gc.collect()
                        t0=perf_counter_ns()
                        c0=process_time_ns()
                        result=fn(jobs,cap,FCFSScanningPolicy())
                        wall=perf_counter_ns()-t0
                        cpu=process_time_ns()-c0
                        assert result==ref
                        records.append({"engine":engine,"n":n,"family":family,"load":load,
                            "capacity":[8,16],"seed":seed,"repeat":rep,"time_ns":wall,
                            "cpu_ns":cpu,"decisions":result.decisions,
                            "events":len(result.events),"trace_hash":h,
                            "maxrss_kib_process":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    output.parent.mkdir(exist_ok=True,parents=True)
    manifest={"protocol":"D006_pilot_v1","pr25_head":"f39ed8a2cf10febc8affc0525c29e4a6a25b9be7",
              "python":sys.version,"platform":platform.platform(),"simpy":simpy.__version__,
              "note":"Exploratory 3 reps/cell; NOT preregistered definitive matrix; peak RSS is process-global high watermark, not per-engine isolation"}
    output.write_text(json.dumps({"manifest":manifest,"records":records},indent=2)+"\n")
    summary=[]
    for n in (100,1000):
        for family in ("uniform","heterogeneous","bursty"):
            for load in ("light","saturated"):
                data={engine:median(x["time_ns"] for x in records if x["n"]==n and
                    x["family"]==family and x["load"]==load and x["engine"]==engine)
                    for engine in ("custom","simpy")}
                summary.append({"n":n,"family":family,"load":load,
                                "custom_over_simpy_speed":round(data["simpy"]/data["custom"],3)})
    return {"pilot_record_count":len(records),"speed_ratios":summary,"output":str(output)}

if __name__=="__main__":
    verified=correctness()
    print("CORRECTNESS_PASS",json.dumps(verified),flush=True)
    if "--pilot" in sys.argv:
        print("PILOT",json.dumps(pilot(Path("benchmarks/d006/pilot_results.json"))),flush=True)