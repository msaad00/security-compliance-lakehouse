import { isAuditorMode } from "@/lib/state/auditor";
import type {
  Assessment,
  AssetRisk,
  ConfigurePayload,
  ConnectorRun,
  ConnectorView,
  ControlPosture,
  ControlTest,
  FrameworkView,
  Health,
  NormalizedEvent,
  SnapshotResponse,
  TrackingEvent,
  TriagePayload,
  VerifyResult,
  Violation,
} from "./types";

const BASE = "/api";

function headers(): Record<string, string> {
  const out: Record<string, string> = { "content-type": "application/json" };
  if (isAuditorMode()) out["X-Trust-Role"] = "auditor";
  return out;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store", headers: headers() });
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
  createSnapshot: (reason: string) => post<SnapshotResponse>("/snapshots", { reason }),
  listSnapshots: () =>
    get<{ count: number; snapshots: SnapshotSummary[] }>("/snapshots"),
  getTracking: (violationId: string) =>
    get<{ violation_id: string; current_state: string; events: TrackingEvent[] }>(
      `/violations/${encodeURIComponent(violationId)}/tracking`,
    ),
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
    post<{ run: ConnectorRun }>(`/connectors/${encodeURIComponent(id)}/probe`, {}),
  connectorRuns: (id: string) =>
    get<{ connector_id: string; runs: ConnectorRun[] }>(
      `/connectors/${encodeURIComponent(id)}/runs`,
    ),
  listFrameworks: () =>
    get<{ count: number; frameworks: FrameworkView[] }>("/frameworks"),
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
