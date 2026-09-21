#!/usr/bin/env python3
"""Generates the geometric instance families (Delaunay triangulations and
random geometric graphs).  These are the families on which data reductions are
known to stall, so they are the core of the hard benchmark set."""
import argparse
import os
import sys

import numpy as np
from scipy.spatial import Delaunay, cKDTree


def delaunay_edges(n, seed):
    rng = np.random.default_rng(seed)
    pts = rng.random((n, 2))
    tri = Delaunay(pts)
    s = tri.simplices
    e = np.vstack([s[:, [0, 1]], s[:, [1, 2]], s[:, [0, 2]]])
    e = np.sort(e, axis=1)
    return np.unique(e, axis=0)


def rgg_edges(n, seed, avg_deg):
    # Radius chosen so that the expected degree matches avg_deg on the unit
    # square (boundary effects make the realised value slightly lower).
    rng = np.random.default_rng(seed)
    pts = rng.random((n, 2))
    r = np.sqrt(avg_deg / (np.pi * n))
    tree = cKDTree(pts)
    pairs = tree.query_pairs(r, output_type="ndarray")
    return np.unique(np.sort(pairs, axis=1), axis=0)


def write_edges(path, n, edges):
    with open(path, "w") as f:
        f.write("# n=%d m=%d\n" % (n, len(edges)))
        np.savetxt(f, edges, fmt="%d %d")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--scales", default="16,18,20", help="log2 vertex counts")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--avg-deg", type=float, default=8.0, help="target degree for rgg")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    for k in [int(x) for x in args.scales.split(",")]:
        n = 1 << k
        for family in ("del", "rgg"):
            path = os.path.join(args.out, "%s%d.txt" % (family, k))
            if os.path.exists(path):
                print("skip", path)
                continue
            edges = (delaunay_edges(n, args.seed) if family == "del"
                     else rgg_edges(n, args.seed, args.avg_deg))
            write_edges(path, n, edges)
            print("%s n=%d m=%d -> %s" % (family, n, len(edges), path), flush=True)


if __name__ == "__main__":
    sys.exit(main())
