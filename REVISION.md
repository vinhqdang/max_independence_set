# Revision notes

State of the manuscript in `paper/` after the second round of work.

* `paper/cascade-mis.tex` builds with `make` in `paper/` (needs `elsarticle`).
* `paper/response-letter.tex` lists every reviewer point, what changed and what is
  still open.
* New experiments are in `results/revision.jsonl`, produced by
  `scripts/revision_bench.py` and tabulated by `scripts/revision_tables.py`.
* `results/instance_checksums.sha256` has SHA-256 of every instance file used.

Open items (also in the response letter): no baseline newer than 2019 has been
run; no baseline has been run on the independent Delaunay graphs; BHOSLIB kernel
statistics were not measured; bibliographic details of the InfVC and the two
arXiv entries should be checked.
