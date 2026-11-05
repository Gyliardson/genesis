"""No benchmark timing or engine execution in the D006_Exogenous_v2 test suite."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import unittest

from exogenous_v2 import (
    A_CELLS, HOLDOUT_NAMESPACE, S1_CELLS, S1_SEED_BY_N, Cell, RHO,
    a_order_seeds, a_seeds, arrival_rate, canonical, exp_gap, jobs_bytes,
    exogenous_cell, make_jobs_v2, offered_work_per_job, payload_bytes, plan_a, realized_load,
    sha256, substream,
)


class ExogenousV2Tests(unittest.TestCase):
    def test_matrix_pairwise_coverage_and_seeds(self):
        self.assertEqual(len(A_CELLS), 8)
        factors = (
            lambda c: c.n, lambda c: (c.cpu, c.memory),
            lambda c: c.load, lambda c: c.family, lambda c: c.policy,
        )
        actual = 0
        possible = 0
        for i in range(len(factors)):
            for j in range(i + 1, len(factors)):
                observed = {(factors[i](c), factors[j](c)) for c in A_CELLS}
                possible_pairs = {
                    (a, b) for a in {factors[i](c) for c in A_CELLS}
                    for b in {factors[j](c) for c in A_CELLS}
                }
                actual += len(observed)
                possible += len(possible_pairs)
        self.assertEqual((actual, possible), (62, 66))
        self.assertEqual(len(plan_a()), 16)
        seeds = [seed for _, seed, _ in plan_a()]
        orders = [order for _, _, order in plan_a()]
        self.assertEqual(len(set(seeds)), 16)
        self.assertEqual(len(set(orders)), 16)
        self.assertFalse(set(seeds) & {120101, 120211})
        self.assertTrue(all(not HOLDOUT_NAMESPACE[0] <= s <= HOLDOUT_NAMESPACE[1]
                            for s in seeds + orders))
        self.assertEqual(a_seeds(1), (710111, 710129))
        self.assertEqual(a_order_seeds(8), (820811, 820829))
        self.assertEqual(len(S1_CELLS), 6)
        self.assertEqual(S1_SEED_BY_N, {1000: 810011, 10000: 811011,
                                         100000: 812011})

    def test_analytic_b_and_lambda(self):
        cases = [
            ("uniform", (1, 1), 2.0),
            ("uniform", (8, 16), 0.25),
            ("heterogeneous", (1, 1), 4.5),
            ("heterogeneous", (8, 16), 2.53125),
            ("bursty", (1, 1), 3.0),
            ("bursty", (8, 16), 1.6875),
        ]
        for family, (cpu, mem), b in cases:
            for load in ("light", "saturated"):
                with self.subTest(family=family, cap=(cpu, mem), load=load):
                    cell = Cell("T01", 16, cpu, mem, load, family,
                                "FCFSScanningPolicy")
                    self.assertAlmostEqual(offered_work_per_job(cell), b)
                    self.assertAlmostEqual(arrival_rate(cell), RHO[load] / b)

    def test_replay_and_seed_diversity_in_actual_jobs_not_envelope(self):
        for family in ("uniform", "heterogeneous", "bursty"):
            cell = Cell("T01", 128, 8, 16, "light", family,
                        "FCFSScanningPolicy")
            first = make_jobs_v2(cell, 710111)
            second = make_jobs_v2(cell, 710129)
            self.assertEqual(first, make_jobs_v2(cell, 710111))
            self.assertNotEqual(sha256(jobs_bytes(first)),
                                sha256(jobs_bytes(second)))
            self.assertEqual(sha256(payload_bytes(cell, 710111, first)),
                             sha256(payload_bytes(cell, 710111,
                                                   make_jobs_v2(cell, 710111))))
            self.assertEqual(
                json.loads(payload_bytes(cell, 710111, first))["schema"],
                "D006_Exogenous_v2",
            )

    def test_policy_not_part_of_exogenous_rng_or_payload(self):
        resource_fit = Cell("T01", 128, 8, 16, "light", "heterogeneous",
                            "ResourceFit")
        fcfs = replace(resource_fit, policy="FCFSScanningPolicy")
        jobs = make_jobs_v2(resource_fit, 710111)
        self.assertEqual(jobs, make_jobs_v2(fcfs, 710111))
        self.assertEqual(payload_bytes(resource_fit, 710111, jobs),
                         payload_bytes(fcfs, 710111, jobs))
        self.assertNotIn("policy", exogenous_cell(resource_fit))

    def test_bursts_ties_and_monotone_time(self):
        for family in ("uniform", "heterogeneous", "bursty"):
            cell = Cell("T01", 97, 8, 16, "saturated", family,
                        "ResourceFit")
            jobs = make_jobs_v2(cell, 731011)
            arrivals = [j.arrival_tick for j in jobs]
            self.assertEqual(arrivals, sorted(arrivals))
            self.assertGreaterEqual(arrivals[0], 0)
            if family == "bursty":
                for start in range(0, len(jobs), 16):
                    self.assertEqual(len({j.arrival_tick
                                          for j in jobs[start:start+16]}), 1)
            self.assertEqual([j.id for j in jobs],
                             [f"J{i:06d}" for i in range(cell.n)])

    def test_private_durations_not_invertible_and_resource_fit(self):
        for family in ("heterogeneous", "bursty"):
            for cpu, memory in ((1, 1), (8, 16)):
                cell = Cell("T01", 256, cpu, memory, "light", family,
                            "ResourceFit")
                jobs = make_jobs_v2(cell, 710111)
                self.assertTrue(all(1 <= j.cpu_units <= cpu and
                                    1 <= j.memory_units <= memory
                                    for j in jobs))
                self.assertTrue(any(j.actual_duration_ticks !=
                                    j.estimated_duration_ticks - 1
                                    for j in jobs))
                self.assertTrue(any(j.actual_duration_ticks !=
                                    j.estimated_duration_ticks
                                    for j in jobs))
                if (cpu, memory) == (1, 1):
                    self.assertEqual({(j.cpu_units, j.memory_units)
                                      for j in jobs}, {(1, 1)})

    def test_uniform_known_truth_and_effective_seed(self):
        cell = Cell("T01", 128, 1, 1, "saturated", "uniform",
                    "FCFSScanningPolicy")
        jobs = make_jobs_v2(cell, 710111)
        self.assertEqual(
            {(j.cpu_units, j.memory_units, j.actual_duration_ticks,
              j.estimated_duration_ticks) for j in jobs}, {(1, 1, 2, 2)}
        )
        self.assertNotEqual(jobs, make_jobs_v2(cell, 710129))
        self.assertGreater(realized_load(cell, jobs)["arrival_window_ticks"], 0)

    def test_domain_separation_and_canonicalization(self):
        cell = Cell("T01", 8, 8, 16, "light", "heterogeneous",
                    "ResourceFit")
        values = {domain: [substream(cell, 17, domain, i).random()
                           for i in range(4)]
                  for domain in ("arrival", "demands", "duration_true",
                                 "duration_est")}
        self.assertEqual(len({tuple(v) for v in values.values()}), 4)
        self.assertNotEqual(values["arrival"][0], values["arrival"][1])
        self.assertEqual(canonical({"b": 2, "a": 1}), b'{"a":1,"b":2}')
        self.assertEqual(sha256(b"abc"), hashlib.sha256(b"abc").hexdigest())
        self.assertGreaterEqual(exp_gap(cell, 17, 0, 1.0), 0)

    def test_fail_closed_invalid_inputs(self):
        cell = Cell("T01", 2, 8, 16, "light", "bursty", "ResourceFit")
        for seed in (-1, 1.0, True):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                make_jobs_v2(cell, seed)
        with self.assertRaises(ValueError):
            Cell("BAD/PATH", 2, 8, 16, "light", "uniform", "ResourceFit")
        with self.assertRaises(ValueError):
            Cell("T01", 2, 0, 16, "light", "uniform", "ResourceFit")
        with self.assertRaises(ValueError):
            Cell("T01", 2, 8, 16, "unknown", "uniform", "ResourceFit")
        with self.assertRaises(ValueError):
            substream(cell, 1, "engine", 0)
        with self.assertRaises(ValueError):
            exp_gap(cell, 1, 0, 0.0)
        with self.assertRaises(ValueError):
            a_seeds(0)


if __name__ == "__main__":
    unittest.main()
