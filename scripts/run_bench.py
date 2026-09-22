#!/usr/bin/env python3
"""Benchmark harness.

Runs every solver on every instance under a common wall-clock budget, verifies
the returned set independently, and appends one row per run to a CSV.

Solution sizes are only recorded when they come with a solution file that the
verifier accepts; solvers that print a size without emitting the set are marked
verified=0 so the distinction stays visible in the results.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.environ.get("MIS_BASELINE_DIR",
                     "/tmp/claude-0/-home-user-max-independence-set/"
                     "ab0fd628-37f5-5a8a-bda6-c8eaa0ba89dd/scratchpad")
VERIFY = os.path.join(ROOT, "build", "mis-verify")

BIN = {
    "redumis": os.path.join(EXT, "kamis", "build", "redumis"),
    "online_mis": os.path.join(EXT, "kamis", "build", "online_mis"),
    "chang": os.path.join(EXT, "Near-Maximum-Independent-Set", "mis"),
    "vcsolver": os.path.join(EXT, "vertex_cover"),
    "pace": os.path.join(EXT, "pace-2019", "optimized", "vc_solver"),
    "cascade": os.path.join(ROOT, "build", "cascade"),
}

# Solver identifier -> (paper, whether it is an exact solver)
SOLVERS = {
    "redumis":     ("Lamm et al., J. Heuristics 2017", False),
    "online_mis":  ("Dahlum et al., SEA 2016", False),
    "nearlinear":  ("Chang et al., SIGMOD 2017", False),
    "lineartime":  ("Chang et al., SIGMOD 2017", False),
    "vcsolver":    ("Akiba & Iwata, TCS 2016", True),
    "pace":        ("Hespe et al., PACE 2019 winner", True),
    "cascade":     ("this work", False),
    "cascade-nolns":  ("this work, no neighbourhood moves", False),
    "cascade-nolp":   ("this work, no LP reduction", False),
    "cascade-nopert": ("this work, no perturbation or restarts", False),
    "cascade-dive":   ("this work, decision-space moves instead", False),
    "cascade-exact": ("this work", True),
    "highs":       ("HiGHS MIP", True),
}


def run(cmd, timeout, stdin=None, stdout=None, cwd=None):
    t0 = time.perf_counter()
    try:
        res = subprocess.run(cmd, timeout=timeout, capture_output=(stdout is None),
                             stdin=stdin, stdout=stdout, text=True, cwd=cwd)
        return time.perf_counter() - t0, res, False
    except subprocess.TimeoutExpired:
        return time.perf_counter() - t0, None, True


def verify(instance_path, sol_path, extra=()):
    if not os.path.exists(sol_path) or os.path.getsize(sol_path) == 0:
        return None, "missing solution file"
    res = subprocess.run([VERIFY, instance_path, sol_path] + list(extra),
                         capture_output=True, text=True)
    out = res.stdout.strip()
    if out.startswith("VALID"):
        m = re.search(r"size=(\d+)", out)
        return int(m.group(1)), "maximal=yes" if "maximal=yes" in out else "maximal=no"
    return None, out or res.stderr.strip()


def invoke(solver, inst, tl, seed, tmp):
    """Returns (size, elapsed, verified, note)."""
    name, path, prepared = inst["name"], inst["path"], inst["prepared"]
    sol = os.path.join(tmp, "%s.%s.%d.sol" % (name, solver, seed))

    if solver in ("redumis", "online_mis"):
        metis = prepared + ".graph"
        cmd = [BIN[solver], metis, "--output=" + sol, "--seed=%d" % seed,
               "--time_limit=%g" % tl]
        if solver == "redumis":
            cmd.append("--kernelization=full")
        el, res, to = run(cmd, timeout=tl + 600)
        size, note = verify(path, sol)
        return size, el, size is not None, note + (" TIMEOUT" if to else "")

    if solver in ("nearlinear", "lineartime"):
        alg = "NearLinear" if solver == "nearlinear" else "LinearTime"
        el, res, to = run([BIN["chang"], alg, prepared], timeout=tl + 600)
        if to or res is None:
            return None, el, False, "TIMEOUT"
        m = re.search(r"MIS:\s*(\d+)", res.stdout)
        k = re.search(r"kernal \(\|V\|,\|E\|\): \((\d+),(\d+)\)", res.stdout)
        note = "kernel=%s" % (k.group(1) if k else "?")
        # The reference implementation reports a size but never writes the set,
        # so this number cannot be verified here.
        return (int(m.group(1)) if m else None), el, False, note

    if solver == "vcsolver":
        # Fed the compacted edge list so the ids it prints match the verifier's.
        el, res, to = run(["java", "-Xmx12g", "-cp", "bin", "Main", prepared + ".el", "-p"],
                          timeout=tl, cwd=BIN["vcsolver"])
        if to or res is None or res.returncode != 0:
            return None, el, False, "TIMEOUT" if to else "error"
        lines = [l for l in res.stdout.split("\n") if l.strip()]
        with open(sol, "w") as f:
            f.write("\n".join(lines[1:]))
        size, note = verify(path, sol, extra=["--cover"])
        return size, el, size is not None, "exact " + note

    if solver == "pace":
        gr = prepared + ".gr"
        if not os.path.exists(gr):
            return None, 0.0, False, "no PACE file (instance too large)"
        with open(gr) as fin, open(sol, "w") as fout:
            el, res, to = run([BIN["pace"]], timeout=tl, stdin=fin, stdout=fout)
        if to:
            return None, el, False, "TIMEOUT"
        size, note = verify(path, sol)
        return size, el, size is not None, "exact " + note

    if solver == "highs":
        ilp = os.path.join(ROOT, "tools", "ilp_baseline.py")
        el, res, to = run(["python3", ilp, path, "--output", sol,
                           "--time-limit", "%g" % tl], timeout=tl + 300)
        size, note = verify(path, sol)
        opt = res is not None and "optimal=1" in (res.stdout or "")
        return size, el, size is not None, note + (" proved_optimal" if opt else "")

    if solver.startswith("cascade"):
        cmd = [BIN["cascade"], path, "--output", sol, "--seed", str(seed),
               "--time-limit", "%g" % tl, "--lns-free", "4"]
        if solver == "cascade-exact":
            cmd.append("--exact")
        elif solver == "cascade-nolns":
            cmd.append("--no-lns")
        elif solver == "cascade-nolp":
            cmd.append("--no-lp")
        elif solver == "cascade-nopert":
            cmd += ["--no-perturb"]
        elif solver == "cascade-dive":
            cmd += ["--no-lns", "--dive-moves"]
        el, res, to = run(cmd, timeout=tl + 600)
        size, note = verify(path, sol)
        proved = res is not None and "proved_optimal=1" in (res.stdout or "")
        return size, el, size is not None, note + (" proved_optimal" if proved else "")

    raise SystemExit("unknown solver " + solver)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", default="/home/user/data/instances/catalogue.json")
    ap.add_argument("--solvers", default="redumis,online_mis,nearlinear,cascade")
    ap.add_argument("--instances", default="all")
    ap.add_argument("--family", default=None)
    ap.add_argument("--max-n", type=int, default=None)
    ap.add_argument("--time-limit", type=float, default=60.0)
    ap.add_argument("--seeds", default="1")
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "raw.csv"))
    ap.add_argument("--tmp", default="/tmp/mis_runs")
    args = ap.parse_args()

    os.makedirs(args.tmp, exist_ok=True)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.catalogue) as f:
        cat = json.load(f)

    names = sorted(cat) if args.instances == "all" else args.instances.split(",")
    insts = []
    for n in names:
        if n not in cat:
            print("unknown instance", n, file=sys.stderr)
            continue
        e = cat[n]
        if args.family and e["family"] != args.family:
            continue
        if args.max_n and e["n"] > args.max_n:
            continue
        # The prepared files always live next to the catalogue, not next to the
        # instance: complemented instances point into prepared/ themselves.
        root = os.path.dirname(os.path.abspath(args.catalogue))
        insts.append({"name": n, "path": e["path"], "family": e["family"],
                      "n": e["n"], "m": e["m"],
                      "prepared": os.path.join(root, "prepared", n)})

    new = not os.path.exists(args.out)
    with open(args.out, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["instance", "family", "n", "m", "solver", "seed",
                        "time_limit", "size", "seconds", "verified", "note"])
        for inst in insts:
            for solver in args.solvers.split(","):
                for seed in [int(s) for s in args.seeds.split(",")]:
                    size, el, ver, note = invoke(solver, inst, args.time_limit, seed, args.tmp)
                    w.writerow([inst["name"], inst["family"], inst["n"], inst["m"],
                                solver, seed, args.time_limit,
                                size if size is not None else "",
                                "%.3f" % el, int(ver), note])
                    f.flush()
                    print("%-20s %-14s seed=%d  size=%-9s %7.2fs  %s"
                          % (inst["name"], solver, seed,
                             size if size is not None else "-", el, note), flush=True)


if __name__ == "__main__":
    sys.exit(main())
