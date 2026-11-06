"""Contrato prospectivo de custódia D006: somente metadata, nenhum workload."""
import subprocess
import sys
from pathlib import Path


def test_d006_plan_custody_readback_and_adversarial_mutants():
    root = Path(__file__).resolve().parents[1]
    script = root / "docs/custody/d006/verify_plan.py"
    result = subprocess.run(
        [sys.executable, str(script), "--self-test"],
        cwd=root, capture_output=True, text=True, timeout=15, check=False,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "1 positive + 9 negative" in result.stdout
    assert "FREEZE_NOT_AUTHORIZED" in result.stdout
