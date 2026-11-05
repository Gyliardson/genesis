"""Independent literal D-006 event and allocation oracles; no engine-generated snapshots."""
from __future__ import annotations

import importlib.util
import unittest
from dataclasses import replace

from genesis.simulation.core import (
    Capacity,
    Event,
    FCFSScanningPolicy,
    JobOutcome,
    JobSpecPrivate,
    SimulationResult,
    StartA_v0,
    simulate,
)

# A row is (tick, event kind, job id, post-event CPU, post-event MEM).
# Every row, outcome, decision count and integral is manually specified.
CASES = {
    "A": (
        [("J2", 0, 1, 1, 1), ("J1", 0, 2, 1, 3)], (2, 2), None,
        [(0,"ARRIVE","J1",0,0),(0,"ARRIVE","J2",0,0),
         (0,"START","J1",2,1),(0,"FORCED_ADVANCE",None,2,1),
         (3,"COMPLETE","J1",0,0),(3,"START","J2",1,1),
         (3,"FORCED_ADVANCE",None,1,1),(4,"COMPLETE","J2",0,0),
         (4,"TERMINATE",None,0,0)],
        [("J1","COMPLETED",0,3),("J2","COMPLETED",3,4)],
        ("COMPLETED","ALL_COMPLETED",4,2,0,0), (7,4),
    ),
    "B": (
        [("J1",0,1,1,2),("J2",2,1,1,1)], (1,1), None,
        [(0,"ARRIVE","J1",0,0),(0,"START","J1",1,1),
         (0,"FORCED_ADVANCE",None,1,1),(2,"COMPLETE","J1",0,0),
         (2,"ARRIVE","J2",0,0),(2,"START","J2",1,1),
         (2,"FORCED_ADVANCE",None,1,1),(3,"COMPLETE","J2",0,0),
         (3,"TERMINATE",None,0,0)],
        [("J1","COMPLETED",0,2),("J2","COMPLETED",2,3)],
        ("COMPLETED","ALL_COMPLETED",3,2,0,0), (3,3),
    ),
    "C": (
        [("J1",0,1,1,5),("J2",0,1,1,1)], (1,1), 3,
        [(0,"ARRIVE","J1",0,0),(0,"ARRIVE","J2",0,0),
         (0,"START","J1",1,1),(0,"FORCED_ADVANCE",None,1,1),
         (3,"TERMINATE",None,1,1)],
        [("J1","RUNNING",0,None),("J2","READY",None,None)],
        ("CENSORED_FIXED_H","EVALUATION_CUTOFF",3,1,1,1), (3,3),
    ),
    "HOL": (
        [("R",0,1,1,5),("H",1,2,1,1),("Z",1,1,1,1)], (2,2), None,
        [(0,"ARRIVE","R",0,0),(0,"START","R",1,1),
         (0,"FORCED_ADVANCE",None,1,1),(1,"ARRIVE","H",1,1),
         (1,"ARRIVE","Z",1,1),(1,"START","Z",2,2),
         (1,"FORCED_ADVANCE",None,2,2),(2,"COMPLETE","Z",1,1),
         (2,"FORCED_ADVANCE",None,1,1),(5,"COMPLETE","R",0,0),
         (5,"START","H",2,1),(5,"FORCED_ADVANCE",None,2,1),
         (6,"COMPLETE","H",0,0),(6,"TERMINATE",None,0,0)],
        [("R","COMPLETED",0,5),("H","COMPLETED",5,6),
         ("Z","COMPLETED",1,2)], ("COMPLETED","ALL_COMPLETED",6,3,0,0), (8,7),
    ),
    "MULTI_TIE": (
        [("B",0,1,1,2),("A",0,1,1,2),
         ("D",2,1,1,1),("C",2,1,1,1)], (2,2), None,
        [(0,"ARRIVE","A",0,0),(0,"ARRIVE","B",0,0),
         (0,"START","A",1,1),(0,"START","B",2,2),
         (0,"FORCED_ADVANCE",None,2,2),(2,"COMPLETE","A",1,1),
         (2,"COMPLETE","B",0,0),(2,"ARRIVE","C",0,0),
         (2,"ARRIVE","D",0,0),(2,"START","C",1,1),
         (2,"START","D",2,2),(2,"FORCED_ADVANCE",None,2,2),
         (3,"COMPLETE","C",1,1),(3,"COMPLETE","D",0,0),
         (3,"TERMINATE",None,0,0)],
        [("A","COMPLETED",0,2),("B","COMPLETED",0,2),
         ("C","COMPLETED",2,3),("D","COMPLETED",2,3)],
        ("COMPLETED","ALL_COMPLETED",3,4,0,0), (6,6),
    ),
}


