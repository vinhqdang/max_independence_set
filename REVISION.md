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

Resubmitted to EJOR after the technical check (EJOR-D-26-05254) on 5 November 2026:
main manuscript (30 pp) plus supplement (19 pp), 5 keywords. Next step is the editor's
scientific assessment; the open items above (InfVC, baselines on the independent Delaunay
graphs) still apply.

## EJOR outcome (reported 7 November 2026)

EJOR-D-26-05254 was desk-rejected. The editor's stated reason was fit: the paper is better
suited to a computing-oriented journal than to EJOR. No scientific assessment was made, so
there are no new reviewer comments.

Next: transfer to a computing / operations-research journal (named by the author as
"Computers and Operations Research"; note that the first submission, CAOR-D-26-02865, was
rejected by that journal on 23 September 2026 reviews, so confirm whether this is the same
journal or a different one before reformatting).

Submission history:

| date | journal | reference | outcome |
| --- | --- | --- | --- |
| 23 Sep 2026 | Computers & Operations Research | CAOR-D-26-02865 | rejected after review (four reports) |
| 4 Nov 2026 | European Journal of Operational Research | EJOR-D-26-05254 | sent back at technical check (35 pages at 1.5 spacing, 3-5 keywords) |
| 5 Nov 2026 | European Journal of Operational Research | EJOR-D-26-05254 | resubmitted, 30 pp + 19 pp supplement, 5 keywords |
| 7 Nov 2026 | European Journal of Operational Research | EJOR-D-26-05254 | desk-rejected on fit (editor: better suited to a computing journal) |

The EJOR-format manuscript (30 pages, 5 keywords, separate supplement) and the response
letter remain valid for a new target; only the journal name in `\journal{}`, the cover letter
and the highlights/keyword limits need checking against the new guide for authors.

## Computational Optimization and Applications (Springer), 7 November 2026

The target is *Computational Optimization and Applications* (the author's clarification: not
Computers & Operations Research, which already rejected the paper). Springer Nature template
(`sn-jnl`, numbered references, `sn-mathphys-num`).

* Main manuscript: `paper/cascade-mis-coap.tex` (27 pp). Abstract 167 words (limit 150-250),
  5 keywords (limit 4-6), declarations section before the references, AI use documented in
  Section 5.1 (Methods), supplement cited as Online Resource 1.
* Online Resource 1: `paper/supplement-coap.tex` (19 pp; build the main file first).
* Cover letter: `paper/cover-letter-coap.txt`.
* The Elsevier-format files (`cascade-mis.tex`, `supplement.tex`) are kept for reference.
* Springer wants editable source: submit the `.tex`, `sn-jnl.cls`, `sn-mathphys-num.bst`,
  `refs.bib`/`.bbl`, tables, figures and the compiled PDF.

Submission history addendum:

| date | journal | outcome |
| --- | --- | --- |
| 7 Nov 2026 | Computational Optimization and Applications | submitted (Springer Nature template, 27 pp + Online Resource 1, 19 pp) |

Submitted to Computational Optimization and Applications on 7 November 2026. Next step: the
editor's decision. If reviewers ask for it: run ReduMIS, FastVC and InfVC on the independent
Delaunay graphs (checksums in `results/instance_checksums.sha256`), add InfVC to the main
benchmark, and check the InfVC author list and the two arXiv entries in `paper/refs.bib`.
