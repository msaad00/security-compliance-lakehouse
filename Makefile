.PHONY: test validate pipeline dashboard smoke web-install web-dev web-typecheck web-build web-clean

test:
	PYTHONPATH=src python -m pytest -q

validate:
	PYTHONPATH=src python -m security_lakehouse.cli validate --raw data/raw/security_events.jsonl

pipeline:
	PYTHONPATH=src python -m security_lakehouse.cli pipeline run --raw data/raw/security_events.jsonl --out build/lakehouse

dashboard:
	PYTHONPATH=src python -m security_lakehouse.cli dashboard --lake build/lakehouse --out build/dashboard/index.html

smoke: validate pipeline dashboard test

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

web-clean:
	rm -rf src/security_lakehouse/web/dist/* src/security_lakehouse/web/dist/.* 2>/dev/null || true
	mkdir -p src/security_lakehouse/web/dist
	touch src/security_lakehouse/web/dist/.gitkeep
