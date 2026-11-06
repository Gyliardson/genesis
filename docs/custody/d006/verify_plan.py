"""Verificador independente do plano A. Apenas metadados, nenhum job ou engine."""
import hashlib
import json
from pathlib import Path
import sys

HASH = "77934cf30e3937a9f339f3f6cc4144b9fa67ae2531c0185a8565acd5d0e789ba"
HEAD = "0399e842722e9bffe3063308e622830816744dc3"
TREE = "e692edb46a4fd7e0689c83e621c8b1346d4f3fe7"
ROWS = (
    ("A01", 100, 1, 1, "light", "uniform", "FCFSScanningPolicy"),
    ("A02", 100, 8, 16, "saturated", "bursty", "ResourceFit"),
    ("A03", 1000, 1, 1, "light", "heterogeneous", "ResourceFit"),
    ("A04", 1000, 8, 16, "saturated", "uniform", "FCFSScanningPolicy"),
    ("A05", 10000, 1, 1, "saturated", "uniform", "ResourceFit"),
    ("A06", 10000, 8, 16, "light", "heterogeneous", "FCFSScanningPolicy"),
    ("A07", 100000, 1, 1, "light", "bursty", "FCFSScanningPolicy"),
    ("A08", 100000, 8, 16, "saturated", "heterogeneous", "ResourceFit"),
)

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")

def pairs_unique(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError("duplicate JSON key")
        d[k] = v
    return d

def parse(raw):
    def reject_constant(v):
        raise ValueError("non-JSON constant")
    value = json.loads(raw, object_pairs_hook=pairs_unique, parse_constant=reject_constant)
    if canonical(value) != raw:
        raise ValueError("noncanonical JSON")
    return value

def expected_plan():
    slots = []
    for i, (id_, n, cpu, mem, load, family, policy) in enumerate(ROWS, 1):
        for offset in (11, 29):
            seed = 710000 + 100*i + offset
            slots.append({"cell":{"id":id_,"n":n,"cpu":cpu,"memory":mem,
                                   "load":load,"family":family,"policy":policy},
                          "file": f"{id_}_{seed}.json", "workload_seed": seed,
                          "order_seed":820000 + 100*i + offset, "policy_seed":93011})
    return {"schema":"D006_ExpectedFreezePlan_v1","slots":slots}

def verify(plan, lock):
    if len(plan) != 3305 or hashlib.sha256(plan).hexdigest() != HASH:
        raise ValueError("plan byte count / hash mismatch")
    if plan != canonical(expected_plan()) or parse(plan) != expected_plan():
        raise ValueError("plan descriptor mismatch")
    rec = parse(lock)
    if rec.get("schema") != "D006_A_SoloCustodyLock_v1":
        raise ValueError("lock schema")
    if rec.get("plan") != {"schema":"D006_ExpectedFreezePlan_v1","sha256":HASH,
                            "bytes":3305,"slots":16,"file":"expected_plan_A_v1.json"}:
        raise ValueError("locked plan identity")
    code = rec.get("code", {})
    if code.get("head") != HEAD or code.get("tree") != TREE or code.get("repository") != "Gyliardson/genesis":
        raise ValueError("locked generator code identity")
    if rec.get("authority",{}).get("freeze_authorized") is not False or rec.get("authority",{}).get("s1_authorized") is not False:
        raise ValueError("unapproved execution in lock")
    if rec.get("custody",{}).get("holdout_confidential") is not False:
        raise ValueError("public holdout falsely marked confidential")
    if rec.get("custody",{}).get("mode") != "single_operator_git_hosted_commit":
        raise ValueError("unexpected custody mode")
    return True

def main():
    root = Path(__file__).resolve().parent
    plan = (root/"expected_plan_A_v1.json").read_bytes()
    lock = (root/"lock.json").read_bytes()
    verify(plan, lock)
    if "--self-test" in sys.argv:
        altered = [
            (plan+b"\n", lock),
            (plan.replace(b'"order_seed":820111', b'"order_seed":820111.0', 1),lock),
            (plan.replace(b'"policy_seed":93011', b'"policy_seed":true', 1),lock),
            (plan.replace(b'"workload_seed":710111', b'"workload_seed":710112', 1),lock),
            (plan,lock.replace(b'"freeze_authorized":false',b'"freeze_authorized":true',1)),
            (plan,lock.replace(HEAD.encode(),b"0"*40,1))
        ]
        for ap, al in altered:
            if ap == plan and al == lock:
                raise AssertionError("mutation not applied")
            try:
                verify(ap, al)
            except (ValueError, TypeError, KeyError):
                continue
            raise AssertionError("mutation bypass")
        print("PASS: 1 positive + 6 negative fixtures; no workloads")
    print("PLAN_OK sha256="+HASH+" slots=16; FREEZE_NOT_AUTHORIZED")

if __name__ == "__main__":
    main()
