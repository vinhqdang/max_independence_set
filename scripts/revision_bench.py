#!/usr/bin/env python3
"""Experiments added in the revision: kernel statistics, whole-input exact
solving, ablation with process counters, parameter sweep over the initial
release size, and independent Delaunay graphs.  Cascade only; every run is a
single-threaded process, three run concurrently on a 4-core machine.

Output: one JSON object per run in results/revision.jsonl.
"""
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "build", "cascade")
D = os.path.expanduser("~/data")
OUT = os.path.join(ROOT, "results", "revision.jsonl")

SNAP = ["roadNet-PA", "roadNet-CA", "ca-AstroPh", "ca-CondMat", "email-Enron", "com-dblp",
        "com-amazon", "com-youtube", "soc-pokec-relationships", "as-skitter", "wiki-Talk",
        "com-lj", "web-Stanford", "web-BerkStan"]


def path(name):
    if name in SNAP:
        return f"{D}/inst/{name}.txt"
    if name.startswith("n"):  # DIMACS10: n16
        return f"{D}/dimacs10/delaunay_{name}/delaunay_{name}.mtx"
    s, base = name.split("/")  # s3/del16
    return f"{D}/geo/{s}/{base}.txt"


def run(job):
    group, inst, extra, tl, seed = job
    cmd = [BIN, path(inst), "--time-limit", str(tl), "--seed", str(seed)] + extra
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    rec = {"group": group, "instance": inst, "args": " ".join(extra), "seed": seed,
           "limit": tl, "wall": round(time.time() - t0, 3)}
    for tok in p.stdout.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            try:
                rec[k] = float(v) if "." in v else int(v)
            except ValueError:
                rec[k] = v
    return rec


def jobs(which):
    J = []
    geo1 = ["s1/del16", "s1/del18", "s1/del20", "s1/rgg16", "s1/rgg18"]
    if "kernel" in which:
        for i in SNAP + geo1:
            J.append(("kernel_capped", i, ["--kernel-only", "--kernel-capped"], 60, 1))
            J.append(("kernel_full", i, ["--kernel-only", "--kernel-share", "1.0"], 300, 1))
    if "exact" in which:
        for i in SNAP + geo1:
            J.append(("exact", i, ["--exact"], 120, 1))
    if "ablation" in which:
        inst = ["s1/del16", "s1/del18", "s1/rgg16", "roadNet-PA", "web-Stanford", "com-amazon"]
        var = {"full": [], "heuristic": ["--lns-heuristic"], "noreduce": ["--lns-no-reduce"],
               "nolns": ["--no-lns"]}
        for s in (1, 2, 3):
            for i in inst:
                for v, a in var.items():
                    J.append(("ablation_" + v, i, a, 60, s))
    if "delaunay" in which:
        for s in (1, 2, 3):
            for i in ["s1/del16", "s2/del16", "s3/del16", "s4/del16", "s5/del16", "s6/del16",
                      "s1/del18", "s2/del18", "s3/del18", "s4/del18", "s5/del18", "s6/del18",
                      "n16", "n18", "n20"]:
                if s == 3 and i in ("s4/del16", "s5/del16", "s6/del16", "s4/del18", "s5/del18", "s6/del18"):
                    continue
                J.append(("delaunay", i, [], 60, s))
    if "sweep" in which:
        for i in ["s1/del18", "s1/rgg16", "web-Stanford", "roadNet-PA"]:
            for k in (1, 4, 16, 64, 256, 1024):
                J.append(("sweep_k", i, ["--lns-free", str(k)], 60, 1))
    return J


if __name__ == "__main__":
    which = sys.argv[1].split(",")
    J = jobs(which)
    done = set()
    if os.path.exists(OUT):
        for l in open(OUT):
            r = json.loads(l)
            done.add((r["group"], r["instance"], r["args"], r["seed"]))
    J = [j for j in J if (j[0], j[1], " ".join(j[2]), j[4]) not in done]
    print(len(J), "jobs", flush=True)
    with cf.ThreadPoolExecutor(3) as ex, open(OUT, "a") as f:
        for r in ex.map(run, J):
            f.write(json.dumps(r) + "\n")
            f.flush()
