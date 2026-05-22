# Data Model

```mermaid
erDiagram
  NORMALIZED_EVENTS {
    string event_id PK
    string tenant_id
    datetime event_time
    string source
    string event_type
    string asset_id
    string asset_type
    string asset_owner
    string environment
    string severity
    int severity_score
    string status
    string control_ids_json
    string evidence_id
    string evidence_ref
    string raw_sha256
  }

  CONTROL_POSTURE {
    string control_id PK
    string framework
    string title
    string risk_domain
    string owner
    string status
    int risk_score
    int event_count
    int open_event_count
    int evidence_count
    float evidence_coverage
    datetime latest_event_time
  }

  ASSET_RISK {
    string asset_id PK
    string asset_type
    string asset_owner
    string environment
    int risk_score
    int critical_open
    int high_open
    int event_count
    datetime latest_event_time
  }

  METRICS {
    string metric PK
    string value
  }

  NORMALIZED_EVENTS }o--o{ CONTROL_POSTURE : maps_to_controls
  NORMALIZED_EVENTS }o--|| ASSET_RISK : rolls_up_to_asset
```

## Canonical Event Fields

| Field | Purpose |
|---|---|
| `event_id` | Source-stable event identifier |
| `tenant_id` | Boundary for multi-tenant analytics |
| `source` | Tool or system that produced the evidence |
| `event_type` | Normalized event family such as `vulnerability.finding` |
| `asset_id` | Canonical asset key for joins and rollups |
| `control_ids` | Framework controls affected by this event |
| `evidence_ref` | Pointer to the retained artifact |
| `raw_sha256` | Replay and tamper-evidence link to bronze data |
