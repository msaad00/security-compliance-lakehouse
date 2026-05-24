"use client";

import { usePosture, useControlTests } from "@/lib/api/hooks";
import { PostureKpis } from "@/components/dashboard/PostureKpis";
import { FrameworkBars } from "@/components/dashboard/FrameworkBars";
import { EvidenceTrend } from "@/components/dashboard/EvidenceTrend";
import { ControlTestTable } from "@/components/dashboard/ControlTestTable";
import { Badge } from "@/components/ui/badge";

export default function DashboardPage() {
  const posture = usePosture();
  const tests = useControlTests();

  const p = posture.data?.posture;
  const evidenceCount = posture.data?.violations
    ? posture.data.posture.open_violation_count +
      (posture.data.frameworks?.reduce((a, f) => a + f.control_count, 0) ?? 0)
    : 0;

  return (
    <div className="grid gap-5 px-7 py-7">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-[12px] font-black uppercase tracking-wider text-brand">
            Dashboard
          </div>
          <h1 className="mt-1 text-3xl font-black text-ink">
            Assessment workbench
          </h1>
          <p className="mt-2 max-w-[780px] text-sm text-muted">
            Current assessment computed from normalized evidence, control tests,
            source health, and signed snapshots. Every value here is
            deterministic over the gold layer.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge
            tone={
              p?.state === "ready"
                ? "ready"
                : p?.state === "critical"
                  ? "critical"
                  : "attention"
            }
          >
            {p?.state ?? "loading"}
          </Badge>
          <span className="rounded-full border border-line bg-white px-3 py-1.5 text-xs font-black text-slate-600">
            {posture.data?.posture?.framework_count ?? 0} frameworks
          </span>
          <span className="rounded-full border border-line bg-white px-3 py-1.5 text-xs font-black text-slate-600">
            {posture.data?.posture?.control_count ?? 0} controls
          </span>
        </div>
      </div>

      <PostureKpis posture={posture.data} evidenceCount={evidenceCount} />

      <div className="grid gap-5 lg:grid-cols-2">
        <EvidenceTrend currentScore={Math.round(p?.score ?? 0)} />
        <FrameworkBars frameworks={posture.data?.frameworks ?? []} />
      </div>

      <ControlTestTable rows={tests.data ?? []} />
    </div>
  );
}
