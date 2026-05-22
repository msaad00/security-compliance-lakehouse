# ASCII System Map

```text
                 +----------------------+
                 |  Existing Evidence   |
                 | SIEM / Cloud / IdP   |
                 | Scanners / Tickets   |
                 +----------+-----------+
                            |
                            v
               +------------+-------------+
               | Normalized Evidence Model|
               | asset + control + hash   |
               +------------+-------------+
                            |
              +-------------+--------------+
              |                            |
              v                            v
   +----------+-----------+     +----------+-----------+
   | Control Evaluation   |     | Lake Adapters        |
   | score / pass / fail  |     | Snowflake/ClickHouse |
   +----------+-----------+     +----------+-----------+
              |                            |
              v                            v
   +----------+-----------+     +----------+-----------+
   | Current Posture      |     | Analytics + Evidence |
   | violations / owners  |     | views / tables       |
   +----------+-----------+     +----------+-----------+
              |
              v
   +----------+-----------+
   | Snapshot Service     |
   | audit / vendor / JIT |
   +----------+-----------+
              |
              v
   +----------+-----------+
   | Human + Agent API    |
   | UI / CLI / Skills    |
   +----------------------+
```
