import { isAuditorMode } from "@/lib/state/auditor";
import type {
  ActionSpec,
  Assessment,
  AssetRisk,
  AuthMethods,
  ControlExceptionItem,
  EvidenceRequestItem,
  RemediationTask,
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
const LOGIN_PATH = "/console/login";

function redirectToLogin(): void {
  if (typeof window === "undefined") return;
  const pathname = window.location.pathname.replace(/\/$/, "");
  if (pathname === LOGIN_PATH) return;
  const returnTo = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  window.location.assign(
    `${LOGIN_PATH}?return_to=${encodeURIComponent(returnTo)}`,
  );
}

function headers(): Record<string, string> {
  const out: Record<string, string> = { "content-type": "application/json" };
  if (isAuditorMode()) out["X-Trust-Role"] = "auditor";
  return out;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    cache: "no-store",
    credentials: "same-origin",
    headers: headers(),
  });
  if (res.status === 401) redirectToLogin();
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return (await res.json()) as T;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    credentials: "same-origin",
    headers: headers(),
    body: JSON.stringify(body ?? {}),
  });
  if (res.status === 401) redirectToLogin();
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    const reason = (payload as { reason?: string }).reason ?? `${res.status}`;
    throw new Error(`${path} -> ${reason}`);
  }
  return (await res.json()) as T;
}

async function mutate<T>(
  path: string,
  method: "PATCH" | "DELETE",
  body?: unknown,
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    credentials: "same-origin",
    headers: headers(),
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (res.status === 401) redirectToLogin();
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    const reason = (payload as { reason?: string }).reason ?? `${res.status}`;
    throw new Error(`${path} -> ${reason}`);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => get<Health>("/healthz"),
  authMethods: () =>
    get<{ data: AuthMethods }>("/v1/auth/methods").then((body) => body.data),
  remediationTasks: (query = "") =>
    get<{ data: RemediationTask[] }>(`/v1/remediation/tasks${query}`).then(
      (b) => b.data,
    ),
  createRemediationTask: (
    payload: Partial<RemediationTask> & { title: string },
  ) =>
    post<{ data: RemediationTask }>("/v1/remediation/tasks", payload).then(
      (b) => b.data,
    ),
  updateRemediationTask: (id: string, payload: Record<string, unknown>) =>
    mutate<{ data: RemediationTask }>(
      `/v1/remediation/tasks/${encodeURIComponent(id)}`,
      "PATCH",
      payload,
    ).then((b) => b.data),
  evidenceRequests: () =>
    get<{ data: EvidenceRequestItem[] }>(
      "/v1/remediation/evidence-requests",
    ).then((b) => b.data),
  createEvidenceRequest: (payload: {
    control_id: string;
    requested_from?: string;
    note?: string;
  }) =>
    post<{ data: EvidenceRequestItem }>(
      "/v1/remediation/evidence-requests",
      payload,
    ).then((b) => b.data),
  setEvidenceRequestStatus: (id: string, status: string) =>
    mutate<{ data: EvidenceRequestItem }>(
      `/v1/remediation/evidence-requests/${encodeURIComponent(id)}`,
      "PATCH",
      { status },
    ).then((b) => b.data),
  controlExceptions: () =>
    get<{ data: ControlExceptionItem[] }>("/v1/remediation/exceptions").then(
      (b) => b.data,
    ),
  createControlException: (payload: {
    control_id: string;
    reason?: string;
    expires_at?: string | null;
  }) =>
    post<{ data: ControlExceptionItem }>(
      "/v1/remediation/exceptions",
      payload,
    ).then((b) => b.data),
  revokeControlException: (id: string) =>
    mutate<{ data: ControlExceptionItem }>(
      `/v1/remediation/exceptions/${encodeURIComponent(id)}`,
      "DELETE",
    ).then((b) => b.data),
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
  repoGraph: () => get<ComplianceGraph>("/repo-graph"),
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
