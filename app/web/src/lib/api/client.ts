import type {
  Assessment,
  AssetRisk,
  ControlPosture,
  ControlTest,
  Health,
  NormalizedEvent,
  SnapshotResponse,
  Violation,
} from "./types";

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
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
  createSnapshot: async (reason: string): Promise<SnapshotResponse> => {
    const res = await fetch(`${BASE}/snapshots`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ reason }),
    });
    if (!res.ok) throw new Error(`snapshot -> ${res.status}`);
    return (await res.json()) as SnapshotResponse;
  },
};

// Offline render path: dashboard.py embeds the full assessment in
// <script id="app-data" type="application/json">…</script> so the React app
// can hydrate without the API server running.
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
