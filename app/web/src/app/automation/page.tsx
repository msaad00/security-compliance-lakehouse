"use client";

import { useState } from "react";
import { Sparkles, Workflow } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/PageHeader";
import { useControlTests, useAssets } from "@/lib/api/hooks";

const MODULES = [
  "enterprise grc",
  "compliance automation",
  "trust center",
  "questionnaire automation",
  "third-party risk",
];

const toneFor = (result: string) =>
  result === "pass" ? "ready" : result === "fail" ? "critical" : "attention";

export default function AutomationPage() {
  const tests = useControlTests();
  const assets = useAssets();
  const [active, setActive] = useState(MODULES[1]);
  const firstAsset = (assets.data ?? [])[0];

  return (
    <div className="grid gap-5 px-7 py-7">
      <PageHeader
        eyebrow="Automation"
        title="Continuous trust management"
        description="Collect evidence automatically, monitor controls continuously, and create remediation tasks from failing tests. Agents can read the same API contracts humans use in the console."
      />
      <Card className="overflow-hidden bg-slate-950 text-slate-100">
        <div className="flex flex-wrap gap-2 border-b border-railLine p-3">
          {MODULES.map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setActive(m)}
              className={[
                "rounded-md px-3 py-2 text-xs font-black uppercase tracking-wide transition-colors",
                m === active
                  ? "bg-brand text-slate-950"
                  : "text-slate-300 hover:bg-slate-800",
              ].join(" ")}
            >
              {m}
            </button>
          ))}
        </div>
        <div className="grid gap-5 p-5 lg:grid-cols-[minmax(0,1fr)_minmax(360px,1fr)]">
          <div>
            <div className="text-[12px] font-black uppercase tracking-wider text-brand-cyan">
              Initiate launch
            </div>
            <h2 className="mt-2 text-3xl font-black">
              Engage continuous compliance on autopilot.
            </h2>
            <p className="mt-3 max-w-prose text-sm text-slate-300">
              Live control tests fire on every silver-layer evidence update. PR 3 wires interactive
              workflow building, where you compose triggers, evidence checks, owner routing, and
              snapshot actions.
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              <Button variant="primary">Open control workbench</Button>
              <Button variant="dark">Compose workflow</Button>
            </div>
          </div>
          <Card className="overflow-hidden">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Workflow className="h-4 w-4 text-brand" /> Continuous control monitoring
              </CardTitle>
              <CardDescription>Live control test queue</CardDescription>
            </CardHeader>
            <div className="grid gap-2 p-5 pt-0">
              {(tests.data ?? []).map((t) => (
                <div
                  key={t.control_id}
                  className="flex items-center justify-between rounded-lg border border-line bg-white p-2.5 text-xs"
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={t.result === "pass"}
                      readOnly
                      className="h-4 w-4 rounded border-line accent-brand"
                    />
                    <span className="font-extrabold text-ink">{t.name}</span>
                  </div>
                  <Badge tone={toneFor(t.result)}>{t.status}</Badge>
                </div>
              ))}
              {(tests.data ?? []).length === 0 && (
                <div className="rounded-lg border border-dashed border-line p-3 text-xs text-muted">
                  No control tests reported yet.
                </div>
              )}
            </div>
          </Card>
        </div>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-brand" /> AI control test summary
          </CardTitle>
          <CardDescription>
            Resource: <code className="text-ink">{firstAsset?.asset_id ?? "n/a"}</code> · cause:
            failing control evidence in the lake. Suggested next step: open ticket, attach evidence,
            request owner attestation.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
