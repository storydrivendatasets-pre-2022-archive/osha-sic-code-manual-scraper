.DEFAULT_GOAL := help
.PHONY : clean_wrangled_db clean_compiled_db help ALL

clean:
	rm -rf data/collected


help:
	@echo 'Run `make ALL` to see how things run from scratch'

ALL: collect


collect:
	./scripts/collect_pages.py
