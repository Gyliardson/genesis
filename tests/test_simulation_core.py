"""Independent hand-calculated and negative oracles for the simulation reference engine."""

from dataclasses import FrozenInstanceError, asdict
from random import Random

import pytest

from genesis.simulation import (
    Capacity,
    FCFSScanningPolicy,
    JobSpecPrivate,
    StartA_v0,
    simulate,
)


def job(
    id: str,
    arrival: int,
    cpu: int,
    memory: int,
    actual: int,
    estimate: int | None = None,
) -> JobSpecPrivate:
    return JobSpecPrivate(id, arrival, cpu, memory, actual if estimate is None else estimate, actual)


def outcomes(result):
    return {j.id: j for j in result.jobs}


def integrated_resource_ticks(events) -> tuple[int, int]:
    """Integrate the Core's actual post-transition resource state over event intervals."""
    assert [event.sequence for event in events] == list(range(len(events)))
    assert [event.tick for event in events] == sorted(event.tick for event in events)
    return (
        sum(
            (next_event.tick - event.tick) * getattr(event, dimension)
            for event, next_event in zip(events, events[1:])
        )
        for dimension in ("cpu_allocated", "memory_allocated")
    )


def assert_event_conservation(result, specs, capacity) -> None:
    """Independently replay log transitions without relying on Core's private state."""
    truth = {spec.id: spec for spec in specs}
    started = set()
    finished = set()
    running = set()
    for event in result.events:
        if event.kind == "START":
            assert event.job_id not in started
            assert event.job_id in truth
            started.add(event.job_id)
            running.add(event.job_id)
        elif event.kind == "COMPLETE":
            assert event.job_id in running
            assert event.job_id not in finished
            running.remove(event.job_id)
            finished.add(event.job_id)
        assert event.cpu_allocated == sum(truth[job_id].cpu_units for job_id in running)
        assert event.memory_allocated == sum(truth[job_id].memory_units for job_id in running)
        assert 0 <= event.cpu_allocated <= capacity.cpu_units
        assert 0 <= event.memory_allocated <= capacity.memory_units
    assert {j.id for j in result.jobs if j.phase == "RUNNING"} == running
    assert {j.id for j in result.jobs if j.phase == "COMPLETED"} == finished


def test_golden_a_contention_and_resource_integrals() -> None:
    result = simulate(
        (job("J2", 0, 1, 1, 1), job("J1", 0, 2, 1, 3)),
        Capacity(2, 2),
        FCFSScanningPolicy(),
    )
    assert result.run_status == "COMPLETED"
    assert result.stop_tick == 4
    assert [(j.id, j.started_at, j.completed_at) for j in result.jobs] == [
        ("J1", 0, 3),
        ("J2", 3, 4),
    ]
    sojourn = [j.completed_at - spec.arrival_tick for j, spec in zip(
        result.jobs, sorted((job("J1", 0, 2, 1, 3), job("J2", 0, 1, 1, 1)), key=lambda s: (s.arrival_tick, s.id))
    )]
    assert sojourn == [3, 4]
    assert integrated_resource_ticks(result.events) == (7, 4)
    assert_event_conservation(
        result,
        (job("J1", 0, 2, 1, 3), job("J2", 0, 1, 1, 1)),
        Capacity(2, 2),
    )
    assert result.cpu_allocated_at_stop == result.memory_allocated_at_stop == 0


def test_golden_b_completes_before_simultaneous_arrival_and_start() -> None:
    result = simulate(
        (job("J1", 0, 1, 1, 2), job("J2", 2, 1, 1, 1)),
        Capacity(1, 1),
        FCFSScanningPolicy(),
    )
    assert result.stop_tick == 3
    assert [(j.id, j.started_at, j.completed_at) for j in result.jobs] == [
        ("J1", 0, 2),
        ("J2", 2, 3),
    ]
    at_two = [(e.kind, e.job_id) for e in result.events if e.tick == 2]
    # After starting J2 the Core records its forced advance to J2 completion.
    assert at_two == [
        ("COMPLETE", "J1"),
        ("ARRIVE", "J2"),
        ("START", "J2"),
        ("FORCED_ADVANCE", None),
    ]


