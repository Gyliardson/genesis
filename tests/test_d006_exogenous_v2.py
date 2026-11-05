"""Collect research-only generator regressions in default pytest CI."""
from importlib import import_module
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks" / "d006"))
TestExogenousV2 = import_module("test_exogenous_v2").ExogenousV2Tests
