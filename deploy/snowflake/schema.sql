-- Snowflake schema for the governed security evidence lake.
-- Load artifacts from build/lakehouse into these tables with COPY INTO, Snowpipe,
-- dbt seeds, or a small Python loader.

create database if not exists SECURITY_COMPLIANCE_LAKEHOUSE;
use database SECURITY_COMPLIANCE_LAKEHOUSE;

create schema if not exists SECURITY_BRONZE;
create schema if not exists SECURITY_SILVER;
create schema if not exists SECURITY_GOLD;

create table if not exists SECURITY_BRONZE.RAW_EVENTS (
  ingested_at timestamp_tz not null,
  raw_sha256 string not null,
  raw variant not null,
  loaded_at timestamp_tz default current_timestamp(),
  primary key (raw_sha256)
);

create table if not exists SECURITY_SILVER.NORMALIZED_EVENTS (
  event_id string not null,
  tenant_id string not null,
  event_time timestamp_tz not null,
  source string not null,
  event_type string not null,
  asset_id string not null,
  asset_type string not null,
  asset_owner string not null,
  environment string not null,
  severity string not null,
  severity_score number not null,
  status string not null,
  control_ids array not null,
  evidence_id string not null,
  evidence_ref string not null,
  evidence_collected_at timestamp_tz,
  raw_sha256 string not null,
  loaded_at timestamp_tz default current_timestamp(),
  primary key (event_id)
);

create table if not exists SECURITY_GOLD.CONTROL_POSTURE (
  control_id string not null,
  framework string not null,
  title string not null,
  risk_domain string not null,
  owner string not null,
  status string not null,
  risk_score number not null,
  event_count number not null,
  open_event_count number not null,
  evidence_count number not null,
  evidence_coverage float not null,
  latest_event_time timestamp_tz not null,
  loaded_at timestamp_tz default current_timestamp(),
  primary key (control_id)
);

create table if not exists SECURITY_GOLD.ASSET_RISK (
  asset_id string not null,
  asset_type string not null,
  asset_owner string not null,
  environment string not null,
  risk_score number not null,
  critical_open number not null,
  high_open number not null,
  event_count number not null,
  latest_event_time timestamp_tz not null,
  loaded_at timestamp_tz default current_timestamp(),
  primary key (asset_id)
);

create or replace view SECURITY_GOLD.AUDITOR_CONTROL_EVIDENCE as
select
  c.framework,
  c.control_id,
  c.title,
  c.status as control_status,
  c.risk_score,
  e.event_time,
  e.source,
  e.event_type,
  e.asset_id,
  e.severity,
  e.status as event_status,
  e.evidence_ref,
  e.raw_sha256
from SECURITY_GOLD.CONTROL_POSTURE c
join SECURITY_SILVER.NORMALIZED_EVENTS e
  on array_contains(c.control_id::variant, e.control_ids);

create or replace view SECURITY_GOLD.EXECUTIVE_RISK_SUMMARY as
select
  framework,
  count(*) as controls,
  count_if(status = 'fail') as failing_controls,
  round(avg(risk_score), 2) as avg_risk_score,
  round(avg(evidence_coverage), 4) as avg_evidence_coverage
from SECURITY_GOLD.CONTROL_POSTURE
group by framework
order by avg_risk_score desc;
