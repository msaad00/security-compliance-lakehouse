-- ClickHouse schema for high-volume security telemetry analytics.
-- The tables mirror the local gold/silver artifacts and are optimized for
-- time-window investigations, dashboard aggregates, and runtime event analytics.

create database if not exists security;

create table if not exists security.normalized_events
(
  event_id String,
  tenant_id LowCardinality(String),
  event_time DateTime64(3, 'UTC'),
  source LowCardinality(String),
  event_type LowCardinality(String),
  asset_id String,
  asset_type LowCardinality(String),
  asset_owner LowCardinality(String),
  environment LowCardinality(String),
  severity LowCardinality(String),
  severity_score UInt8,
  status LowCardinality(String),
  control_ids Array(String),
  evidence_id String,
  evidence_ref String,
  evidence_collected_at DateTime64(3, 'UTC'),
  raw_sha256 FixedString(64)
)
engine = MergeTree
partition by toYYYYMM(event_time)
order by (tenant_id, event_time, source, event_type, asset_id)
ttl event_time + interval 730 day;

create table if not exists security.control_posture
(
  control_id String,
  framework LowCardinality(String),
  title String,
  risk_domain LowCardinality(String),
  owner LowCardinality(String),
  status LowCardinality(String),
  risk_score UInt8,
  event_count UInt64,
  open_event_count UInt64,
  evidence_count UInt64,
  evidence_coverage Float32,
  latest_event_time DateTime64(3, 'UTC'),
  loaded_at DateTime64(3, 'UTC') default now64(3)
)
engine = ReplacingMergeTree(loaded_at)
order by (framework, control_id);

create table if not exists security.asset_risk
(
  asset_id String,
  asset_type LowCardinality(String),
  asset_owner LowCardinality(String),
  environment LowCardinality(String),
  risk_score UInt8,
  critical_open UInt64,
  high_open UInt64,
  event_count UInt64,
  latest_event_time DateTime64(3, 'UTC'),
  loaded_at DateTime64(3, 'UTC') default now64(3)
)
engine = ReplacingMergeTree(loaded_at)
order by (environment, asset_owner, asset_id);

create view if not exists security.runtime_policy_metrics as
select
  tenant_id,
  toStartOfHour(event_time) as hour,
  count() as runtime_events,
  countIf(status in ('blocked', 'failed')) as blocked_events,
  round(blocked_events / runtime_events, 4) as block_rate
from security.normalized_events
where startsWith(event_type, 'runtime.')
group by tenant_id, hour
order by hour desc;
