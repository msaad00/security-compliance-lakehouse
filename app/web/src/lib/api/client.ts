import { isAuditorMode } from "@/lib/state/auditor";
import type {
  ActionSpec,
  Assessment,
  AssetRisk,
  AuditLogEntry,
  ComplianceGraph,
  ConfigurePayload,
  ConnectorRun,
  ConnectorView,
  ControlPosture,
  ControlTest,
  ControlArticleMapping,
  Crosswalk,
  FrameworkReadiness,
  FrameworkView,
  ReviewedCrosswalk,
  Health,
  NormalizedEvent,
  SnapshotResponse,
  TrackingEvent,
  TriagePayload,
  TrustShare,
  VerifyResult,
  Violation,
  Workflow,
  WorkflowEdge,
  WorkflowNode,
  WorkflowRun,
} from "./types";

const BASE = "/api";

function headers(): Record<string, string> {
  const out: Record<string, string> = { "content-type": "application/json" };
  if (isAuditorMode()) out["X-Trust-Role"] = "auditor";
  return out;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    cache: "no-store",
    headers: headers(),
  });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return (await res.json()) as T;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    const reason = (payload as { reason?: string }).reason ?? `${res.status}`;
    throw new Error(`${path} -> ${reason}`);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => get<Health>("/healthz"),
  posture: () => get<Assessment>("/posture/current"),
  controls: () => get<{ controls: ControlPosture[] }>("/controls"),
  controlTests: () =>
    get<{ count: number; control_tests: ControlTest[] }>("/control-tests"),
  violations: () =>
    get<{ count: number; violations: Violation[] }>("/violations"),
  evidence: () =>
    get<{ count: number; evidence: NormalizedEvent[] }>("/evidence"),
  assets: () => get<{ assets: AssetRisk[] }>("/assets"),
  createSnapshot: (reason: string) =>
    post<SnapshotResponse>("/snapshots", { reason }),
  listSnapshots: () =>
    get<{ count: number; snapshots: SnapshotSummary[] }>("/snapshots"),
  getTracking: (violationId: string) =>
    get<{
      violation_id: string;
      current_state: string;
      events: TrackingEvent[];
    }>(`/violations/${encodeURIComponent(violationId)}/tracking`),
  triage: (violationId: string, payload: TriagePayload) =>
    post<{ event: TrackingEvent }>(
      `/violations/${encodeURIComponent(violationId)}/triage`,
      payload,
    ),
  verifyEvidence: (eventId: string) =>
    post<VerifyResult>(`/evidence/${encodeURIComponent(eventId)}/verify`, {}),
  listConnectors: () =>
    get<{ count: number; connectors: ConnectorView[] }>("/connectors"),
  configureConnector: (id: string, payload: ConfigurePayload) =>
    post<{ event: Record<string, unknown> }>(
      `/connectors/${encodeURIComponent(id)}/configure`,
      payload,
    ),
  probeConnector: (id: string) =>
    post<{ run: ConnectorRun }>(
      `/connectors/${encodeURIComponent(id)}/probe`,
      {},
    ),
  connectorRuns: (id: string) =>
    get<{ connector_id: string; runs: ConnectorRun[] }>(
      `/connectors/${encodeURIComponent(id)}/runs`,
    ),
  listFrameworks: () =>
    get<{ count: number; frameworks: FrameworkView[] }>("/frameworks"),
  listWorkflows: () =>
    get<{ count: number; workflows: Workflow[] }>("/workflows"),
  getWorkflow: (id: string) =>
    get<Workflow>(`/workflows/${encodeURIComponent(id)}`),
  workflowRuns: (id: string) =>
    get<{ workflow_id: string; runs: WorkflowRun[] }>(
      `/workflows/${encodeURIComponent(id)}/runs`,
    ),
  actionCatalog: () => get<{ actions: ActionSpec[] }>("/workflows/actions"),
  saveWorkflow: (payload: {
    workflow_id?: string;
    name: string;
    description?: string;
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
  }) => post<{ workflow: Workflow }>("/workflows", payload),
  runWorkflow: (id: string) =>
    post<{ run: WorkflowRun }>(`/workflows/${encodeURIComponent(id)}/run`, {}),
  testAction: (node_type: string, params: Record<string, unknown>) =>
    post<{ output: Record<string, unknown> }>("/workflows/actions/run", {
      node_type,
      params,
    }),
  listTrustShares: () =>
    get<{ count: number; shares: TrustShare[] }>("/trust-shares"),
  createTrustShare: (payload: {
    role: "auditor";
    scope?: "posture_full" | "posture_framework";
    framework_id?: string | null;
    expires_in_hours: number;
  }) => post<{ share: TrustShare }>("/trust-shares", payload),
  revokeTrustShare: (share_id: string) =>
    post<{ share: TrustShare }>(
      `/trust-shares/${encodeURIComponent(share_id)}/revoke`,
      {},
    ),
  graph: () => get<ComplianceGraph>("/graph"),
  readiness: () =>
    get<{ count: number; frameworks: FrameworkReadiness[] }>("/readiness"),
  crosswalk: () => get<Crosswalk>("/crosswalk"),
  reviewedCrosswalk: () => get<ReviewedCrosswalk>("/crosswalk/reviewed"),
  mappings: () =>
    get<{ count: number; mappings: ControlArticleMapping[] }>("/mappings"),
  auditLog: (
    opts: { category?: string; actor?: string; limit?: number } = {},
  ): Promise<{ count: number; entries: AuditLogEntry[] }> => {
    const qs = new URLSearchParams();
    if (opts.category) qs.set("category", opts.category);
    if (opts.actor) qs.set("actor", opts.actor);
    if (opts.limit !== undefined) qs.set("limit", String(opts.limit));
    const tail = qs.toString();
    return get<{ count: number; entries: AuditLogEntry[] }>(
      `/audit-log${tail ? `?${tail}` : ""}`,
    );
  },
};

export interface SnapshotSummary {
  snapshot_path: string;
  evaluated_at: string;
  reason: string;
  assessment_hash: string;
  posture_score: number | null;
  open_violation_count: number | null;
  critical_violation_count: number | null;
}

export function bootstrapAssessment(): Assessment | null {
  if (typeof document === "undefined") return null;
  const tag = document.getElementById("app-data");
  if (!tag?.textContent) return null;
  try {
    const data = JSON.parse(tag.textContent);
    if (data && typeof data === "object" && "posture" in data) {
      return data as Assessment;
    }
  } catch {
    return null;
  }
  return null;
}
