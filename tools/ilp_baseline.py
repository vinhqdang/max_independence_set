#!/usr/bin/env python3
"""Integer-programming baseline.

Solves max sum_v x_v  s.t.  x_u + x_v <= 1 for every edge, x binary, with HiGHS.
Included as a reference point: Akiba & Iwata (TCS 2016) already showed that
branch-and-reduce dominates general-purpose MIP on these instances, so this is
expected to be competitive only on the smallest ones.
"""
import argparse
import sys
import time

import highspy
import numpy as np


def read_edges(path):
    n = 0
    edges = []
    with open(path) as f:
        first = True
        mtx = path.endswith(".mtx")
        for line in f:
            line = line.strip()
            if not line or line[0] in "#%c":
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            if mtx and first:
                first = False
                continue  # dimension line
            first = False
            u, v = int(parts[0]), int(parts[1])
            edges.append((u, v))
    ids = sorted({x for e in edges for x in e})
    remap = {x: i for i, x in enumerate(ids)}
    return len(ids), [(remap[u], remap[v]) for u, v in edges if u != v]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("graph")
    ap.add_argument("--output")
    ap.add_argument("--time-limit", type=float, default=60.0)
    ap.add_argument("--threads", type=int, default=1)
    args = ap.parse_args()

    t0 = time.perf_counter()
    n, edges = read_edges(args.graph)
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    h.setOptionValue("time_limit", args.time_limit)
    h.setOptionValue("threads", args.threads)

    inf = highspy.kHighsInf
    h.addVars(n, np.zeros(n), np.ones(n))
    h.changeColsIntegrality(n, np.arange(n, dtype=np.int32),
                            np.array([highspy.HighsVarType.kInteger] * n))
    # HiGHS minimises by default; maximise the cardinality.
    h.changeColsCost(n, np.arange(n, dtype=np.int32), -np.ones(n))
    starts = np.arange(0, 2 * len(edges), 2, dtype=np.int32)
    idx = np.array([v for e in edges for v in e], dtype=np.int32)
    vals = np.ones(2 * len(edges))
    h.addRows(len(edges), -inf * np.ones(len(edges)), np.ones(len(edges)),
              2 * len(edges), starts, idx, vals)

    h.run()
    status = h.getModelStatus()
    sol = h.getSolution()
    x = np.array(sol.col_value)
    chosen = (x > 0.5).astype(np.int8)
    elapsed = time.perf_counter() - t0
    optimal = str(h.modelStatusToString(status)) == "Optimal"
    print("n=%d m=%d size=%d time=%.3f status=%s optimal=%d"
          % (n, len(edges), int(chosen.sum()), elapsed,
             h.modelStatusToString(status), int(optimal)))
    if args.output:
        with open(args.output, "w") as f:
            f.write("\n".join(str(int(c)) for c in chosen) + "\n")


if __name__ == "__main__":
    sys.exit(main())
