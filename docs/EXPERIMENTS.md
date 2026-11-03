# Experimental evaluation

The experimental record is the paper (`paper/`) and the raw per-run records in
`results/`.  The earlier tables kept here were built from five of the seven
solvers and are superseded.

| file | content |
| --- | --- |
| `results/cor_main60.csv` | main comparison, seven solvers, 27 instances, 60 s |
| `results/cor_seeds60.csv` | five-seed study on ten instances |
| `results/cor_long600.csv` | 600 s budget on four instances |
| `results/replication60.csv` | second platform |
| `results/revision.jsonl` | kernel statistics, whole-input exact solves, regional ablation with process counters, sweep over the initial release size, independent Delaunay graphs |
| `results/instance_checksums.sha256` | SHA-256 of every downloaded and generated instance file |

Tables are regenerated with `scripts/make_tables.py` (main comparison),
`scripts/stats_test.py` (Wilcoxon on relative gaps, Holm-corrected) and
`scripts/revision_tables.py` (revision experiments).  Every solution is checked
by `build/mis-verify` where the solver emits the set; the two reducing-peeling
programs print a size only, and their values are unverified.

One note on BHOSLIB.  The instances are distributed in clique form, and the copies
on Network Repository are the dense clique graphs (`frb30-15-1` has 450 vertices
and 83,198 edges, independence number 15).  The MIS instance is the complement
(17,827 edges, independence number 30) and that is what is benchmarked.
