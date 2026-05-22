.PHONY: test validate pipeline dashboard smoke

test:
	PYTHONPATH=src python -m pytest -q

validate:
	PYTHONPATH=src python -m security_lakehouse.cli validate --raw data/raw/security_events.jsonl

pipeline:
	PYTHONPATH=src python -m security_lakehouse.cli pipeline run --raw data/raw/security_events.jsonl --out build/lakehouse

dashboard:
	PYTHONPATH=src python -m security_lakehouse.cli dashboard --lake build/lakehouse --out build/dashboard/index.html

smoke: validate pipeline dashboard test
