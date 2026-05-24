"use client";

import { useMemo, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/PageHeader";
import { Toolbar, matchesQuery } from "@/components/Toolbar";
import { useControls, useControlTests, usePosture } from "@/lib/api/hooks";
import { useToolbar } from "@/lib/state/filters";
import { cn } from "@/lib/utils";
import type { ControlPosture } from "@/lib/api/types";

const toneForStatus = (status: string) =>
  status === "pass" ? "ready" : status === "fail" ? "critical" : "attention";

function ControlRow({
  control,
  active,
  onSelect,
  confidence,
}: {
  control: ControlPosture;
  active: boolean;
  onSelect: () => void;
  confidence?: number;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "block w-full rounded-xl border bg-white p-3 text-left transition-colors",
        active ? "border-ink shadow-card" : "border-line hover:border-brand",
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <code className="text-sm font-black text-ink">{control.control_id}</code>
        <Badge tone={toneForStatus(control.status)}>{control.status}</Badge>
      </div>
      <div className="mt-1 text-sm text-ink">{control.title}</div>
      <div className="mt-2 flex flex-wrap gap-1.5">
        <Badge>{control.framework}</Badge>
        <Badge>{control.owner}</Badge>
        <Badge tone={Number(control.risk_score) >= 80 ? "critical" : "default"}>
          risk {control.risk_score}
        </Badge>
        <Badge>
          evidence {control.evidence_count}/{control.event_count}
        </Badge>
        {confidence !== undefined && (
          <Badge tone={confidence >= 75 ? "ready" : "attention"}>test {confidence}%</Badge>
        )}
      </div>
    </button>
  );
}

export default function ControlsPage() {
  const controls = useControls();
  const tests = useControlTests();
  const posture = usePosture();
  const { filters, setFilters } = useToolbar();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const frameworks = useMemo(
    () => Array.from(new Set((controls.data ?? []).map((c) => c.framework))),
    [controls.data],
  );

  const filtered = useMemo(
    () =>
      (controls.data ?? []).filter(
        (c) =>
          (filters.framework === "all" || c.framework === filters.framework) &&
          matchesQuery(c, filters.query),
      ),
    [controls.data, filters],
  );

  const selected =
    (controls.data ?? []).find((c) => c.control_id === selectedId) ?? filtered[0] ?? null;

  const violations = useMemo(
    () =>
      (posture.data?.violations ?? []).filter(
        (v) => selected && v.control_id === selected.control_id,
      ),
    [posture.data, selected],
  );

  const testForSelected = (tests.data ?? []).find(
    (t) => selected && t.control_id === selected.control_id,
  );

  return (
    <div className="grid gap-5 px-7 py-7">
      <PageHeader
        eyebrow="Controls"
        title="Control workbench"
        description="Per-framework control catalog. Select a control to inspect its evidence coverage, owner, and open violations. Drill-through editing arrives in PR 3."
      />
      <Toolbar
        filters={filters}
        frameworks={frameworks}
        onChange={setFilters}
        placeholder="Search by control id, title, framework, owner…"
      />
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle>{filtered.length} controls</CardTitle>
            <CardDescription>
              Click a control to inspect evidence, violations, owner, and API-safe facts.
            </CardDescription>
          </CardHeader>
          <div className="grid gap-2 p-5 pt-0">
            {filtered.length === 0 && (
              <div className="rounded-lg border border-dashed border-line p-4 text-sm text-muted">
                No controls match the current filters.
              </div>
            )}
            {filtered.map((c) => {
              const t = (tests.data ?? []).find((x) => x.control_id === c.control_id);
              return (
                <ControlRow
                  key={c.control_id}
                  control={c}
                  active={selected?.control_id === c.control_id}
                  onSelect={() => setSelectedId(c.control_id)}
                  confidence={t?.confidence_score}
                />
              );
            })}
          </div>
        </Card>
        <Card className="sticky top-5 self-start overflow-hidden">
          <CardHeader>
            <CardTitle>Control detail</CardTitle>
            <CardDescription>
              {selected ? selected.control_id : "Select a control to inspect"}
            </CardDescription>
          </CardHeader>
          {selected ? (
            <div className="grid gap-4 p-5 pt-0 text-sm">
              {testForSelected && (
                <div className="rounded-xl border border-line bg-slate-50/60 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <b>{testForSelected.name}</b>
                    <Badge tone={toneForStatus(testForSelected.result)}>
                      {testForSelected.status}
                    </Badge>
                  </div>
                  <div className="mt-1 text-xs text-muted">{testForSelected.next_action}</div>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    <Badge>{testForSelected.agent_skill}</Badge>
                    <Badge tone="info">{testForSelected.freshness_status}</Badge>
                    <Badge tone={testForSelected.confidence_score >= 75 ? "ready" : "attention"}>
                      confidence {testForSelected.confidence_score}%
                    </Badge>
                  </div>
                </div>
              )}
              <dl className="grid grid-cols-[120px_1fr] gap-x-3 gap-y-1.5 text-sm">
                <dt className="text-muted">Framework</dt>
                <dd className="font-extrabold">{selected.framework}</dd>
                <dt className="text-muted">Owner</dt>
                <dd className="font-extrabold">{selected.owner}</dd>
                <dt className="text-muted">Status</dt>
                <dd className="font-extrabold">{selected.status}</dd>
                <dt className="text-muted">Risk</dt>
                <dd className="font-extrabold">{selected.risk_score}</dd>
                <dt className="text-muted">Evidence</dt>
                <dd className="font-extrabold">
                  {selected.evidence_count}/{selected.event_count}
                </dd>
              </dl>
              <div>
                <div className="mb-2 text-xs font-black uppercase tracking-wide text-muted">
                  Open violations · {violations.length}
                </div>
                <div className="grid gap-2">
                  {violations.length === 0 && (
                    <div className="rounded-lg border border-dashed border-line p-3 text-xs text-muted">
                      No open violations linked to this control.
                    </div>
                  )}
                  {violations.map((v) => (
                    <div key={v.violation_id} className="rounded-lg border border-line p-3">
                      <code className="text-xs text-ink">{v.event_id}</code>
                      <div className="mt-1 text-xs text-muted">{v.asset_id}</div>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        <Badge
                          tone={v.severity === "critical" ? "critical" : "attention"}
                        >
                          {v.severity}
                        </Badge>
                        <Badge>{v.asset_owner}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-5 pt-0 text-sm text-muted">
              <ShieldCheck className="mb-2 inline h-4 w-4" /> No control selected.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