def test_golden_c_fixed_h_preserves_all_censored_jobs() -> None:
    result = simulate(
        (job("J1", 0, 1, 1, 5), job("J2", 0, 1, 1, 1)),
        Capacity(1, 1),
        FCFSScanningPolicy(),
        evaluation_cutoff_tick=3,
    )
    assert result.run_status == "CENSORED_FIXED_H"
    assert result.stop_reason == "EVALUATION_CUTOFF"
    assert result.stop_tick == 3
    assert [(j.id, j.phase, j.started_at, j.completed_at) for j in result.jobs] == [
        ("J1", "RUNNING", 0, None),
        ("J2", "READY", None, None),
    ]
    assert not [e for e in result.events if e.kind == "COMPLETE"]
    assert result.cpu_allocated_at_stop == 1
    assert integrated_resource_ticks(result.events) == (3, 3)
    assert_event_conservation(
        result,
        (job("J1", 0, 1, 1, 5), job("J2", 0, 1, 1, 1)),
        Capacity(1, 1),
    )


def test_head_of_line_discriminator_follows_fcfs_scanning() -> None:
    result = simulate(
        (
            job("R", 0, 1, 1, 5),
            job("H", 1, 2, 1, 1),
            job("Z", 1, 1, 1, 1),
        ),
        Capacity(2, 2),
        FCFSScanningPolicy(),
    )
    assert result.run_status == "COMPLETED"
    assert {
        j.id: (j.started_at, j.completed_at) for j in result.jobs
    } == {"R": (0, 5), "H": (5, 6), "Z": (1, 2)}
    assert [(e.tick, e.job_id) for e in result.events if e.kind == "START"] == [
        (0, "R"),
        (1, "Z"),
        (5, "H"),
    ]


def test_concurrent_admissions_at_one_tick() -> None:
    result = simulate(
        (job("A", 0, 1, 1, 3), job("B", 0, 1, 1, 2)),
        Capacity(2, 2),
        FCFSScanningPolicy(),
    )
    assert result.decisions == 2
    assert [(e.tick, e.job_id) for e in result.events if e.kind == "START"] == [
        (0, "A"),
        (0, "B"),
    ]
    assert result.stop_tick == 3
    assert result.cpu_allocated_at_stop == 0


def test_empty_trace_is_completed_without_policy_decision() -> None:
    result = simulate((), Capacity(1, 1), FCFSScanningPolicy())
    assert result.run_status == "COMPLETED"
    assert result.stop_tick == 0
    assert not result.jobs
    assert result.decisions == 0


def test_individually_unfit_job_is_explicitly_rejected() -> None:
    result = simulate((job("too-big", 0, 2, 1, 3),), Capacity(1, 2), FCFSScanningPolicy())
    assert outcomes(result)["too-big"].phase == "REJECTED_INFEASIBLE"
    assert any(e.kind == "REJECT_INFEASIBLE" for e in result.events)
    assert result.decisions == 0
    assert result.cpu_allocated_at_stop == 0


def test_permutation_replay_and_canonical_events() -> None:
    specs = (
        job("C", 2, 1, 1, 1),
        job("B", 0, 1, 1, 2),
        job("A", 0, 1, 1, 1),
    )
    first = simulate(specs, Capacity(2, 2), FCFSScanningPolicy(), policy_seed=27)
    second = simulate(tuple(reversed(specs)), Capacity(2, 2), FCFSScanningPolicy(), policy_seed=27)
    assert first == second
    assert [e.sequence for e in first.events] == list(range(len(first.events)))
    assert [e.tick for e in first.events] == sorted(e.tick for e in first.events)
    assert all(0 <= e.cpu_allocated <= 2 and 0 <= e.memory_allocated <= 2 for e in first.events)
    assert all(j.phase == "COMPLETED" for j in first.jobs)


