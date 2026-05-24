"use client";

import { ExternalLink, FileLock2, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/PageHeader";
import { usePosture, useControls, useEvidence } from "@/lib/api/hooks";
import { pct } from "@/lib/utils";

export default function TrustCenterPage() {
  const posture = usePosture();
  const controls = useControls();
  const evidence = useEvidence();

  const frameworks = posture.data?.frameworks ?? [];
  const hash = posture.data?.assessment_hash ?? "";

  return (
    <div className="grid gap-5 px-7 py-7">
      <PageHeader
        eyebrow="Trust center"
        title="Security at Acme Co"
        description="Continuously updated compliance posture, controls, evidence references, and point-in-time snapshots for internal stakeholders and approved external reviewers."
        actions={
          <>
            <Button variant="default">
              <ExternalLink className="h-4 w-4" /> Public link
            </Button>
            <Button variant="primary">
              <FileLock2 className="h-4 w-4" /> Request access snapshot
            </Button>
          </>
        }
      />
      <Card className="overflow-hidden bg-gradient-to-br from-blue-50 via-white to-emerald-50">
        <div className="grid gap-5 p-7 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <Badge tone="info">
              <Sparkles className="mr-1 h-3 w-3" /> Read-only, customer-owned data
            </Badge>
            <h2 className="mt-3 text-3xl font-black text-ink">
              Just-in-time compliance for buyers and auditors.
            </h2>
            <p className="mt-3 max-w-prose text-sm text-muted">
              The trust portal exposes the same assessment hash the workbench produces. PR 3 adds a
              role-scoped auditor view that lets external reviewers browse evidence references
              without seeing internal owners or remediation traffic.
            </p>
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Assessment hash</CardTitle>
              <CardDescription>Snapshot signature is recomputed every evaluation.</CardDescription>
            </CardHeader>
            <div className="p-5 pt-0 text-xs">
              <code className="block break-all rounded-lg border border-line bg-slate-50 p-3 text-ink">
                {hash || "…"}
              </code>
            </div>
          </Card>
        </div>
      </Card>
      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle>Compliance</CardTitle>
            <CardDescription>Framework readiness</CardDescription>
          </CardHeader>
          <div className="grid gap-2 p-5 pt-0">
            {frameworks.map((f) => (
              <div key={f.framework} className="rounded-xl border border-line bg-white p-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="font-black text-ink">{f.framework}</div>
                  <Badge tone={f.score > 80 ? "ready" : "attention"}>{pct(f.score)}%</Badge>
                </div>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-brand to-brand-green"
                    style={{ width: `${pct(f.score)}%` }}
                  />
                </div>
              </div>
            ))}
            {frameworks.length === 0 && (
              <div className="rounded-lg border border-dashed border-line p-3 text-xs text-muted">
                No framework scores yet — run the pipeline first.
              </div>
            )}
          </div>
        </Card>
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle>Controls</CardTitle>
            <CardDescription>Latest tested controls</CardDescription>
          </CardHeader>
          <div className="grid gap-2 p-5 pt-0">
            {(controls.data ?? []).slice(0, 5).map((c) => (
              <div
                key={c.control_id}
                className="rounded-xl border border-line bg-white p-3 text-sm"
              >
                <div className="flex items-center justify-between gap-2">
                  <code className="text-xs text-ink">{c.control_id}</code>
                  <Badge tone={c.status === "pass" ? "ready" : "critical"}>{c.status}</Badge>
                </div>
                <div className="mt-1 text-xs text-muted">{c.title}</div>
              </div>
            ))}
          </div>
        </Card>
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle>Resources</CardTitle>
            <CardDescription>Evidence + attestation</CardDescription>
          </CardHeader>
          <div className="grid gap-3 p-5 pt-0 text-sm">
            <div className="rounded-xl border border-line bg-white p-3">
              <div className="text-xs font-black uppercase tracking-wider text-muted">
                Evidence bundle
              </div>
              <div className="mt-1 text-ink">
                <Badge tone="ready">{(evidence.data ?? []).length} records</Badge>
              </div>
            </div>
            <div className="rounded-xl border border-line bg-white p-3">
              <div className="text-xs font-black uppercase tracking-wider text-muted">
                Assessment scope
              </div>
              <div className="mt-1 text-ink">
                {posture.data?.posture?.framework_count ?? 0} frameworks ·{" "}
                {posture.data?.posture?.control_count ?? 0} controls
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
