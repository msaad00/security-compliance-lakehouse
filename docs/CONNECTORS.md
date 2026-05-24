# Connector And Access Model

TrustOps should collect evidence with the smallest viable access boundary.

## Access Priority

| Priority | Mode                             | Best for                                              | Boundary                          |
| -------- | -------------------------------- | ----------------------------------------------------- | --------------------------------- |
| 1        | Existing security data lake read | Snowflake, ClickHouse, object storage, SIEM exports   | read-only role                    |
| 2        | Managed evidence objects         | one-company rollout, local proof, starter deployments | dedicated schema/output directory |
| 3        | Direct tool API read             | source systems that are the evidence authority        | scoped token or app installation  |

Avoid broad cloud permissions. Connectors should not need admin, delete, owner,
or unrestricted write access to evaluate posture.

## Production Hero Paths

| Store      | Role                                                | Connector                   |
| ---------- | --------------------------------------------------- | --------------------------- |
| Snowflake  | governed evidence, audit views, retention, RBAC     | `snowflake-evidence-lake`   |
| ClickHouse | telemetry, runtime events, trends, fast aggregation | `clickhouse-telemetry-lake` |

## Catalog

The connector catalog is versioned in:

```text
connectors/catalog.json
```

Validate it with:

```bash
security-lakehouse connectors validate
```

List configured connector contracts:

```bash
security-lakehouse connectors list
```

The validator rejects:

- missing collection mode, access boundary, route, permissions, or freshness SLO
- existing-lake connectors that are not read-only
- direct API connectors that are not scoped-token based
- managed evidence mode without a dedicated schema/boundary
- secret-like field names or token-shaped values in the catalog
- broad permission words such as admin, delete, drop, modify, owner, or root
