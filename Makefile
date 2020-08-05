.DEFAULT_GOAL := help
.PHONY : clean_wrangled_db clean_compiled_db help ALL

clean:
	rm -rf data/collected data/compiled


help:
	@echo 'Run `make ALL` to see how things run from scratch'

ALL: collect

compile: data/compiled/sic_manual.csv

data/compiled/sic_manual.csv:
	./scripts/compile_manual.py

collect:
	./scripts/collect_pages.py
