main.pdf: main.tex refs.bib tables/*.tex
	latexmk -pdf -interaction=nonstopmode main.tex

tables:
	python3 ../scripts/make_tables.py

clean:
	latexmk -C
	rm -f main.bbl

.PHONY: tables clean
