# Human And Agent API

The API is designed for humans, dashboards, and coding agents. The route names
describe assessment concepts, not storage implementation details.

## Routes

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/healthz` | service health |
| `GET` | `/api/posture/current` | continuously evaluated posture |
| `GET` | `/api/control-tests` | control tests with owners, evidence requirements, confidence, and next action |
| `GET` | `/api/violations` | open control and asset violations |
| `GET` | `/api/controls` | control workbench data |
| `GET` | `/api/evidence` | normalized evidence facts, optionally filtered by `control_id` |
| `GET` | `/api/assets` | asset risk queue |
| `POST` | `/api/snapshots` | create a point-in-time assessment snapshot |

## Agent Usage

Agents should:

1. read `/api/posture/current` first
2. inspect `/api/control-tests` for evidence requirements, confidence inputs, and next action
3. inspect `/api/violations` for owner/action detail
4. query `/api/controls` for framework context
5. create `/api/snapshots` only when the user asks for an audit, vendor, board,
   incident, or release-gate snapshot

Agents should not infer compliance status from visual text. The API is the
contract.

## Example

```bash
security-lakehouse serve --lake build/lakehouse --port 8787

curl -s http://127.0.0.1:8787/api/posture/current | jq .
curl -s http://127.0.0.1:8787/api/control-tests | jq .
curl -s http://127.0.0.1:8787/api/violations | jq .
curl -s -X POST http://127.0.0.1:8787/api/snapshots \
  -H 'content-type: application/json' \
  --data '{"reason":"vendor_due_diligence"}' | jq .
```