class SpyPolicy(FCFSScanningPolicy):
    def __init__(self):
        self.observations = []
        self.public_config = None

    def reset(self, policy_seed, public_config):
        self.public_config = public_config

    def decide(self, observation):
        self.observations.append(observation)
        return super().decide(observation)


def test_public_projection_excludes_true_duration_and_future_state() -> None:
    base = (job("J", 0, 1, 1, 2, estimate=9), job("future", 6, 1, 1, 1))
    changed = (job("J", 0, 1, 1, 5, estimate=9), job("future", 6, 1, 1, 9))
    a, b = SpyPolicy(), SpyPolicy()
    simulate(base, Capacity(1, 1), a, policy_seed=12)
    simulate(changed, Capacity(1, 1), b, policy_seed=12)
    assert a.observations[0] == b.observations[0]
    assert a.public_config == b.public_config
    assert a.public_config.action_schema == "ActionA_v0"
    obs = a.observations[0]
    assert obs.eligible_job_ids == ("J",)
    assert obs.wait_allowed is False
    assert "actual" not in repr(asdict(obs))
    assert "future" not in repr(asdict(obs))
    assert obs.ready_jobs[0].estimated_duration_ticks == 9
    with pytest.raises(FrozenInstanceError):
        obs.now_tick = 99


class InvalidActionPolicy(FCFSScanningPolicy):
    def __init__(self, action):
        self.action = action

    def decide(self, observation):
        return self.action


@pytest.mark.parametrize(
    "action,reason",
    [
        ("WAIT", "INVALID_ACTION"),
        (StartA_v0("missing"), "INVALID_ACTION"),
        (None, "NO_RETURN"),
        (object(), "INVALID_ACTION"),
    ],
)
def test_invalid_actions_fail_closed_without_reserving(action, reason) -> None:
    result = simulate((job("A", 0, 1, 1, 1),), Capacity(1, 1), InvalidActionPolicy(action))
    assert result.run_status == "ERROR"
    assert result.stop_reason == reason
    assert outcomes(result)["A"].phase == "READY"
    assert result.cpu_allocated_at_stop == result.memory_allocated_at_stop == 0
    assert not [e for e in result.events if e.kind == "START"]


class EqualityBomb:
    def __init__(self):
        self.comparisons = 0

    def __eq__(self, other):
        self.comparisons += 1
        raise AssertionError("Action payload must never execute custom comparison code")


def test_untrusted_action_payload_rejected_without_running_equality() -> None:
    bomb = EqualityBomb()
    result = simulate(
        (job("A", 0, 1, 1, 1),),
        Capacity(1, 1),
        InvalidActionPolicy(StartA_v0(bomb)),
    )
    assert result.run_status == "ERROR"
    assert result.stop_reason == "INVALID_ACTION"
    assert bomb.comparisons == 0
    assert outcomes(result)["A"].phase == "READY"
    assert not [event for event in result.events if event.kind == "START"]


@pytest.mark.parametrize("payload", [True, 1, ["A"], None])
def test_wrong_runtime_job_id_types_fail_closed(payload) -> None:
    result = simulate(
        (job("A", 0, 1, 1, 1),),
        Capacity(1, 1),
        InvalidActionPolicy(StartA_v0(payload)),
    )
    assert result.run_status == "ERROR"
    assert result.stop_reason == "INVALID_ACTION"


class ExplodingPolicy(FCFSScanningPolicy):
    def decide(self, observation):
        raise RuntimeError("secret diagnostic must not appear")


def test_policy_exception_is_sanitized_and_is_not_counted_as_success() -> None:
    result = simulate((job("A", 0, 1, 1, 1),), Capacity(1, 1), ExplodingPolicy())
    assert result.run_status == "ERROR"
    assert result.stop_reason == "DECIDE_EXCEPTION"
    assert "secret" not in repr(result)
    assert outcomes(result)["A"].phase == "READY"


class RepeatedPolicy(FCFSScanningPolicy):
    def decide(self, observation):
        return StartA_v0("A")


