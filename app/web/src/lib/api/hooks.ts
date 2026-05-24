"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { api, bootstrapAssessment, type SnapshotSummary } from "./client";
import type {
  Assessment,
  AssetRisk,
  ControlPosture,
  ControlTest,
  NormalizedEvent,
  TrackingEvent,
  TriagePayload,
  VerifyResult,
  Violation,
} from "./types";

const STALE = 15_000;

type Opts<T> = Omit<UseQueryOptions<T>, "queryKey" | "queryFn">;

export function useHealth(opts?: Opts<{ ok: boolean }>) {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      try {
        const h = await api.health();
        return { ok: Boolean(h.ok) };
      } catch {
        return { ok: false };
      }
    },
    staleTime: STALE,
    retry: false,
    ...opts,
  });
}

export function usePosture(opts?: Opts<Assessment>) {
  const initialData =
    typeof window !== "undefined" ? (bootstrapAssessment() ?? undefined) : undefined;
  return useQuery({
    queryKey: ["posture", "current"],
    queryFn: api.posture,
    staleTime: STALE,
    initialData,
    ...opts,
  });
}

export function useControls(opts?: Opts<ControlPosture[]>) {
  return useQuery({
    queryKey: ["controls"],
    queryFn: async () => (await api.controls()).controls ?? [],
    staleTime: STALE,
    ...opts,
  });
}

export function useControlTests(opts?: Opts<ControlTest[]>) {
  return useQuery({
    queryKey: ["control-tests"],
    queryFn: async () => (await api.controlTests()).control_tests ?? [],
    staleTime: STALE,
    ...opts,
  });
}

export function useViolations(opts?: Opts<Violation[]>) {
  return useQuery({
    queryKey: ["violations"],
    queryFn: async () => (await api.violations()).violations ?? [],
    staleTime: STALE,
    ...opts,
  });
}

export function useEvidence(opts?: Opts<NormalizedEvent[]>) {
  return useQuery({
    queryKey: ["evidence"],
    queryFn: async () => (await api.evidence()).evidence ?? [],
    staleTime: STALE,
    ...opts,
  });
}

export function useAssets(opts?: Opts<AssetRisk[]>) {
  return useQuery({
    queryKey: ["assets"],
    queryFn: async () => (await api.assets()).assets ?? [],
    staleTime: STALE,
    ...opts,
  });
}

export function useSnapshots(opts?: Opts<SnapshotSummary[]>) {
  return useQuery({
    queryKey: ["snapshots"],
    queryFn: async () => (await api.listSnapshots()).snapshots ?? [],
    staleTime: STALE,
    ...opts,
  });
}

export function useTracking(violationId: string | null) {
  return useQuery({
    queryKey: ["tracking", violationId],
    queryFn: async () => {
      if (!violationId) return { events: [] as TrackingEvent[], current_state: "open" };
      const data = await api.getTracking(violationId);
      return { events: data.events, current_state: data.current_state };
    },
    enabled: Boolean(violationId),
    staleTime: 5_000,
  });
}

export function useTriageMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ violationId, payload }: { violationId: string; payload: TriagePayload }) =>
      api.triage(violationId, payload),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ["tracking", vars.violationId] });
    },
  });
}

export function useVerifyMutation() {
  return useMutation({
    mutationFn: (eventId: string) => api.verifyEvidence(eventId),
  });
}

export function useSnapshotMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (reason: string) => api.createSnapshot(reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["snapshots"] });
    },
  });
}

export type { VerifyResult, TrackingEvent };
