# Security Compliance Lakehouse

End-to-end security and compliance analytics project:

- ingest raw security evidence as JSONL
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
lakes: raw evidence, normalized events, dimensional marts, control mappings,
metrics, visualization, and audit-ready exports.

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

The project demonstrates the full analytics path employers expect from a
security data engineer or security analytics engineer:

1. **Ingestion**: raw security events from scanners, cloud posture, identity,
   runtime policy, ticketing, and audit systems.
2. **Transformation**: deterministic normalization into canonical entities.
3. **Mapping logic**: evidence-to-control joins with severity and status rules.
4. **Metrics**: control coverage, evidence freshness, open critical risk,
   runtime block rate, SLA posture, and asset risk concentration.
5. **Visualization**: static dashboard generated from the gold metrics.
6. **Evidence app**: SQLite mart and JSON artifacts for queries and audits.
7. **Agent skill**: repeatable instructions for an AI agent to answer posture,
   audit, and remediation questions using the produced artifacts.
8. **Hero data lakes**: Snowflake schema/views for governed audit evidence and
   ClickHouse tables/views for fast telemetry analytics.

## Internal Compliance Tool Scope

The project is shaped like a compact trust operations product:

| Capability | Small-company version |
|---|---|
| Connector inventory | JSONL evidence from cloud, vuln, identity, runtime, SIEM, ticketing, and model registry sources |
| Control library | SOC 2, ISO 27001, CIS, PCI, and NIST AI RMF mappings with owner and risk domain |
| Continuous testing | pass/fail control posture, evidence coverage, runtime block rate, open risk events |
| Current posture | continuously refreshed `current_posture.json` with framework scores and violations |
| Point-in-time snapshots | immutable assessment exports for audits, incidents, and just-in-time vendor reviews |
| Owner workflows | asset risk queue and control workbench for remediation ownership |
| Audit room | evidence table with retained artifact references and raw hashes |
| Data lakes | Snowflake for governed evidence, ClickHouse for high-volume telemetry |

## Hero Security Data Lakes

This repo uses two production data-lake stories:

| Backend | Role | Proof |
|---|---|---|
| Snowflake | Governed evidence lake for audit, GRC, RBAC, retention, and executive reporting | `deploy/snowflake/schema.sql` |
| ClickHouse | Telemetry analytics lake for runtime events, detections, fast aggregations, and dashboards | `deploy/clickhouse/schema.sql`, `deploy/clickhouse/docker-compose.yml` |

See [Hero Security Data Lakes](docs/HERO_DATA_LAKES.md) and the
[Dual Lakehouse Architecture](docs/diagrams/dual-lakehouse.md).

## Core Commands

```bash
security-lakehouse validate --raw data/raw/security_events.jsonl
security-lakehouse pipeline run --raw data/raw/security_events.jsonl --out build/lakehouse
security-lakehouse query --lake build/lakehouse "select * from control_posture order by risk_score desc"
security-lakehouse assessment status --lake build/lakehouse
security-lakehouse assessment snapshot --lake build/lakehouse --reason vendor_due_diligence
security-lakehouse dashboard --lake build/lakehouse --out build/dashboard/index.html
```

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
