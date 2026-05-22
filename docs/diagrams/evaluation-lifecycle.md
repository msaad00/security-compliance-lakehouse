# Evaluation Lifecycle

```mermaid
sequenceDiagram
  participant Connector
  participant Evidence as Evidence Model
  participant Catalog as Control Catalog
  participant Engine as Evaluation Engine
  participant Posture as Current Posture
  participant Owner as Owner Queue
  participant Snapshot as Snapshot Service
  participant API as Human/Agent API

  Connector->>Evidence: publish normalized evidence
  Catalog->>Engine: controls, owners, requirements
  Evidence->>Engine: fresh evidence facts
  Engine->>Posture: framework scores and control states
  Engine->>Owner: violations and remediation ownership
  API->>Posture: GET /api/posture/current
  API->>Owner: GET /api/violations
  API->>Snapshot: POST /api/snapshots
  Snapshot->>Snapshot: freeze assessment hash
  Snapshot-->>API: snapshot path and reason
```

## Loop

The loop repeats whenever new evidence arrives or control definitions change:

```text
evidence update -> evaluate controls -> update current posture -> notify owners
```

Snapshots are not the normal operating state. They are freeze points for
specific review moments.
