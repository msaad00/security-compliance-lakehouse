# Product Walkthrough

| First command                                                                                | Artifact                                                                                        | App URL                                                                                      |
| -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `security-lakehouse pipeline run --raw data/raw/security_events.jsonl --out build/lakehouse` | `build/lakehouse/gold/current_posture.json` plus bronze, silver, gold, snapshot, and mart files | `http://127.0.0.1:8787/` after `security-lakehouse serve --lake build/lakehouse --port 8787` |

TrustOps Security Data Lake is an open-source assessment layer for security
evidence lakes. It turns local or lake-backed evidence into posture files,
control tests, owner queues, graph views, snapshots, and agent-readable API
responses.

This walkthrough is intentionally honest about what is shipped versus planned.
TrustOps is not presented as a full enterprise GRC replacement. The shipped
product proves the evidence model, local workbench, catalog contracts, public
repo audit, and API surfaces that a buyer or contributor can run today.

## First Run

| Step               | Command                                                                                       | Artifact                                                       | Next step                         |
| ------------------ | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | --------------------------------- |
| Install locally    | `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`                | editable `security-lakehouse` CLI                              | run the pipeline                  |
| Build the lake     | `security-lakehouse pipeline run --raw data/raw/security_events.jsonl --out build/lakehouse`  | `build/lakehouse/bronze`, `silver`, `gold`, and `mart` outputs | inspect posture                   |
| Check posture      | `security-lakehouse assessment status --lake build/lakehouse`                                 | current scores, confidence inputs, and violations              | freeze or serve evidence          |
| Freeze evidence    | `security-lakehouse assessment snapshot --lake build/lakehouse --reason vendor_due_diligence` | `build/lakehouse/gold/snapshots/assessment-*.json`             | share the immutable snapshot path |
| Open the workbench | `security-lakehouse serve --lake build/lakehouse --port 8787`                                 | local console and API                                          | open `http://127.0.0.1:8787/`     |

The lake output is the proof point. The UI and APIs read from those generated
files instead of asking users to trust marketing copy.

## Shipped Product Surface

| Surface                        | Shipped today                                                                                                                                                                                                                  | Evidence                                                                                                                                          |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Next workbench                 | Static Next.js workbench served by the Python package when the web build is available; routes cover dashboard, controls, evidence, violations, connectors, frameworks, automation, graph, agents, trust center, and audit log. | `app/web/src/app/*/page.tsx`, `src/security_lakehouse/server.py`                                                                                  |
| `/api/v1` envelopes            | Versioned routes return `{data, meta, errors}` envelopes with pagination, sorting, and filters on list resources.                                                                                                              | `docs/api/AGENT_API.md`, `tests/test_api_v1.py`                                                                                                   |
| Local lake outputs             | Pipeline emits bronze raw evidence, silver normalized events, gold posture/control/asset files, snapshots, and a SQLite mart.                                                                                                  | `src/security_lakehouse/pipeline.py`, `README.md#data-model`                                                                                      |
| Public repo audit              | CLI audits public GitHub repositories without credentials and emits normalized raw evidence, including metadata, workflows, manifests, IaC, AI artifacts, and a code graph signal.                                             | `src/security_lakehouse/repo_audit.py`, `docs/REPO_AUDIT.md`, `tests/test_repo_audit.py`                                                          |
| Connector catalog + runner     | Static connector access-boundary catalog plus CLI validation/listing/configure, UI/API state, probe/run history, and a first executable `github-security` sync runner that writes raw evidence and can materialize the lake.   | `connectors/catalog.json`, `src/security_lakehouse/connectors.py`, `src/security_lakehouse/connector_runner.py`, `tests/test_connector_runner.py` |
| Framework catalog and coverage | Source-linked framework registry, readiness gates, reviewed mappings, crosswalks, and neutral text-only coverage visuals. Official marks are not shipped without documented permission.                                        | `frameworks/registry.json`, `mappings/control_map.json`, `docs/images/trustops-framework-coverage.svg`, `tests/test_mappings.py`                  |
| Workflow canvas                | Typed workflow graph model with trigger, condition, assignment, snapshot, webhook, and trust-share actions; UI canvas and API endpoints persist and run workflow versions.                                                     | `src/security_lakehouse/workflows.py`, `app/web/src/app/automation/page.tsx`, `tests/test_workflows.py`                                           |
| Compliance graph canvas        | Framework -> control -> evidence type -> asset graph endpoint and visual canvas with filters, path tracing, and exports.                                                                                                       | `src/security_lakehouse/graph.py`, `app/web/src/app/graph/page.tsx`, `tests/test_graph_fixtures.py`                                               |
| Snapshots                      | CLI and API freeze point-in-time assessment JSON with reason, assessment hash, posture, frameworks, and violations.                                                                                                            | `src/security_lakehouse/assessment.py`, `tests/test_pipeline.py`, `tests/test_api_v1.py`                                                          |
| Evidence room                  | Evidence view traces normalized events to controls, sources, hashes, and collection time.                                                                                                                                      | `app/web/src/app/evidence/page.tsx`, `src/security_lakehouse/server.py`                                                                           |

