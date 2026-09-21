#!/usr/bin/env python3
"""Unpacks the raw benchmark downloads and converts every instance into the
input formats the baseline solvers need.

Layout produced under --out:
    <name>.txt            normalised edge list (input to our solver)
    prepared/<name>.graph METIS   (redumis, online_mis)
    prepared/<name>/      binary  (Chang et al. reducing-peeling)
    prepared/<name>.gr    PACE    (WeGotYouCovered vc_solver)
"""
import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys

CONVERT = os.path.join(os.path.dirname(__file__), "..", "build", "mis-convert")
# PACE format is only produced for instances an exact solver can plausibly read.
PACE_EDGE_LIMIT = 8_000_000


def gunzip(src, dst):
    if os.path.exists(dst):
        return
    with gzip.open(src, "rb") as f_in, open(dst, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out, 1 << 22)


def parse_stats(line):
    out = {}
    for tok in line.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = float(v) if "." in v else int(v)
    return out


def convert(name, src, outdir, want_pace, complement=False):
    prepared = os.path.join(outdir, "prepared")
    os.makedirs(prepared, exist_ok=True)
    cmd = [CONVERT, src,
           "--metis", os.path.join(prepared, name + ".graph"),
           "--chang", os.path.join(prepared, name),
           "--edgelist", os.path.join(prepared, name + ".el"),
           "--stats"]
    if complement:
        cmd.append("--complement")
    if want_pace:
        cmd += ["--pace", os.path.join(prepared, name + ".gr")]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("  FAILED %s: %s" % (name, res.stderr.strip()), flush=True)
        return None
    return parse_stats(res.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="/home/user/data/raw")
    ap.add_argument("--geometric", default="/home/user/data/geometric")
    ap.add_argument("--bhoslib", default="/home/user/data/bhoslib")
    ap.add_argument("--out", default="/home/user/data/instances")
    ap.add_argument("--only", default=None, help="comma separated instance names")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    only = set(args.only.split(",")) if args.only else None
    catalogue = {}

    sources = []
    if os.path.isdir(args.raw):
        for fn in sorted(os.listdir(args.raw)):
            if not fn.endswith(".txt.gz"):
                continue
            name = fn[:-7].replace(".ungraph", "")
            sources.append((name, os.path.join(args.raw, fn), "gz",
                            "road" if name.startswith("road") else
                            "web" if name.startswith("web") else "social"))
    if os.path.isdir(args.geometric):
        for fn in sorted(os.listdir(args.geometric)):
            if fn.endswith(".txt"):
                sources.append((fn[:-4], os.path.join(args.geometric, fn), "plain", "geometric"))
    if os.path.isdir(args.bhoslib):
        for d in sorted(os.listdir(args.bhoslib)):
            p = os.path.join(args.bhoslib, d, d + ".mtx")
            if os.path.exists(p):
                sources.append((d, p, "plain", "bhoslib"))

    for name, src, kind, family in sources:
        if only and name not in only:
            continue
        # The extension selects the reader, so it must survive the copy.
        ext = ".txt" if kind == "gz" else os.path.splitext(src)[1]
        target = os.path.join(args.out, name + ext)
        if kind == "gz":
            gunzip(src, target)
        elif os.path.abspath(src) != os.path.abspath(target):
            if not os.path.exists(target):
                shutil.copy(src, target)
        size_hint = os.path.getsize(target)
        # BHOSLIB instances are distributed in clique form; MIS lives in the
        # complement, and the complement becomes the instance we benchmark on.
        complement = family == "bhoslib"
        stats = convert(name, target, args.out, want_pace=size_hint < 120 << 20,
                        complement=complement)
        if complement:
            target = os.path.join(args.out, "prepared", name + ".el")
        if stats is None:
            continue
        stats["family"] = family
        stats["path"] = target
        catalogue[name] = stats
        print("%-28s n=%-10d m=%-11d avg_deg=%-7.2f [%s]"
              % (name, stats["n"], stats["m"], stats["avg_deg"], family), flush=True)

    path = os.path.join(args.out, "catalogue.json")
    existing = {}
    if os.path.exists(path):
        with open(path) as f:
            existing = json.load(f)
    existing.update(catalogue)
    with open(path, "w") as f:
        json.dump(existing, f, indent=2, sort_keys=True)
    print("catalogue: %d instances -> %s" % (len(existing), path))


if __name__ == "__main__":
    sys.exit(main())
