"""Mutate the adapter's real COMPLETE dispatch rather than only an event snapshot."""

import inspect
import unittest
from builtins import sorted as original_sorted
from unittest.mock import patch

from genesis.simulation.core import Capacity, FCFSScanningPolicy
from oracle_tests import CASES, expected_result, jobs_for
from simpy_adapter_benchmark import simpy_adapter


class DispatchMutation(unittest.TestCase):
    def test_wrong_completion_dispatch_is_caught(self):
        scenario = CASES["MULTI_TIE"]
        jobs = jobs_for(scenario[0])
        capacity = Capacity(*scenario[1])
        expected = expected_result(scenario)
        self.assertEqual(simpy_adapter(jobs, capacity, FCFSScanningPolicy()), expected)
        intercepted = []

        def wrong_complete_order(iterable, *args, **kwargs):
            frame = inspect.currentframe().f_back
            if (frame is not None and frame.f_code.co_name == "simpy_adapter"
                    and iterable is frame.f_locals.get("finished") and len(iterable) > 1):
                intercepted.append(tuple(iterable))
                return list(reversed(original_sorted(iterable, *args, **kwargs)))
            return original_sorted(iterable, *args, **kwargs)

        with patch("builtins.sorted", side_effect=wrong_complete_order):
            mutant = simpy_adapter(jobs, capacity, FCFSScanningPolicy())
        self.assertTrue(intercepted, "mutation must reach the actual COMPLETE dispatch")
        self.assertEqual((mutant.events[5].kind, mutant.events[5].job_id), ("COMPLETE", "B"))
        self.assertNotEqual(mutant, expected)
        with self.assertRaises(AssertionError):
            self.assertEqual(mutant, expected)


if __name__ == "__main__":
    unittest.main()
