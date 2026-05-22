# Data Model

The model separates evidence from evaluation. Evidence describes what was
observed. Assessment describes what that evidence means for controls, risk, and
owners.

## Logical Model

```mermaid
erDiagram
  ASSET {
    string asset_id PK
    string asset_type
    string owner
    string environment
    string business_unit
  }

  EVIDENCE_ITEM {
    string evidence_id PK
    string source
    string evidence_ref
    datetime collected_at
    datetime expires_at
    string raw_sha256
  }

  CONTROL {
    string control_id PK
    string framework
    string title
    string owner
    string risk_domain
    string evidence_requirement
    string frequency
  }

  CONTROL_TEST {
    string test_id PK
    string control_id FK
    string result
    datetime evaluated_at
    string reason
  }

  VIOLATION {
    string violation_id PK
    string control_id FK
    string asset_id FK
    string evidence_id FK
    string severity
    string state
    datetime detected_at
  }

  SNAPSHOT {
    string assessment_hash PK
    string assessment_type
    datetime evaluated_at
    string reason
    string posture_state
  }

  ASSET ||--o{ EVIDENCE_ITEM : observed_on
  CONTROL ||--o{ CONTROL_TEST : evaluated_by
  CONTROL ||--o{ VIOLATION : violated_by
  ASSET ||--o{ VIOLATION : has
  EVIDENCE_ITEM ||--o{ VIOLATION : supports
  SNAPSHOT ||--o{ CONTROL_TEST : freezes
  SNAPSHOT ||--o{ VIOLATION : freezes
```

## Physical Tables

| Layer | Table/object | Purpose |
|---|---|---|
| Bronze | `raw_events` | immutable source evidence plus raw hash |
| Silver | `normalized_events` | canonical evidence facts |
| Gold | `control_posture` | current control status and evidence coverage |
| Gold | `asset_risk` | owner-ready risk queue |
| Gold | `current_posture` | live assessment result |
| Gold | `assessment_snapshots` | point-in-time assessment exports |
| API | `/api/posture/current` | current posture contract |
| API | `/api/violations` | open violation contract |
| Catalog | `frameworks/registry.json` | official framework source registry |
| Catalog | `controls/catalog.json` | implemented controls with evidence requirements |

## Schema Contracts

- [Raw security event](../data/schemas/raw-security-event.schema.json)
- [Normalized event](../data/schemas/normalized-event.schema.json)
- [Current posture](../data/schemas/current-posture.schema.json)
- [Violation](../data/schemas/violation.schema.json)
