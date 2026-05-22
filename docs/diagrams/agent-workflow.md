# Agent Workflow

```mermaid
sequenceDiagram
  participant User
  participant Agent
  participant CLI as security-lakehouse CLI
  participant Lake as Lakehouse Artifacts
  participant Mart as SQLite Mart

  User->>Agent: "Show audit gaps and top risks"
  Agent->>CLI: pipeline run --raw data/raw/security_events.jsonl --out build/lakehouse
  CLI->>Lake: write bronze/silver/gold JSON artifacts
  CLI->>Mart: create analytics tables
  Agent->>CLI: query --lake build/lakehouse "select * from control_posture..."
  CLI->>Mart: read-only SQL
  Mart-->>CLI: risk-ranked controls
  CLI-->>Agent: JSON results
  Agent-->>User: evidence-backed summary with file paths and next actions
```

Agents should answer from generated artifacts, not from memory. Every claim in
an agent response should cite one of:

- `build/lakehouse/gold/metrics.json`
- `build/lakehouse/gold/control_posture.jsonl`
- `build/lakehouse/gold/asset_risk.jsonl`
- `build/lakehouse/mart/security_lakehouse.sqlite`
- the raw evidence reference in `evidence_ref`
