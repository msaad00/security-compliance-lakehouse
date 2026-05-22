# Security Data Lake Compliance Assessment

Open-source continuous risk and compliance assessment layer for security teams,
platform teams, and coding agents.

The project is built around one principle: **assessment is the product;
ingestion is an input**. It can evaluate evidence from an existing security data
lake, or create the normalized lake objects a smaller company needs to get
started.

End-to-end capabilities:

- evaluate current compliance and risk posture from evidence
- create point-in-time assessment snapshots for audits and just-in-time reviews
- expose violations, controls, assets, and snapshots for humans and agents
- ingest raw security evidence as JSONL when a company does not already have a lake
- validate and normalize events into bronze, silver, and gold lake zones
- map findings and evidence to SOC 2, ISO 27001, NIST AI RMF, CIS, and PCI controls
- compute executive, security-engineering, and auditor-facing metrics
- build an SQLite analytics mart and static dashboard artifact
- model Snowflake as a governed evidence lake
- model ClickHouse as a high-volume telemetry analytics lake
- provide an agent skill for repeatable evidence questions

The product vision is a smaller internal trust automation platform for one
company: continuous control monitoring, evidence collection, owner workflows,
and an auditor-ready evidence room. See
[Internal Compliance Tool Vision](docs/INTERNAL_COMPLIANCE_TOOL.md).

This is intentionally self-contained. It runs locally with Python 3.11 and the
standard library, while modeling the same layers used in real security data
lakes: evidence, normalized facts, controls-as-code, continuous evaluations,
violations, snapshots, APIs, and audit-ready exports.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

security-lakehouse pipeline run \
  --raw data/raw/security_events.jsonl \
  --out build/lakehouse

security-lakehouse dashboard \
  --lake build/lakehouse \
  --out build/dashboard/index.html
```

Open `build/dashboard/index.html` in a browser. The generated page is an
internal TrustOps console, not just a static report.

## What It Proves

The project demonstrates the full product path employers expect from a security
platform engineer, security data engineer, or AI-era governance engineer:

1. **Assessment engine**: current posture, violations, stale evidence, framework
   scores, and immutable snapshots.
2. **Interoperability**: existing lake mode or managed lake-object mode.
3. **Evidence model**: deterministic normalization into canonical entities.
4. **Mapping logic**: evidence-to-control joins with severity and status rules.
5. **Metrics**: control coverage, evidence freshness, open critical risk,
   runtime block rate, SLA posture, and asset risk concentration.
6. **Human experience**: TrustOps console for controls, evidence, assets, and risk.
7. **Agent experience**: JSON CLI/API surfaces for posture, violations, and snapshots.
8. **Agent skill**: repeatable instructions for an AI agent to answer posture,
   audit, and remediation questions using the produced artifacts.
9. **Hero data lakes**: Snowflake schema/views for governed audit evidence and
   ClickHouse tables/views for fast telemetry analytics.

## Internal Compliance Tool Scope

The project is shaped like a compact trust operations product:

| Capability | Small-company version |
|---|---|
| Connector inventory | JSONL evidence from cloud, vuln, identity, runtime, SIEM, ticketing, and model registry sources |
| Control library | implemented seed mappings for SOC 2-oriented controls and NIST AI RMF controls with owner and risk domain |
| Continuous testing | pass/fail control posture, evidence coverage, runtime block rate, open risk events |
| Current posture | continuously refreshed `current_posture.json` with framework scores and violations |
| Point-in-time snapshots | immutable assessment exports for audits, incidents, and just-in-time vendor reviews |
| Owner workflows | asset risk queue and control workbench for remediation ownership |
| Audit room | evidence table with retained artifact references and raw hashes |
| Data lakes | Snowflake for governed evidence, ClickHouse for high-volume telemetry |

Current implemented framework scope is intentionally small: SOC 2-oriented
controls and NIST AI RMF. PCI DSS and ISO/IEC 27001 analyst skills are present
as guardrailed expansion surfaces, but their controls are not marked implemented
until a versioned catalog and validation tests are added.

## Hero Security Data Lakes

This repo uses two production data-lake stories:

| Backend | Role | Proof |
|---|---|---|
| Snowflake | Governed evidence lake for audit, GRC, RBAC, retention, and executive reporting | `deploy/snowflake/schema.sql` |
| ClickHouse | Telemetry analytics lake for runtime events, detections, fast aggregations, and dashboards | `deploy/clickhouse/schema.sql`, `deploy/clickhouse/docker-compose.yml` |

See [Hero Security Data Lakes](docs/HERO_DATA_LAKES.md) and the
[Dual Lakehouse Architecture](docs/diagrams/dual-lakehouse.md).

## Product Artifacts

Start here for the product surface:

- [Product Artifacts](docs/PRODUCT_ARTIFACTS.md)
- [Data Flow](docs/DATA_FLOW.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Data Model](docs/DATA_MODEL.md)
- [Visual System](docs/VISUAL_SYSTEM.md)
- [Human and Agent API](docs/api/AGENT_API.md)
- [Framework Analyst Skills](agent-skills/FRAMEWORK_SKILLS.md)

## Core Commands

```bash
security-lakehouse validate --raw data/raw/security_events.jsonl
security-lakehouse pipeline run --raw data/raw/security_events.jsonl --out build/lakehouse
security-lakehouse assessment status --lake build/lakehouse
security-lakehouse assessment violations --lake build/lakehouse
security-lakehouse assessment snapshot --lake build/lakehouse --reason vendor_due_diligence
security-lakehouse serve --lake build/lakehouse --port 8787
security-lakehouse query --lake build/lakehouse "select * from control_posture order by risk_score desc"
security-lakehouse dashboard --lake build/lakehouse --out build/dashboard/index.html
```

## Human And Agent API

The local server exposes assessment-first routes:

| Route | Consumer | Purpose |
|---|---|---|
| `GET /api/posture/current` | agents, dashboards, humans | current posture and framework scores |
| `GET /api/violations` | agents, owners, security engineers | open control and asset violations |
| `POST /api/snapshots` | auditors, vendor reviews, incidents | point-in-time assessment snapshot |
| `GET /api/controls` | UI, reporting, agents | control workbench data |
| `GET /api/assets` | UI, remediation owners | asset risk queue |

## Repo Structure

```text
security-compliance-lakehouse/
├─ src/security_lakehouse/        # CLI, ingestion, transform, metrics, mart
├─ data/raw/                      # sample raw security events
├─ data/schemas/                  # JSON schemas for raw and normalized records
├─ mappings/                      # framework/control mapping logic
├─ deploy/                        # Snowflake and ClickHouse schema/deploy examples
├─ docs/diagrams/                 # Mermaid architecture and data-flow diagrams
├─ agent-skills/                  # AI agent skill for analytics/audit workflows
├─ app/                           # dashboard template
└─ tests/                         # regression tests for pipeline behavior
```

## Design Notes

- Raw events are immutable JSONL records with source, tenant, timestamp, type,
  entity, severity, controls, and evidence metadata.
- Bronze keeps raw records plus SHA-256 hashes for audit replay.
- Silver normalizes fields across tools and security domains.
- Gold produces metrics, control posture, asset risk, and evidence freshness.
- The SQLite mart gives SQL access without requiring cloud infrastructure.

## Diagrams

- [Architecture](docs/diagrams/architecture.md)
- [Data Model](docs/diagrams/data-model.md)
- [Agent Workflow](docs/diagrams/agent-workflow.md)
