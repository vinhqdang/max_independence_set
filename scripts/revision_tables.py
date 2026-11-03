#!/usr/bin/env python3
"""LaTeX tables and summary numbers for the revision experiments, from
results/revision.jsonl.  Prints the statistics quoted in the text."""
import collections
import json
import os
import statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "paper", "tables")
R = [json.loads(l) for l in open(os.path.join(ROOT, "results", "revision.jsonl"))]


def name(r):
    p = r["instance"]
    parts = p.split("/")
    if "geo" in parts:
        return parts[-2] + "/" + os.path.splitext(parts[-1])[0]
    if p.endswith(".mtx"):
        return "DIMACS10 " + os.path.basename(p).replace(".mtx", "").replace("delaunay_", "delaunay\\_")
    return os.path.splitext(parts[-1])[0]


def tt(x):
    return r"\texttt{%s}" % x.replace("_", r"\_").replace("s1/", "").replace("/", r"\slash ")


def group(g):
    return [r for r in R if r["group"] == g]


def write(fn, lines):
    open(os.path.join(OUT, fn), "w").write("\n".join(lines) + "\n")


def kernel_table():
    cap = {name(r): r for r in group("kernel_capped")}
    full = {name(r): r for r in group("kernel_full")}
    ex = {name(r): r for r in group("exact")}
    order = sorted(cap, key=lambda i: cap[i]["n"])
    L = [r"\begin{table}[htbp]", r"\centering",
         r"\caption{Residual kernel after reduction, and the whole-input exact solve. "
         r"\emph{Capped}: kernelization under the 60\,s run's own rule (a share $\kappa=0.3$ of the budget). "
         r"\emph{Full}: run to a fixed point (limit 300\,s). \emph{Exact}: \textsc{Cascade}\,\texttt{--exact} "
         r"on the whole input, limit 120\,s; time to a proven optimum, or the best value if not proved. "
         r"Kernel size is the number of vertices left.}",
         r"\label{tab:kernels}", r"\small", r"\fittable{",
         r"\begin{tabular}{lrrrrrrrr}", r"\toprule",
         r"Instance & $n$ & capped $|K|$ & \% of $n$ & time (s) & full $|K|$ & time (s) & exact (s) & status \\", r"\midrule"]
    for i in order:
        c, f, e = cap[i], full.get(i), ex.get(i)
        st_ = "--"
        es = "--"
        if e:
            if e.get("proved_optimal") == 1:
                st_, es = "proved", "%.2f" % e["time"]
            elif "size" not in e:
                st_, es = "no output", "%.0f" % e["wall"]
            else:
                st_, es = "open", "%.0f" % e["time"]
        L.append("%s & %d & %d%s & %.2f & %.2f & %s & %s & %s & %s \\\\" % (
            tt(i), c["n"], c["kernel_n"], r"$^{\ast}$" if c["kernel_truncated"] else "",
            100.0 * c["kernel_n"] / c["n"], c["kernel_time"],
            ("%d" % f["kernel_n"]) if f else "--", ("%.2f" % f["kernel_time"]) if f else "--", es, st_))
    L += [r"\bottomrule", r"\end{tabular}}",
          r"\\[2pt]\footnotesize $^{\ast}$ kernelization stopped by the budget share before a fixed point.",
          r"\end{table}"]
    write("kernels.tex", L)
    # summary numbers
    ks = [100.0 * cap[i]["kernel_n"] / cap[i]["n"] for i in order]
    print("kernel %% of n (capped): min %.3f median %.3f max %.2f" % (min(ks), st.median(ks), max(ks)))
    for i in order:
        e = ex.get(i)
        print("%-26s n=%-8d capK=%-8d (%.2f%%) trunc=%d fullK=%s exact=%s t=%s" % (
            i, cap[i]["n"], cap[i]["kernel_n"], 100.0 * cap[i]["kernel_n"] / cap[i]["n"], cap[i]["kernel_truncated"],
            full.get(i, {}).get("kernel_n"), e and e.get("proved_optimal"), e and e.get("time")))


def mean_(xs):
    return sum(xs) / len(xs)


