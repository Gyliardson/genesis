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
- `policy_seed=93011` and order seeds `820000+100*i+(11 or 29)` remain independent of exogenous generation; a separate scheduler, not this module, should generate balanced AB/BA order. Holdout `910000..919999` is a **public, reserved namespace**, not a confidential blinded test set. `make_jobs_v2`, `substream` and freeze-plan validation reject those seeds. A/S1/order/policy/pilot seed partitions are checked for collisions. This prevents accidental use by these code paths, **not deliberate use by an independent actor**. Until a prospective human decision specifies a trustworthy independent steward, late seed selection, split/access logs and test-use policy, no final hidden-holdout claim is justified. GitHub visibility is public and the seeds plus algorithm are reproducible by anyone.
- A workload seeds: `710000+100*i+(11 or 29)`, i=1..8. S1 seed namespace `810011/811011/812011` is documented but **no S1 input generation is dispatched**.

## Prospective freeze (not performed by CI)

Inspect and independently review this implementation and the final head first. Only then, if authorized for exogenous-input generation, run in an isolated CPython 3.11.18 environment:

```bash
PYTHONPATH=src:benchmarks/d006 python benchmarks/d006/exogenous_v2.py --plan
# The following command is NOT authorized by this PR; do not run it in CI.
PYTHONPATH=src:benchmarks/d006 python benchmarks/d006/exogenous_v2.py --freeze-a /safe/new/directory
PYTHONPATH=src:benchmarks/d006 python benchmarks/d006/exogenous_v2.py --verify-freeze /safe/new/directory
```

The freeze refuses existing destinations. It requires **CPython 3.11.18 on Linux** and a Git checkout with clean, tracked determinant files. It records Git commit and tree IDs, Git blob identities and SHA256 for generator, freeze module, Core, project config, pinned CI requirements and this contract, alongside runtime build/platform, canonical serialization/schema, PRNG details, per-payload and jobs-only SHA256, complete envelope/counts, realized offered work and deterministic arrival ties/burst diagnostics.

All files are first written with exclusive creation to a unique sibling staging directory, fsynced, and **each file is independently read back**. The manifest and its checksum are verified; every payload is parsed and checked against recorded fields, counts, job hashes and diagnostics. The generator re-attests the source files before **atomic Linux `renameat2(RENAME_NOREPLACE)` publication**, with destination collision denied even during a race. An incomplete staging directory is removed after failure. The publicly visible destination appears only after validation, not while partially writing. An interruption or error does not confer approval: integrity-complete means only `INTEGRITY_COMPLETE_NOT_REVIEWED_NOT_AUTHORIZED`.

Post-freeze verification uses `--verify-freeze /path`, which re-checks every byte, source Git tree and runtime identity, and fails on any mismatch. This is not an independent scientific sign-off or authorization to measure. A crash after directory rename but before caller confirmation must be reconciled by readback, never counted as automatically approved. No published inputs/hashes currently exist; **neither CI nor this PR freezes A**.

The data contains true job durations for the simulator **only**. Runtime policies in Python remain trusted in-process code, not a secrecy sandbox. No cutoff is applied in this complete-workload v2 screening generator; fixed-H remains separate D-020.

## Scientific and execution gates

This module never invokes `simulate`, `simpy_adapter`, GitHub Actions or subprocess measurements. Tests exercise analytic offered-load derivation, deterministic replay, effective U seed diversity on jobs bytes, burst/tie invariants, domain separation, invalid inputs and absence of `estimated=true+1` in H/B. The independent literal test module fixes UTF-8 JSON bytes, SHA256, unsigned big-endian seed, MT19937 draws, exponential gaps, floor/tie behavior, partial bursts and jobs-only/payload hashes for only tiny synthetic T cells. Negative mutations distinguish incorrect endian, transformations, serialization, ordering, and data. Mini-freeze fault injection covers overwritten destinations, race, mid-write failures, missing checksum, readback corruption, altered payload, bad Git tree and incompatible runtimes, without generating the 16 A workloads. Statistical PRNG independence cannot be proven from hash-domain separation or a finite test suite.

**Still required:** exact-head independent code/oracle review; physical trace generation + manifest SHA256 deposition before any A timing; explicit human adjudication D1/D3/D5; independent S1 one-shot/budget/artifact safety gates; specific authorization D6. No A or S1 benchmarks are authorized here.

## Boundaries carried forward from review R27-07/08

Python policies run in-process and are **not sandboxed**: hiding `actual_duration_ticks` from `ObservationV0` does not enforce adversarial secrecy. Exact AB/BA engine-input equality and cross-engine parity require a separate reviewed harness. N=100,000 memory/RSS and possible quadratic simulator work remain **UNVERIFIED**, with no benchmark or S1 preflight authorized here. This review-ready repair does not ratify D1–D6, choose a scheduler engine or convert eight screening cells into evidence for the 96-cell population.
