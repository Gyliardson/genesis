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