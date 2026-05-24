# Mockup company fixtures

Synthetic-but-realistic evidence sets you can pipe through the lake to demo
the workbench without standing up real connectors.

Each company directory ships a `raw/security_events.jsonl` shaped exactly
like real connector output. Load one with the CLI:

```bash
security-lakehouse fixtures list
security-lakehouse fixtures load --company saas --out build/lakehouse-saas
security-lakehouse serve --lake build/lakehouse-saas
```

The shipped companies are:

| Company | Profile |
| --- | --- |
| `saas` | Mid-size SaaS company — typical SOC 2 surface (IAM, GitHub, AWS, Okta, Jira). |
| `ai_lab` | AI/ML lab — model registry + runtime inference + MCP server evidence in addition to the SaaS baseline. |

Add a new company by dropping a directory with `raw/security_events.jsonl`
(must reference only control IDs that exist in `controls/catalog.json`).
