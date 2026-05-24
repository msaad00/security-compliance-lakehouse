"use client";

import { useQuery, type UseQueryOptions } from "@tanstack/react-query";
import { api, bootstrapAssessment } from "./client";
import type { Assessment, ControlTest } from "./types";

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
  const initialData = typeof window !== "undefined" ? bootstrapAssessment() ?? undefined : undefined;
  return useQuery({
    queryKey: ["posture", "current"],
    queryFn: api.posture,
    staleTime: STALE,
    initialData,
    ...opts,
  });
}

export function useControlTests(opts?: Opts<ControlTest[]>) {
  return useQuery({
    queryKey: ["control-tests"],
    queryFn: async () => {
      const r = await api.controlTests();
      return r.control_tests ?? [];
    },
    staleTime: STALE,
    ...opts,
  });
}