def ablation_table():
    var = [("full", "exact repair, regional reductions (full)"), ("heuristic", "heuristic repair (reduce, then one greedy pass)"),
           ("noreduce", "exact repair, no regional reductions"), ("nolns", "no region moves")]
    cells = collections.defaultdict(list)
    for v, _ in var:
        for r in group("ablation_" + v):
            cells[(name(r), v)].append(r)
    insts = []
    for r in group("ablation_full"):
        if name(r) not in insts:
            insts.append(name(r))
    L = [r"\begin{table}[htbp]", r"\centering",
         r"\caption{Exact against heuristic repair, and regional reductions on and off, under one implementation, "
         r"one region-selection rule and one 60\,s budget. Mean size over three seeds (bracket: change from the full "
         r"configuration). The last three columns are process data for the full configuration on that instance "
         r"(per region move, mean over seeds): vertices in the region before reduction, vertices left after the root "
         r"reduction pass, and the share of sub-solves proved optimal.}",
         r"\label{tab:regional}", r"\small", r"\fittable{",
         r"\begin{tabular}{l" + "r" * len(var) + "rrr}", r"\toprule",
         "Instance & " + " & ".join(l for _, l in var) + r" & $|R|$ & $|R'|$ & proved \\", r"\midrule"]
    tot = collections.defaultdict(float)
    for i in insts:
        base = mean_([r["size"] for r in cells[(i, "full")]])
        row = [tt(i)]
        for v, _ in var:
            xs = [r["size"] for r in cells[(i, v)]]
            if not xs:
                row.append("--"); continue
            m = mean_(xs)
            row.append("%.1f" % m if v == "full" else "%.1f (%+.1f)" % (m, m - base))
            tot[v] += m - base
        f = cells[(i, "full")]
        mv = sum(r["lns_moves"] for r in f)
        row += ["%.0f" % (sum(r["lns_region_v"] for r in f) / mv), "%.1f" % (sum(r["lns_root_alive"] for r in f) / mv),
                "%.1f\\%%" % (100.0 * sum(r["lns_proved"] for r in f) / mv)]
        L.append(" & ".join(row) + r" \\")
    L += [r"\bottomrule", r"\end{tabular}}", r"\end{table}"]
    write("regional.tex", L)
    print("ablation summed change vs full:", dict(tot))
    for i in insts:
        print(i, {v: round(mean_([r["size"] for r in cells[(i, v)]]), 1) for v, _ in var if cells[(i, v)]},
              "moves/s full", round(mean_([r["lns_moves"] / r["time"] for r in cells[(i, "full")]])))


def delaunay_table():
    cells = collections.defaultdict(list)
    for r in group("delaunay"):
        cells[name(r)].append(r["size"])
    L = [r"\begin{table}[htbp]", r"\centering",
         r"\caption{\textsc{Cascade} on independent Delaunay graphs: seeds 1--6 of the generator and the public "
         r"DIMACS10 \texttt{delaunay\_n} graphs, 60\,s. Solver seeds 1--3 (1--2 for $2^{16}$ and $2^{18}$ seeds 4--6; "
         r"see text). Baselines were not run on these instances.}",
         r"\label{tab:delaunay}", r"\small", r"\begin{tabular}{lrrrr}", r"\toprule",
         r"Instance & runs & min & mean & max \\", r"\midrule"]
    for i in sorted(cells, key=lambda x: (("DIMACS" in x), x)):
        v = cells[i]
        L.append("%s & %d & %d & %.1f & %d \\\\" % (tt(i) if "DIMACS" not in i else i.replace("DIMACS10 ", r"DIMACS10 \texttt{") + "}", len(v), min(v), mean_(v), max(v)))
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    write("delaunay.tex", L)
    for i, v in sorted(cells.items()):
        print(i, v)


def sweep_table():
    cells = collections.defaultdict(dict)
    ks = set()
    for r in group("sweep_k"):
        k = int(r["args"].split()[-1])
        cells[name(r)][k] = r
        ks.add(k)
    ks = sorted(ks)
    L = [r"\begin{table}[htbp]", r"\centering",
         r"\caption{Sensitivity to the initial number of released vertices $k_0$ (\texttt{--lns-free}); the online rule "
         r"then adapts $k$. One run per cell, 60\,s. The last column is the final $k$ reached at $k_0=4$.}",
         r"\label{tab:ksweep}", r"\small", r"\begin{tabular}{l" + "r" * len(ks) + "r}", r"\toprule",
         "Instance & " + " & ".join("$k_0=%d$" % k for k in ks) + r" & spread (\%) \\", r"\midrule"]
    for i, d in cells.items():
        v = [d[k]["size"] for k in ks if k in d]
        L.append(tt(i) + " & " + " & ".join(str(d[k]["size"]) if k in d else "--" for k in ks) +
                 " & %.3f \\\\" % (100.0 * (max(v) - min(v)) / max(v)))
        print(i, {k: (d[k]["size"], d[k].get("lns_free")) for k in ks if k in d})
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    write("ksweep.tex", L)


if __name__ == "__main__":
    import sys
    for f in (sys.argv[1:] or ["kernel", "ablation", "delaunay", "sweep"]):
        print("==", f)
        {"kernel": kernel_table, "ablation": ablation_table, "delaunay": delaunay_table, "sweep": sweep_table}[f]()
