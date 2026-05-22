# Dashboard App

The dashboard is generated as static HTML:

```bash
security-lakehouse dashboard \
  --lake build/lakehouse \
  --out build/dashboard/index.html
```

The generated page contains:

- architecture-first TrustOps overview
- Snowflake and ClickHouse evidence-routing panels
- bronze/silver/gold pipeline stages
- executive trust KPIs
- evidence connector mix
- control posture table
- asset risk remediation queue
- auditor-facing evidence room

The dashboard is only a consumer. The product core is the assessment engine:

```bash
security-lakehouse assessment status --lake build/lakehouse
security-lakehouse assessment snapshot --lake build/lakehouse --reason audit_request
security-lakehouse assessment violations --lake build/lakehouse
```

This keeps the demo easy to run in interviews while still proving the data
pipeline and visualization layer end to end.
