# Human And Agent API

The API is designed for humans, dashboards, and coding agents. The route names
describe assessment concepts, not storage implementation details.

Use `/api/v1/*` for external automation. Versioned responses always use:

```json
{
  "data": [],
  "meta": {
    "api_version": "v1",
    "resource": "control-tests",
    "count": 4,
    "returned": 4,
    "limit": 100,
    "offset": 0,
    "sort": null,
    "filters": {}
  },
  "errors": []
}
```

List routes support:

- `limit`: 1-1000, default 100
- `offset`: zero-based row offset
- `sort`: field name, or `-field` for descending
- field filters: exact scalar match, list membership match, comma-separated OR
  values

## Routes

| Method | Path                      | Purpose                                                                       |
| ------ | ------------------------- | ----------------------------------------------------------------------------- |
| `GET`  | `/api/v1/healthz`         | service health                                                                |
| `GET`  | `/api/v1/posture/current` | continuously evaluated posture                                                |
| `GET`  | `/api/v1/control-tests`   | control tests with owners, evidence requirements, confidence, and next action |
| `GET`  | `/api/v1/violations`      | open control and asset violations                                             |
| `GET`  | `/api/v1/controls`        | control workbench data                                                        |
| `GET`  | `/api/v1/evidence`        | normalized evidence facts, filterable by any top-level field                  |
| `GET`  | `/api/v1/assets`          | asset risk queue                                                              |
| `GET`  | `/api/v1/snapshots`       | list point-in-time assessment snapshots                                       |
| `POST` | `/api/v1/snapshots`       | create a point-in-time assessment snapshot                                    |

The unversioned `/api/*` routes remain for the bundled console and local
compatibility. Server mode serves the same unversioned surface behind the same
identity and RBAC boundary as `/api/v1/*`.

## Agent Usage

Agents should:

1. read `/api/v1/posture/current` first
2. inspect `/api/v1/control-tests` for evidence requirements, confidence inputs, and next action
3. inspect `/api/v1/violations` for owner/action detail
4. query `/api/v1/controls` for framework context
5. create `/api/v1/snapshots` only when the user asks for an audit, vendor, board,
   incident, or release-gate snapshot

Agents should not infer compliance status from visual text. The API is the
contract.

## Example

```bash
security-lakehouse serve --lake build/lakehouse --port 8787

curl -s http://127.0.0.1:8787/api/v1/posture/current | jq .
curl -s 'http://127.0.0.1:8787/api/v1/control-tests?result=fail&sort=-confidence_score&limit=10' | jq .
curl -s 'http://127.0.0.1:8787/api/v1/violations?severity=critical,high' | jq .
curl -s -X POST http://127.0.0.1:8787/api/v1/snapshots \
  -H 'content-type: application/json' \
  --data '{"reason":"vendor_due_diligence"}' | jq .
```