def test_repeated_start_rejected_without_second_allocation() -> None:
    result = simulate(
        (job("A", 0, 1, 1, 2), job("B", 0, 1, 1, 1)),
        Capacity(2, 2),
        RepeatedPolicy(),
    )
    assert result.run_status == "ERROR"
    assert result.stop_reason == "INVALID_ACTION"
    assert outcomes(result)["A"].phase == "RUNNING"
    assert outcomes(result)["B"].phase == "READY"
    assert result.cpu_allocated_at_stop == result.memory_allocated_at_stop == 1
    assert [e.kind for e in result.events].count("START") == 1


def test_completion_exactly_at_cutoff_counts_without_new_start() -> None:
    result = simulate(
        (job("A", 0, 1, 1, 2), job("B", 0, 1, 1, 1)),
        Capacity(1, 1),
        FCFSScanningPolicy(),
        evaluation_cutoff_tick=2,
    )
    assert outcomes(result)["A"].phase == "COMPLETED"
    assert outcomes(result)["B"].phase == "READY"
    assert result.run_status == "CENSORED_FIXED_H"
    assert not [e for e in result.events if e.kind == "START" and e.tick == 2]


@pytest.mark.parametrize(
    "spec",
    [
        ("A", -1, 1, 1, 1, 1),
        ("A", 0, 0, 1, 1, 1),
        ("A", 0, 1, 1, 0, 1),
        ("A", 0, 1, 1, 1, 0),
        ("A", 0, 1, 1, 1, True),
        ("A", 0, 1.0, 1, 1, 1),
    ],
)
def test_invalid_spec_values_rejected(spec) -> None:
    with pytest.raises(ValueError):
        JobSpecPrivate(*spec)


def test_duplicate_ids_and_invalid_capacity_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        simulate((job("A", 0, 1, 1, 1), job("A", 1, 1, 1, 1)), Capacity(2, 2), FCFSScanningPolicy())
    with pytest.raises(ValueError):
        Capacity(True, 1)
    with pytest.raises(ValueError):
        Capacity(1, -1)


@pytest.mark.parametrize("scenario_seed", range(64))
def test_random_small_traces_replay_resource_integrals_and_progress(scenario_seed) -> None:
    """Deterministic property probes over competing CPU/memory traces, including rejects."""
    rng = Random(scenario_seed)
    capacity = Capacity(rng.randint(1, 4), rng.randint(1, 4))
    specs = tuple(
        job(
            f"J{i:02d}",
            rng.randrange(7),
            rng.randint(1, capacity.cpu_units + 1),
            rng.randint(1, capacity.memory_units + 1),
            rng.randint(1, 6),
            estimate=rng.randint(1, 6),
        )
        for i in range(rng.randint(4, 18))
    )
    first = simulate(specs, capacity, FCFSScanningPolicy(), policy_seed=17)
    replay = simulate(tuple(reversed(specs)), capacity, FCFSScanningPolicy(), policy_seed=17)
    assert first == replay
    assert first.run_status == "COMPLETED"
    assert all(j.phase in {"COMPLETED", "REJECTED_INFEASIBLE"} for j in first.jobs)
    assert_event_conservation(first, specs, capacity)

    by_id = {spec.id: spec for spec in specs}
    completed = [outcome for outcome in first.jobs if outcome.phase == "COMPLETED"]
    independent_integrals = (
        sum(
            by_id[outcome.id].cpu_units * (outcome.completed_at - outcome.started_at)
            for outcome in completed
        ),
        sum(
            by_id[outcome.id].memory_units * (outcome.completed_at - outcome.started_at)
            for outcome in completed
        ),
    )
    assert integrated_resource_ticks(first.events) == independent_integrals
    assert first.cpu_allocated_at_stop == first.memory_allocated_at_stop == 0


def test_cutoff_rejects_input_at_or_after_boundary() -> None:
    with pytest.raises(ValueError, match="cohort"):
        simulate(
            (job("A", 3, 1, 1, 1),),
            Capacity(1, 1),
            FCFSScanningPolicy(),
            evaluation_cutoff_tick=3,
        )
