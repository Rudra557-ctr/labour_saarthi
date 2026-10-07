PY := .venv/bin/python
export PYTHONPATH := src

.PHONY: help setup sources acquire verify masters profile pilot report test reproduce clean-check publish lint-terminology serve

help:
	@grep -E '^[a-z-]+:.*?##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'

setup:  ## create venv and install dependencies
	@PY_BIN=""; \
	for c in python3.14 python3.13 python3.12 python3; do \
	  if command -v $$c >/dev/null 2>&1 && \
	     $$c -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null; \
	  then PY_BIN=$$c; break; fi; \
	done; \
	if [ -z "$$PY_BIN" ]; then \
	  echo "ERROR: need Python >= 3.12 on PATH (pyproject requires-python = >=3.12)"; exit 1; \
	fi; \
	echo "creating .venv with $$PY_BIN"; $$PY_BIN -m venv .venv
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -e '.[dev]'

sources:  ## list the source registry
	$(PY) -m lmis.cli sources

acquire:  ## acquire immutable raw snapshots (never overwrites)
	$(PY) -m lmis.cli acquire-all

verify:  ## re-hash all snapshots against their manifests
	$(PY) -m lmis.cli verify

masters:  ## build master/reference tables
	$(PY) -m lmis.cli build-masters

profile:  ## profile standardized + staging tables
	$(PY) -m lmis.cli profile

pilot:  ## validate provisional pilot scope against acquired data
	$(PY) -m lmis.cli pilot-coverage

report:  ## snapshot status per source
	$(PY) -m lmis.cli report

test:  ## run the test suite
	$(PY) -m pytest -q

facts:  ## build observed fact tables from raw snapshots
	$(PY) -m lmis.cli build-facts

validate:  ## enforce Pandera contracts -> fact_data_quality
	$(PY) -m lmis.cli validate-tables

warehouse:  ## apply DDL and load DuckDB warehouse
	$(PY) -m lmis.cli load-warehouse

analytical:  ## build the derived analytical layer
	$(PY) -m lmis.cli build-analytical

demand:  ## build the three approved demand estimates (Step 4.0)
	$(PY) -m lmis.cli build-demand

supply:  ## build the OBSERVED supply-side tables (Step 5.0)
	$(PY) -m lmis.cli build-supply

publish:  ## emit the approved Step 7.1 publication contract (metadata only)
	$(PY) -m lmis.cli publish-contract

lint-terminology:  ## fail if a published label drifts into unsupported interpretation
	$(PY) -m lmis.cli lint-terminology

serve:  ## run the API + dashboard at http://127.0.0.1:8000
	$(PY) -m uvicorn api.main:app --reload --port 8000

reproduce: verify masters facts analytical demand supply validate warehouse publish lint-terminology profile test  ## full reproducible rebuild from raw snapshots
	@echo "reproduce complete"

docs-sources:  ## regenerate docs/data_sources.md from the source registry
	$(PY) scripts/gen_data_sources.py
