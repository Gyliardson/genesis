# D-006 — D006_Exogenous_v2 (prospective, NOT RATIFIED)

This is a **candidate implementation** of the S0 v2 proposal in [Issue #5 comment 6668170998](https://github.com/Gyliardson/genesis/issues/5#issuecomment-6668170998). It is NOT the original pre-registration, does NOT supersede v1, and MUST NOT be pooled with the v1 pilot. No engine benchmark, runtime workflow, main/core/PR26 edits, S1 authorization, or selection of SimPy/custom is included.

Source: `exogenous_v2.py`. Non-measurement tests: `test_exogenous_v2.py`. The eight A cells are **screening only** (8/96 configurations, 62/66 pair levels; not inferential coverage or 96-cell generalization). Workload unit is one cell × seed, not technical repeats.

## Generator contract

- Jobs: J000000..J{N−1}; integer ticks; each job is exogenous, `JobSpecPrivate`; no job exceeds capacity. Oversize tests remain separate negative strata.
- U: CPU=MEM=1, true duration=2, public estimate=2. Only arrival randomness changes across U seeds; duration truth is intentionally public through the constant-family design.
- H: independent demands sampled uniformly from integer [1,CPUCap] × [1,MEMCap], true duration [1,8], independent *uninformative* estimate [1,8].
- B: same resource demands, true duration [1,5], independent estimate [1,5], bursts of 16 arrivals together.
- `rho` target: light=0.4, saturated=1.2; `b=max(E[CPU×duration]/CPUCap, E[MEM×duration]/MEMCap)`; `lambda=rho/b`. U/H interarrival gaps: Exp(rate=lambda); B gaps between 16-job groups: Exp(rate=lambda/16). First arrival accumulates the first gap, then arrival ticks are `floor(cumulative_gaps)`. This discretization yields ties; load labels do NOT guarantee observed utilization or steady-state saturation.
- Every random draw is seeded by SHA256 of canonical UTF-8 JSON for (schema, full cell, workload_seed, domain, item index), digested as an unsigned big-endian integer. Domains are arrival, demands, duration_true, duration_est. The algorithm is CPython `random.Random` (MT19937), `random.random`, `randint` and `math.log1p`. Pin **CPython 3.11.18** before freezing reproducible bytes.
- `policy_seed=93011` and order seeds `820000+100*i+(11 or 29)` remain independent of exogenous generation; a separate scheduler, not this module, should generate balanced AB/BA order. Holdout `910000..919999` is reserved and never generated.
- A workload seeds: `710000+100*i+(11 or 29)`, i=1..8. S1 seed namespace `810011/811011/812011` is documented but **no S1 input generation is dispatched**.

## Prospective freeze (not performed by CI)

Inspect and independently review this implementation and the final head first. Only then, if authorized for exogenous-input generation, run in an isolated CPython 3.11.18 environment:

```bash
PYTHONPATH=src:benchmarks/d006 python benchmarks/d006/exogenous_v2.py --plan
PYTHONPATH=src:benchmarks/d006 python benchmarks/d006/exogenous_v2.py --freeze-a /safe/new/directory
```

The freeze refuses any existing destination and writes canonical JSON per cell × seed (16 payloads), each payload SHA256, **jobs-only SHA256** (excluding envelope/seed), realized offered work over [0, last_arrival_tick+1), source hash, explicit Python version and manifest SHA256. A partial/interrupted freeze with missing manifest/checksum is INVALID, not an experimental result. Verify every byte by readback and independent regeneration before considering immutable freeze deposited.

The data contains true job durations for the simulator **only**. Runtime policies in Python remain trusted in-process code, not a secrecy sandbox. No cutoff is applied in this complete-workload v2 screening generator; fixed-H remains separate D-020.

## Scientific and execution gates

This module never invokes `simulate`, `simpy_adapter`, GitHub Actions or subprocess measurements. Tests exercise analytic offered-load derivation, deterministic replay, effective U seed diversity on jobs bytes, burst/tie invariants, domain separation, invalid inputs and absence of `estimated=true+1` in H/B. Statistical PRNG independence cannot be proven from hash-domain separation or a finite test suite.

**Still required:** exact-head independent code/oracle review; physical trace generation + manifest SHA256 deposition before any A timing; explicit human adjudication D1/D3/D5; independent S1 one-shot/budget/artifact safety gates; specific authorization D6. No A or S1 benchmarks are authorized here.
