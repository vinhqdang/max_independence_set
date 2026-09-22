#!/usr/bin/env python3
"""Collects solution-quality-over-time traces, for the convergence figures.

Our solver writes them directly; NuMVC and FastVC report every improvement on
stdout and are parsed. Traces are stored as CSV with one row per improvement so
the plotting script stays independent of how each solver reports.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.environ.get("MIS_BASELINE_DIR", os.path.dirname(ROOT))


def run(cmd, timeout, cwd=None):
    t0 = time.perf_counter()
    try:
        r = subprocess.run(cmd, timeout=timeout, capture_output=True, text=True, cwd=cwd)
        return r, time.perf_counter() - t0
    except subprocess.TimeoutExpired:
        return None, time.perf_counter() - t0


def trace_cascade(path, tl, seed, tmp):
    tf = os.path.join(tmp, "cascade.trace")
    run([os.path.join(ROOT, "build", "cascade"), path, "--time-limit", "%g" % tl,
         "--seed", str(seed), "--trace", tf, "--lns-free", "4"], timeout=tl + 900)
    out = []
    if os.path.exists(tf):
        for line in open(tf):
            p = line.split()
            if len(p) == 2:
                out.append((float(p[0]), int(p[1])))
    return out


def trace_libmvc(solver, prepared, n, tl):
    """LibMVC prints 'Better MVC found.\tSize: S\tTime: Tms' for each improvement."""
    r, _ = run([os.path.join(EXT, "libmvc", solver), prepared + ".dimacs", "0", "%d" % int(tl)],
               timeout=tl + 900)
    out = []
    if r is None:
        return out
    for m in re.finditer(r"Size:\s*(\d+)\s*Time:\s*(\d+)ms", r.stdout):
        cover, ms = int(m.group(1)), int(m.group(2))
        out.append((ms / 1000.0, n - cover))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", default="/home/user/data/instances/catalogue.json")
    ap.add_argument("--instances", required=True)
    ap.add_argument("--time-limit", type=float, default=60.0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "traces.csv"))
    ap.add_argument("--tmp", default="/tmp/mis_traces")
    args = ap.parse_args()

    os.makedirs(args.tmp, exist_ok=True)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    cat = json.load(open(args.catalogue))
    root = os.path.dirname(os.path.abspath(args.catalogue))

    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["instance", "solver", "seconds", "size"])
        for name in args.instances.split(","):
            e = cat[name]
            prepared = os.path.join(root, "prepared", name)
            series = {"cascade": trace_cascade(e["path"], args.time_limit, args.seed, args.tmp)}
            for s in ("numvc", "fastvc"):
                series[s] = trace_libmvc(s, prepared, e["n"], args.time_limit)
            for solver, pts in series.items():
                for sec, size in pts:
                    w.writerow([name, solver, "%.4f" % sec, size])
                print("%-16s %-8s %4d points" % (name, solver, len(pts)), flush=True)
            f.flush()


if __name__ == "__main__":
    main()