def expected_result(case):
    _, _, _, rows, outcomes, summary, _ = case
    status, reason, stop, decisions, cpu_stop, mem_stop = summary
    return SimulationResult(
        status, reason, stop,
        tuple(Event(i, *row) for i, row in enumerate(rows)),
        tuple(JobOutcome(*outcome) for outcome in outcomes),
        decisions, cpu_stop, mem_stop,
    )


def resource_integrals(events, stop):
    cpu = mem = 0
    for i, event in enumerate(events):
        next_tick = events[i + 1].tick if i + 1 < len(events) else stop
        if next_tick < event.tick:
            raise AssertionError("event clock moved backwards")
        cpu += event.cpu_allocated * (next_tick - event.tick)
        mem += event.memory_allocated * (next_tick - event.tick)
    return cpu, mem


def engines():
    result = [simulate]
    if importlib.util.find_spec("simpy"):
        from simpy_adapter_benchmark import simpy_adapter
        result.append(simpy_adapter)
    return result


def jobs_for(rows):
    return tuple(JobSpecPrivate(name, arrival, cpu, mem, duration, duration)
                 for name, arrival, cpu, mem, duration in rows)


class IndependentOracles(unittest.TestCase):
    def test_manual_event_outcome_integral_oracles(self):
        for label, case in CASES.items():
            rows, resource, cutoff, *_ = case
            expected = expected_result(case)
            self.assertEqual(resource_integrals(expected.events, expected.stop_tick),
                             case[-1], label)
            for engine in engines():
                for order in (jobs_for(rows), tuple(reversed(jobs_for(rows)))):
                    with self.subTest(case=label, engine=engine.__name__, order=order):
                        actual = engine(order, Capacity(*resource), FCFSScanningPolicy(),
                                        evaluation_cutoff_tick=cutoff)
                        self.assertEqual(actual, expected)
                        self.assertEqual(resource_integrals(actual.events, actual.stop_tick),
                                         case[-1])

    def test_deliberate_tie_order_mutation_fails(self):
        expected = expected_result(CASES["MULTI_TIE"])
        events = list(expected.events)
        events[5], events[6] = replace(events[6], sequence=5), replace(events[5], sequence=6)
        mutant = replace(expected, events=tuple(events))
        with self.assertRaises(AssertionError):
            self.assertEqual(mutant, expected)

    def test_invalid_specs_constructor(self):
        base = dict(id="X", arrival_tick=0, cpu_units=1, memory_units=1,
                    actual_duration_ticks=1, estimated_duration_ticks=1)
        cases = [
            (dict(id=""), "job id must be a nonempty string"),
            (dict(id=1), "job id must be a nonempty string"),
            (dict(arrival_tick=True), "arrival_tick must be an integer >= 0"),
            (dict(arrival_tick=-1), "arrival_tick must be an integer >= 0"),
            (dict(cpu_units=0), "cpu_units must be an integer >= 1"),
            (dict(memory_units=1.2), "memory_units must be an integer >= 1"),
            (dict(actual_duration_ticks=False),
             "actual_duration_ticks must be an integer >= 1"),
            (dict(estimated_duration_ticks=0),
             "estimated_duration_ticks must be an integer >= 1"),
        ]
        for mutation, message in cases:
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, message):
                JobSpecPrivate(**(base | mutation))
        with self.assertRaisesRegex(ValueError, "cpu_units must be an integer >= 1"):
            Capacity(True, 1)

    def test_validation_exception_types_and_messages(self):
        valid = jobs_for([("X",0,1,1,1)])
        cases = [
            (valid + valid, Capacity(1,1), {}, ValueError, "job IDs must be unique"),
            (list(valid), Capacity(1,1), {}, TypeError, "jobs must be a tuple"),
            (("X",), Capacity(1,1), {}, TypeError, "jobs must be a tuple"),
            (valid, "bad", {}, TypeError, "capacity must be Capacity"),
            (valid, Capacity(1,1), {"policy_seed": True}, ValueError, "policy_seed"),
            (valid, Capacity(1,1), {"policy_seed": 0.5}, ValueError, "policy_seed"),
            (valid, Capacity(1,1), {"policy_seed": -1}, ValueError, "policy_seed"),
            (valid, Capacity(1,1), {"evaluation_cutoff_tick": False},
             ValueError, "evaluation_cutoff_tick"),
            (valid, Capacity(1,1), {"evaluation_cutoff_tick": 0.5},
             ValueError, "evaluation_cutoff_tick"),
            (valid, Capacity(1,1), {"evaluation_cutoff_tick": -1},
             ValueError, "evaluation_cutoff_tick"),
            (valid, Capacity(1,1), {"evaluation_cutoff_tick": 0},
             ValueError, "fixed-H input cohort must arrive before evaluation cutoff"),
        ]
        for engine in engines():
            for jobs, cap, kwargs, exc, message in cases:
                with self.subTest(engine=engine.__name__, kwargs=kwargs), self.assertRaisesRegex(
                    exc, message
                ):
                    engine(jobs, cap, FCFSScanningPolicy(), **kwargs)

    def test_policy_adversarial_payload_and_exception(self):
        class Returns:
            def __init__(self, value):
                self.value = value

            def reset(self, seed, config):
                pass

            def decide(self, observation):
                return self.value

        class Raises(Returns):
            def decide(self, observation):
                raise RuntimeError("private error")

        class ResetRaises(Returns):
            def reset(self, seed, config):
                raise RuntimeError("private error")

        class SubStart(StartA_v0):
            pass

        class Hostile:
            def __eq__(self, value):
                raise RuntimeError("must not compare arbitrary payload")

        cases = [
            (Returns(None), "NO_RETURN", 1),
            (Returns("X"), "INVALID_ACTION", 1),
            (Returns(StartA_v0), "INVALID_ACTION", 1),
            (Returns(StartA_v0("unknown")), "INVALID_ACTION", 1),
            (Returns(StartA_v0(1)), "INVALID_ACTION", 1),
            (Returns(StartA_v0(True)), "INVALID_ACTION", 1),
            (Returns(StartA_v0(None)), "INVALID_ACTION", 1),
            (Returns(SubStart("X")), "INVALID_ACTION", 1),
            (Returns(Hostile()), "INVALID_ACTION", 1),
            (Raises(None), "DECIDE_EXCEPTION", 1),
            (ResetRaises(None), "DECIDE_EXCEPTION", 0),
        ]
        for engine in engines():
            for policy, reason, decisions in cases:
                with self.subTest(engine=engine.__name__, reason=reason,
                                  policy=type(policy).__name__):
                    result = engine(jobs_for([("X",0,1,1,1)]),
                                    Capacity(1,1), policy)
                    self.assertEqual((result.run_status, result.stop_reason,
                                      result.decisions), ("ERROR", reason, decisions))
                    self.assertEqual(result.events[-1].kind, "TERMINATE")


if __name__ == "__main__":
    unittest.main()
