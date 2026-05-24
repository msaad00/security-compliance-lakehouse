// Wire types mirror security_lakehouse/assessment.py and gold/*.jsonl.

export interface FrameworkPosture {
  framework: string;
  score: number;
  state: "ready" | "attention_required";
  control_count: number;
  failing_control_count: number;
  violation_count: number;
  stale_control_count: number;
  critical_violation_count: number;
  high_violation_count: number;
}

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export interface Violation {
  violation_id: string;
  control_id: string;
  event_id: string;
  asset_id: string;
  asset_owner: string;
  environment: string;
  source: string;
  event_type: string;
  severity: Severity;
  severity_score: number;
  state: string;
  evidence_ref: string;
  raw_sha256: string;
  detected_at: string;
}

export interface PostureBlock {
  score: number;
  state: "ready" | "attention_required" | "critical";
  framework_count: number;
  control_count: number;
  asset_count: number;
  open_violation_count: number;
  critical_violation_count: number;
  high_violation_count: number;
  stale_control_count: number;
}

export interface AssetRisk {
  asset_id: string;
  asset_owner: string;
  asset_type: string;
  environment: string;
  risk_score: number;
  critical_open: number;
  high_open: number;
}

export interface Assessment {
  schema_version: string;
  assessment_type: string;
  evaluated_at: string;
  freshness_days: number;
  posture: PostureBlock;
  frameworks: FrameworkPosture[];
  violations: Violation[];
  top_risk_assets: AssetRisk[];
  stale_controls: string[];
  assessment_hash: string;
}

export interface ControlPosture {
  control_id: string;
  framework: string;
  status: "pass" | "fail" | "warn" | string;
  title: string;
  owner: string;
  risk_score: number;
  evidence_count: number;
  event_count: number;
}

export interface ControlTest {
  control_id: string;
  name: string;
  result: "pass" | "fail" | "warn" | string;
  status: string;
  owner: string;
  confidence_score: number;
  agent_skill: string;
  freshness_status: string;
  next_action: string;
}

export interface NormalizedEvent {
  event_id: string;
  event_time: string;
  source: string;
  status: string;
  severity: Severity;
  asset_id: string;
  asset_owner: string;
  evidence_ref: string;
  evidence_id: string;
  control_ids: string[];
  evidence_collected_at: string;
}

export interface Health {
  ok: boolean;
  service: string;
}

export interface SnapshotResponse {
  snapshot_path: string;
  reason: string;
}

export type TrackingState =
  | "open"
  | "triaged"
  | "in_progress"
  | "resolved"
  | "dismissed";

export interface TrackingEvent {
  tracking_id: string;
  violation_id: string;
  actor: string;
  state: TrackingState;
  assignee: string | null;
  due_at: string | null;
  note: string | null;
  occurred_at: string;
}

export interface TriagePayload {
  state: TrackingState;
  actor?: string;
  assignee?: string;
  due_at?: string;
  note?: string;
}

export interface VerifyResult {
  event_id: string;
  verified: boolean;
  expected_sha256: string | null;
  computed_sha256: string | null;
  source_layer: "bronze" | "missing";
  reason: string | null;
}
