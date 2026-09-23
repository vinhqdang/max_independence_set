# The document is named for what it contains, not for being the entry point:
# a downloaded cascade-mis.pdf is identifiable, main.pdf is not.
PAPER = cascade-mis

$(PAPER).pdf: $(PAPER).tex refs.bib tables/*.tex
	latexmk -pdf -interaction=nonstopmode $(PAPER).tex

tables:
	python3 ../scripts/make_tables.py

clean:
	latexmk -C
	rm -f $(PAPER).bbl

.PHONY: tables clean