## Planned Or Incomplete

| Area                              | Planned, not claimed as complete                                                                             | Current honest boundary                                                                                                                                                                  |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hosted multi-tenant control plane | Production-grade tenant isolation, managed accounts, admin lifecycle, billing, and hosted operations.        | The repo ships local/self-hosted patterns and API contracts, not a hosted SaaS control plane.                                                                                            |
| Enterprise connector ingestion    | Direct production ingestion for every source system in the catalog.                                          | The `github-security` runner is executable with a fixture or read-only token. Other catalog sources remain planned or existing-lake-read contracts.                                      |
| Full framework coverage           | Exhaustive official-control evaluation for every listed framework.                                           | Frameworks are source-linked and readiness-gated with limited mappings. Neutral framework labels show source-linked scope and readiness-gate status; they do not indicate certification. |
| Auditor collaboration room        | External reviewer accounts, comments, requests, approvals, and export workflows.                             | Snapshots and trust-share lifecycle primitives exist; full collaboration workflow is future work.                                                                                        |
| Policy enforcement                | Preventive controls across identity, cloud, CI, and runtime systems.                                         | TrustOps currently assesses evidence and drives workflow actions; it does not claim broad enforcement.                                                                                   |
| Production lake adapters          | Complete Snowflake and ClickHouse operational adapters with migrations, auth, retention, and scheduled sync. | Schema artifacts exist; the default runnable path is local files plus SQLite, with optional DuckDB analytics.                                                                            |

## Walkthrough Paths

### 1. Local Evidence To Workbench

Run:

```bash
security-lakehouse pipeline run \
  --raw data/raw/security_events.jsonl \
  --out build/lakehouse
security-lakehouse serve --lake build/lakehouse --port 8787
```

Artifact:

- `build/lakehouse/gold/current_posture.json`
- `build/lakehouse/gold/control_tests.jsonl`
- `build/lakehouse/gold/asset_risk.jsonl`
- `build/lakehouse/mart/security_lakehouse.sqlite`

Next step: open `http://127.0.0.1:8787/` and use the workbench to inspect
posture, controls, evidence, violations, graph, and snapshots.

### 2. Agent Or API Review

Run:

```bash
curl -s http://127.0.0.1:8787/api/v1/posture/current | jq .
curl -s 'http://127.0.0.1:8787/api/v1/control-tests?result=fail&limit=10' | jq .
curl -s -X POST http://127.0.0.1:8787/api/v1/snapshots \
  -H 'content-type: application/json' \
  --data '{"reason":"vendor_due_diligence"}' | jq .
```

Artifact: JSON envelopes with `data`, `meta`, and `errors`.

Next step: route failed controls to the owner queue or freeze a snapshot for a
review packet.

### 3. Public Repository Audit

Run:

```bash
security-lakehouse repo audit OWNER/REPO --out build/repo-audit.jsonl
```

Artifact: normalized raw evidence for a public repository, including repository
metadata, workflow files, manifests, policy files, infrastructure hints, AI
artifacts, and a code graph summary.

Next step: feed `build/repo-audit.jsonl` into the pipeline or inspect it as
source evidence for supply-chain posture.

### 4. Connector And Framework Catalog Review

Run:

```bash
security-lakehouse connectors validate
security-lakehouse connectors list
security-lakehouse connectors configure --lake build/lakehouse --connector-id github-security --state enabled
security-lakehouse connectors sync \
  --lake build/lakehouse \
  --connector-id github-security \
  --repo acme/model-service \
  --fixture-dir tests/fixtures/github-governance
security-lakehouse frameworks readiness
```

Artifact: connector access-boundary JSON, connector raw evidence, materialized
lake outputs, run history, and framework readiness rows.

Next step: choose the smallest viable integration boundary: read-only existing
lake role, scoped source API token, or managed evidence object.

## Screenshots And Visual Assets

| Asset                                                         | Status                                                                                                                                                           |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Control-plane/workbench screenshot                            | Available at `docs/images/trustops-console.png`.                                                                                                                 |
| Framework coverage graphic                                    | Available at `docs/images/trustops-framework-coverage.svg`.                                                                                                      |
| Control detail, evidence room, connector setup, snapshot room | Not yet committed as separate screenshots. The shipped UI routes exist, but this walkthrough does not imply screenshot coverage until image artifacts are added. |

## Buyer-Readable Boundary

TrustOps is useful today for proving an evidence model:

- first command -> local lake artifact -> workbench/API
- evidence -> controls -> violations -> owner workflow
- framework registry -> source-linked mapping -> readiness gate
- public repo audit -> normalized evidence -> graph signal
- snapshot -> immutable review artifact -> next action

The current product is strongest as a self-hosted OSS proof-of-value and
developer-facing evidence workbench. Broader enterprise workflows should be
positioned as roadmap unless code, tests, deployment artifacts, and live smoke
evidence prove them in this repository.
