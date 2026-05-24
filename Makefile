.PHONY: compile lint format-check diff-check test validate validate-json validate-generated pipeline dashboard api-smoke smoke ci web-install web-dev web-typecheck web-build web-clean web-ci

test:
	PYTHONPATH=src python -m pytest -q

compile:
	PYTHONPATH=src python -m compileall -q src tests tools

lint:
	PYTHONPATH=src python -m ruff check src tests tools

format-check:
	PYTHONPATH=src python -m ruff format --check src tests tools

diff-check:
	git diff --check

validate:
	PYTHONPATH=src python -m security_lakehouse.cli validate --raw data/raw/security_events.jsonl
	PYTHONPATH=src python -m security_lakehouse.cli connectors validate
	PYTHONPATH=src python -c "from security_lakehouse.catalog import validate_catalog; from security_lakehouse.programs import validate_program_catalog; errors = validate_catalog() + validate_program_catalog(); assert not errors, errors"

validate-json:
	PYTHONPATH=src python tools/validate_ci_artifacts.py

validate-generated:
	PYTHONPATH=src python tools/validate_ci_artifacts.py --generated

pipeline:
	PYTHONPATH=src python -m security_lakehouse.cli pipeline run --raw data/raw/security_events.jsonl --out build/lakehouse

dashboard:
	PYTHONPATH=src python -m security_lakehouse.cli dashboard --lake build/lakehouse --out build/dashboard/index.html

api-smoke:
	PYTHONPATH=src python tools/api_smoke.py

smoke: validate validate-json pipeline validate-generated dashboard api-smoke test

ci: diff-check compile lint format-check web-ci smoke

# --- React (Next.js) workbench targets -------------------------------------
# Lives in app/web/, builds to src/security_lakehouse/web/dist/ so the Python
# wheel ships the bundle. Dev mode proxies /api to a running `security-lakehouse serve`.

web-install:
	npm --prefix app/web ci

web-dev:
	npm --prefix app/web run dev

web-typecheck:
	npm --prefix app/web run typecheck

web-build:
	npm --prefix app/web run build

web-ci: web-install web-typecheck web-build

web-clean:
	rm -rf src/security_lakehouse/web/dist/* src/security_lakehouse/web/dist/.* 2>/dev/null || true
	mkdir -p src/security_lakehouse/web/dist
	touch src/security_lakehouse/web/dist/.gitkeep
