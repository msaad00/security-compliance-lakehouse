"use client";

import { useQuery, type UseQueryOptions } from "@tanstack/react-query";
import { api, bootstrapAssessment } from "./client";
import type {
  Assessment,
  AssetRisk,
  ControlPosture,
  ControlTest,
  NormalizedEvent,
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
