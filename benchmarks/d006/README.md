# D-006: SimPy versus ActionA_v0 custom DES (research-only)

**Status:** OPEN / pilot exploratory, not an architectural decision. Base candidate: PR #25 `f39ed8a2cf10febc8affc0525c29e4a6a25b9be7`; maintained in an independent worktree/branch. No production import, lockfile, CI or core edits.

## Reproduction

Run in a distinct isolated Python environment with `simpy==4.1.2` (initial Codespace interpreter Python 3.14.2) and the GENESIS source on `PYTHONPATH`:

```sh
PYTHONPATH=src python benchmarks/d006/simpy_adapter_benchmark.py
PYTHONPATH=src python benchmarks/d006/simpy_adapter_benchmark.py --pilot
```

The first command compares full exact `SimulationResult`, including event order and post-event CPU/MEM, for 16 golden/policy combinations, 4 negative policies, and 64 fixed-seed generated workloads with replay, input permutations and fixed-H variants. This does **not** validate D-020/D-021 or untrusted Python policies.

`pilot_results.json` contains **72 exploratory raw timings**, 12 cells (N=100/1000 × uniform/heterogeneous/bursty × light/saturated at CPU=8 MEM=16), 3 repeats per engine, FCFS-scanning. The speed ratio is `median(SimPy time)/median(custom time)`, hence **>1 = custom faster** and **<1 = SimPy faster**. Data is illustrative only: lacks full N=10k/100k, capacity=(1,1), resource-fit performance, 5 warmups, 20 balanced AB/BA repetitions, isolated memory measurement, confidence intervals, and other preregistered scientific gates. Engine loop order is fixed custom→SimPy in this pilot, an order/confounding risk. `maxrss_kib_process` is a process-global high-water mark **not a comparable per-engine memory measurement**. Do not choose a framework based on this pilot.

The existing Core checks invariants via a per-event full scan of job states, yielding substantial Python-level cost. The adapter retains comparable per-event scan/check semantics but has a separate event-dispatch implementation. Benchmark results measure **these exact implementations**, not intrinsic SimPy versus optimal hand-written DES asymptotics. Any optimization should retain identical correctness fixtures and be evaluated at a new version/SHA.

## Scientific and engineering gates

Pre-registered protocol: https://github.com/Gyliardson/genesis/issues/5#issuecomment-6657670493. Full comparison must retain identical ActionA_v0 and exogenous traces and include equal semantics for error/censor conditions, workload-scale/stress distribution, CPU time/throughput/RSS/decision overhead, maintenance cost and uncertainty. Negative findings count. D-020 horizon and D-021 timeout remain separate open contracts. SimPy is MIT licensed and adds a runtime dependency; custom DES avoids it but assumes ongoing responsibility for correct event scheduling, tie phases, boundedness and invariant/property tests. This pilot does not quantify future maintenance hours.

No default branch merge, no real workloads, no `sell-docker`.

## Repair-26: independently specified correctness and reproducible replay

The literal table in `oracle_tests.py` contains five independently reasoned scenarios:
A (CPU integral 7, MEM integral 4), B (simultaneous COMPLETE before ARRIVE),
C (fixed-H censor; integral 3/3), HOL (first eligible scanning; integral 8/7)
and MULTI_TIE (two completions before two arrivals). The expected full ordered
events include per-event post-state allocations, all job outcomes, decision counts,
terminal reason and resource integrals. A deliberately re-ordered completion
trace is asserted to disagree with the literal oracle; this is a test-harness
mutation, **not** a mutated engine implementation. Invalid constructors, validation
type/message and adversarial action payloads are also covered. With SimPy
installed, the same tests assert both engines against the literal expectations;
without SimPy they test **only** the Core and must not be reported as adapter PASS.

Run outside production from a separate worktree, with clean Python **3.11**:

```sh
python3.11 -m venv /tmp/genesis-d006-py311
/tmp/genesis-d006-py311/bin/python -m pip install --require-hashes --no-deps -r benchmarks/d006/requirements-research.txt
/tmp/genesis-d006-py311/bin/python -c 'import sys, simpy; assert sys.version_info[:2] == (3,11); assert simpy.__version__ == "4.1.2"'
PYTHONPATH=src:benchmarks/d006 /tmp/genesis-d006-py311/bin/python -m unittest discover -s benchmarks/d006 -p oracle_tests.py -v
PYTHONPATH=src /tmp/genesis-d006-py311/bin/python benchmarks/d006/simpy_adapter_benchmark.py
```

Research-only SimPy wheel SHA256 is pinned in
`requirements-research.txt` (PyPI release metadata). Python, OS, kernel,
CPU model, RAM, interpreter/build/GC, worktree HEAD/base and hashed input
trace must be attached to a later actual execution log; these are **not**
asserted by the presence of this file. Core import and production dependencies
remain unchanged. To run without the research-only SimPy dependency,
`oracle_tests.py` works against the Core, but that is a reduced gate.

**Current scientific gate:** full adapter tests on Python 3.11 with the exact
remote HEAD, followed by a balanced AB/BA feasibility pilot. Existing
`pilot_results.json` is historical, remains explicitly exploratory and must
not be relabeled, overwritten or promoted into confirmatory evidence. The
pre-registered full 96-cell matrix requires a separate feasibility/budget
decision before execution; D-006, D-020 and D-021 remain OPEN.
