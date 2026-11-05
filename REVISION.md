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

## Submission record

Submitted to the European Journal of Operational Research on 4 November 2026
(manuscript built from the commit that follows `9c70c82`).

Title, abstract and keywords as in `paper/cascade-mis.tex`; highlights in
`paper/highlights.txt`; cover letter in `paper/cover-letter.txt`.

If the journal asks for a revision, in this order:
1. Run ReduMIS, FastVC and InfVC on the independent Delaunay graphs
   (`results/instance_checksums.sha256` lists the files; seeds 1-6 and DIMACS10).
2. Add InfVC to the main benchmark under the same rules.
3. Check the InfVC author list and the two arXiv entries in `paper/refs.bib`.

## EJOR technical check (5 November 2026)

Sent back for: (1) more than 35 pages at 1.5 line spacing, (2) more than 5 keywords.
Resubmitted version: `paper/cascade-mis.tex` is 30 pages at 1.5 spacing (11 pt, A4, 2.5 cm
margins, references included) with 5 keywords. Material that does not fit is in
`paper/supplement.tex` (19 pages): proofs of the standard reduction rules, per-family tables,
convergence, exact solvers, replication, other parameters, implementation notes and the
instance appendices. Build the main file first, then the supplement (it cross-references the
main file's labels through `xr`).
