"""Independent hand-calculated and negative oracles for the simulation reference engine."""

from dataclasses import FrozenInstanceError, asdict

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
    assert 2 * 3 + 1 * 1 == 7  # CPU resource-ticks in four time ticks.
    assert 1 * 3 + 1 * 1 == 4  # Memory resource-ticks.
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


def test_cutoff_rejects_input_at_or_after_boundary() -> None:
    with pytest.raises(ValueError, match="cohort"):
        simulate(
            (job("A", 3, 1, 1, 1),),
            Capacity(1, 1),
            FCFSScanningPolicy(),
            evaluation_cutoff_tick=3,
        )
