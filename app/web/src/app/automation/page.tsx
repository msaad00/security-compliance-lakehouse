"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, Construction, ShieldCheck, Workflow } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/PageHeader";
import { useControlTests } from "@/lib/api/hooks";

const toneFor = (result: string) =>
  result === "pass" ? "ready" : result === "fail" ? "critical" : "attention";

export default function AutomationPage() {
  const tests = useControlTests();
  const [stateFilter, setStateFilter] = useState<"all" | "pass" | "fail">("all");

  const rows = (tests.data ?? []).filter(
    (t) => stateFilter === "all" || t.result === stateFilter,
  );

  return (
    <div className="grid gap-5 px-7 py-7">
      <PageHeader
        eyebrow="Workflows"
        title="Continuous control monitoring"
        description="Every silver-layer evidence update re-runs the control tests below. The DAG editor for triggers, evidence checks, owner routing, and snapshot actions ships in the next release — for now use this view to inspect what runs on every update."
        actions={
          <Badge tone="info">
            <Workflow className="mr-1 h-3 w-3" /> {tests.data?.length ?? 0} live tests
          </Badge>
        }
      />

      <Card className="overflow-hidden border-dashed bg-slate-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Construction className="h-4 w-4 text-amber-600" /> Workflow canvas — coming next release
          </CardTitle>
          <CardDescription>
            Drag-and-drop DAG editor with trigger / evidence-check / owner-route / snapshot nodes, per-node
            schemas, live action testing, versioned stories, and a template library. Persisted to{" "}
            <code>gold/workflows.jsonl</code> via <code>POST /api/workflows</code>.
          </CardDescription>
        </CardHeader>
      </Card>

      <Card className="overflow-hidden">
        <CardHeader>
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <CardTitle>Live control test queue</CardTitle>
              <CardDescription>
                Each row is the latest evaluation against the gold layer. Click a row to inspect the control in
                the workbench.
              </CardDescription>
            </div>
            <select
              value={stateFilter}
              onChange={(e) => setStateFilter(e.target.value as typeof stateFilter)}
              className="rounded-lg border border-line bg-white px-3 py-2 text-sm font-extrabold focus:outline-none focus:ring-1 focus:ring-brand"
            >
              <option value="all">All results</option>
              <option value="pass">Pass</option>
              <option value="fail">Fail</option>
            </select>
          </div>
        </CardHeader>
        <div className="grid gap-2 p-5 pt-0">
          {rows.length === 0 && (
            <div className="rounded-lg border border-dashed border-line p-4 text-sm text-muted">
              No control tests match the current filter.
            </div>
          )}
          {rows.map((t) => (
            <Link
              key={t.control_id}
              href={`/controls?id=${encodeURIComponent(t.control_id)}`}
              className="grid grid-cols-[auto_minmax(0,1fr)_auto_auto] items-center gap-3 rounded-xl border border-line bg-white p-3 text-sm transition-colors hover:border-brand hover:shadow-card"
            >
              <input
                type="checkbox"
                checked={t.result === "pass"}
                readOnly
                className="h-4 w-4 rounded border-line accent-brand"
              />
              <div className="min-w-0">
                <div className="truncate font-black text-ink">{t.name}</div>
                <div className="mt-0.5 text-xs text-muted">
                  {t.control_id} · {t.next_action}
                </div>
              </div>
              <Badge tone={toneFor(t.result)}>{t.result}</Badge>
              <ArrowRight className="h-4 w-4 text-muted" />
            </Link>
          ))}
        </div>
      </Card>

      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldCheck className="h-4 w-4 text-emerald-600" /> Evaluation pipeline
          </CardTitle>
          <CardDescription>
            Every test runs deterministically over the same silver layer. Identical evidence yields identical
            posture — agents and humans see the same gold-layer truth.
          </CardDescription>
        </CardHeader>
        <div className="grid gap-2 p-5 pt-0 lg:grid-cols-4">
          {[
            { name: "Ingest", body: "Connector lands raw evidence to bronze with SHA-256." },
            { name: "Normalize", body: "Silver layer maps records to OCSF + AI extensions." },
            { name: "Evaluate", body: "Each control runs its CEL/Rego rule against silver." },
            { name: "Materialize", body: "Gold layer emits (control × asset × time) results." },
          ].map((s, i) => (
            <div key={s.name} className="rounded-xl border border-line bg-white p-4">
              <div className="text-[11px] font-black uppercase tracking-wide text-muted">step {i + 1}</div>
              <div className="mt-1 text-sm font-black text-ink">{s.name}</div>
              <div className="mt-1 text-xs text-muted">{s.body}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
