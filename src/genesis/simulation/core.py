"""Event-driven, deterministic single-node scheduling reference engine (ActionA_v0).

Experimental M1 implementation. D-017 fixes the action space; event/horizon,
error/fallback and engine-choice ADRs remain independently reviewable. No real jobs
are executed. Policies receive only immutable public observations.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import Protocol


def _integer(name: str, value: int, minimum: int) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


@dataclass(frozen=True, slots=True)
class JobSpecPrivate:
    """Exogenous job truth; pass to the Core only, never to a Policy."""

    id: str
    arrival_tick: int
    cpu_units: int
    memory_units: int
    estimated_duration_ticks: int
    actual_duration_ticks: int

    def __post_init__(self) -> None:
        if type(self.id) is not str or not self.id:
            raise ValueError("job id must be a nonempty string")
        _integer("arrival_tick", self.arrival_tick, 0)
        for name in (
            "cpu_units",
            "memory_units",
            "estimated_duration_ticks",
            "actual_duration_ticks",
        ):
            _integer(name, getattr(self, name), 1)


@dataclass(frozen=True, slots=True)
class Capacity:
    cpu_units: int
    memory_units: int

    def __post_init__(self) -> None:
        _integer("cpu_units", self.cpu_units, 1)
        _integer("memory_units", self.memory_units, 1)


@dataclass(frozen=True, slots=True)
class ReadyJobPublic:
    id: str
    arrival_tick: int
    cpu_units: int
    memory_units: int
    estimated_duration_ticks: int
    waiting_age_ticks: int


@dataclass(frozen=True, slots=True)
class ObservationV0:
    """No actual durations, future events, run progress, or scenario RNG."""

    schema_version: str
    now_tick: int
    cpu_capacity: int
    cpu_free: int
    memory_capacity: int
    memory_free: int
    ready_jobs: tuple[ReadyJobPublic, ...]
    eligible_job_ids: tuple[str, ...]
    wait_allowed: bool = False


@dataclass(frozen=True, slots=True)
class PublicPolicyConfig:
    protocol_id: str
    observation_schema: str
    cpu_capacity: int
    memory_capacity: int


@dataclass(frozen=True, slots=True)
class StartA_v0:
    job_id: str


class PolicyV0(Protocol):
    def reset(self, policy_seed: int, public_config: PublicPolicyConfig) -> None: ...

    def decide(self, observation: ObservationV0) -> StartA_v0: ...


class FCFSScanningPolicy:
    """First *eligible* arrival/id, not head-of-line FCFS and not reserved backfilling."""

    def reset(self, policy_seed: int, public_config: PublicPolicyConfig) -> None:
        pass

    def decide(self, observation: ObservationV0) -> StartA_v0:
        return StartA_v0(observation.eligible_job_ids[0])


@dataclass(frozen=True, slots=True)
class Event:
    sequence: int
    tick: int
    kind: str
    job_id: str | None
    cpu_allocated: int
    memory_allocated: int


@dataclass(frozen=True, slots=True)
class JobOutcome:
    id: str
    phase: str
    started_at: int | None
    completed_at: int | None


@dataclass(frozen=True, slots=True)
class SimulationResult:
    run_status: str
    stop_reason: str
    stop_tick: int
    events: tuple[Event, ...]
    jobs: tuple[JobOutcome, ...]
    decisions: int
    cpu_allocated_at_stop: int
    memory_allocated_at_stop: int


@dataclass(slots=True)
class _Runtime:
    phase: str = "FUTURE"
    started_at: int | None = None
    completed_at: int | None = None


def simulate(
    jobs: tuple[JobSpecPrivate, ...],
    capacity: Capacity,
    policy: PolicyV0,
    *,
    policy_seed: int = 0,
    evaluation_cutoff_tick: int | None = None,
) -> SimulationResult:
    """Run a finite exogenous trace under the ratified work-conserving ActionA_v0.

    The optional fixed evaluation cutoff is a diagnostic proposal for D-020,
    not a ratified experiment protocol. Jobs supplied for this mode must arrive
    strictly before its boundary. Completions at the boundary count, but no
    START is legal at the boundary. Censored jobs remain in results.
    """
    _integer("policy_seed", policy_seed, 0)
    if evaluation_cutoff_tick is not None:
        _integer("evaluation_cutoff_tick", evaluation_cutoff_tick, 0)
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

    runtime = {j.id: _Runtime() for j in ordered}
    by_id = {j.id: j for j in ordered}
    completions: list[tuple[int, str]] = []
    event_log: list[Event] = []
    now = 0
    arrivals_index = 0
    cpu_allocated = 0
    memory_allocated = 0
    decisions = 0
    event_limit = 8 * len(ordered) + 16

    def record(kind: str, job_id: str | None = None) -> None:
        if len(event_log) >= event_limit:
            raise RuntimeError("event bound exceeded")
        event_log.append(
            Event(
                sequence=len(event_log),
                tick=now,
                kind=kind,
                job_id=job_id,
                cpu_allocated=cpu_allocated,
                memory_allocated=memory_allocated,
            )
        )

    def invariant() -> None:
        expected_cpu = sum(
            by_id[job_id].cpu_units
            for job_id, state in runtime.items()
            if state.phase == "RUNNING"
        )
        expected_memory = sum(
            by_id[job_id].memory_units
            for job_id, state in runtime.items()
            if state.phase == "RUNNING"
        )
        if not (
            cpu_allocated == expected_cpu
            and memory_allocated == expected_memory
            and 0 <= cpu_allocated <= capacity.cpu_units
            and 0 <= memory_allocated <= capacity.memory_units
        ):
            raise RuntimeError("resource conservation violated")

    def result(status: str, reason: str) -> SimulationResult:
        invariant()
        record("TERMINATE")
        return SimulationResult(
            run_status=status,
            stop_reason=reason,
            stop_tick=now,
            events=tuple(event_log),
            jobs=tuple(
                JobOutcome(
                    id=j.id,
                    phase=runtime[j.id].phase,
                    started_at=runtime[j.id].started_at,
                    completed_at=runtime[j.id].completed_at,
                )
                for j in ordered
            ),
            decisions=decisions,
            cpu_allocated_at_stop=cpu_allocated,
            memory_allocated_at_stop=memory_allocated,
        )

    config = PublicPolicyConfig(
        protocol_id="ActionA_v0",
        observation_schema="ObservationV0",
        cpu_capacity=capacity.cpu_units,
        memory_capacity=capacity.memory_units,
    )
    try:
        policy.reset(policy_seed, config)
    except Exception:
        return result("ERROR", "DECIDE_EXCEPTION")

    while True:
        # Process all completions before all arrivals at this tick.
        while completions and completions[0][0] == now:
            _, job_id = heapq.heappop(completions)
            state = runtime[job_id]
            if state.phase != "RUNNING":
                return result("ERROR", "SIMULATION_ERROR")
            spec = by_id[job_id]
            state.phase = "COMPLETED"
            state.completed_at = now
            cpu_allocated -= spec.cpu_units
            memory_allocated -= spec.memory_units
            invariant()
            record("COMPLETE", job_id)

        while arrivals_index < len(ordered) and ordered[arrivals_index].arrival_tick == now:
            spec = ordered[arrivals_index]
            arrivals_index += 1
            if spec.cpu_units > capacity.cpu_units or spec.memory_units > capacity.memory_units:
                runtime[spec.id].phase = "REJECTED_INFEASIBLE"
                record("REJECT_INFEASIBLE", spec.id)
            else:
                runtime[spec.id].phase = "READY"
                record("ARRIVE", spec.id)

        pending = any(state.phase in ("FUTURE", "READY", "RUNNING") for state in runtime.values())
        if evaluation_cutoff_tick is not None and now == evaluation_cutoff_tick:
            return result(
                "CENSORED_FIXED_H" if pending else "COMPLETED",
                "EVALUATION_CUTOFF" if pending else "ALL_COMPLETED",
            )

        ready = tuple(j for j in ordered if runtime[j.id].phase == "READY")
        eligible = tuple(
            j.id
            for j in ready
            if j.cpu_units <= capacity.cpu_units - cpu_allocated
            and j.memory_units <= capacity.memory_units - memory_allocated
        )
        if eligible:
            obs = ObservationV0(
                schema_version="ObservationV0",
                now_tick=now,
                cpu_capacity=capacity.cpu_units,
                cpu_free=capacity.cpu_units - cpu_allocated,
                memory_capacity=capacity.memory_units,
                memory_free=capacity.memory_units - memory_allocated,
                ready_jobs=tuple(
                    ReadyJobPublic(
                        id=j.id,
                        arrival_tick=j.arrival_tick,
                        cpu_units=j.cpu_units,
                        memory_units=j.memory_units,
                        estimated_duration_ticks=j.estimated_duration_ticks,
                        waiting_age_ticks=now - j.arrival_tick,
                    )
                    for j in ready
                ),
                eligible_job_ids=eligible,
            )
            decisions += 1
            try:
                action = policy.decide(obs)
            except Exception:
                return result("ERROR", "DECIDE_EXCEPTION")
            if action is None:
                return result("ERROR", "NO_RETURN")
            if type(action) is not StartA_v0 or action.job_id not in eligible:
                return result("ERROR", "INVALID_ACTION")
            spec = by_id[action.job_id]
            state = runtime[spec.id]
            # Safety revalidates against the authoritative private state.
            if (
                state.phase != "READY"
                or spec.cpu_units > capacity.cpu_units - cpu_allocated
                or spec.memory_units > capacity.memory_units - memory_allocated
            ):
                return result("ERROR", "INVALID_ACTION")
            cpu_allocated += spec.cpu_units
            memory_allocated += spec.memory_units
            state.phase = "RUNNING"
            state.started_at = now
            heapq.heappush(completions, (now + spec.actual_duration_ticks, spec.id))
            invariant()
            record("START", spec.id)
            continue  # Permit consecutive START actions at the same tick.

        next_arrival = ordered[arrivals_index].arrival_tick if arrivals_index < len(ordered) else None
        next_complete = completions[0][0] if completions else None
        future_events = [t for t in (next_arrival, next_complete) if t is not None]
        if not future_events:
            if ready:
                return result("POLICY_STALL", "NO_EXOGENOUS_PROGRESS")
            return result("COMPLETED", "ALL_COMPLETED")
        next_tick = min(future_events)
        if evaluation_cutoff_tick is not None:
            next_tick = min(next_tick, evaluation_cutoff_tick)
        if next_tick <= now:
            return result("ERROR", "SIMULATION_ERROR")
        record("FORCED_ADVANCE")
        now = next_tick
