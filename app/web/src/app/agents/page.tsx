"use client";

import { Bot, Copy } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/PageHeader";

interface Route {
  method: "GET" | "POST";
  path: string;
  description: string;
  scope: "posture" | "controls" | "evidence" | "assets" | "snapshots";
}

const ROUTES: Route[] = [
  { method: "GET", path: "/api/posture/current", description: "Continuously refreshed assessment posture, frameworks, violations, top risk assets.", scope: "posture" },
  { method: "GET", path: "/api/control-tests", description: "Live control test results with owner, confidence, freshness.", scope: "controls" },
  { method: "GET", path: "/api/violations", description: "Open control failures (severity sorted). Supports framework/control_id filters.", scope: "controls" },
  { method: "GET", path: "/api/controls", description: "Control posture catalog. Supports control_id filter.", scope: "controls" },
  { method: "GET", path: "/api/evidence", description: "Silver-layer normalized evidence facts. Supports control_id filter.", scope: "evidence" },
  { method: "GET", path: "/api/assets", description: "Asset risk roll-up: owner, environment, severity counts.", scope: "assets" },
  { method: "POST", path: "/api/snapshots", description: "Freeze a point-in-time assessment snapshot. Body: { reason }.", scope: "snapshots" },
  { method: "GET", path: "/api/healthz", description: "Server liveness.", scope: "posture" },
];

const SCOPE_TONE: Record<Route["scope"], "ready" | "info" | "attention" | "critical" | "default"> = {
  posture: "info",
  controls: "ready",
  evidence: "info",
  assets: "attention",
  snapshots: "critical",
};

export default function AgentsPage() {
  return (
    <div className="grid gap-5 px-7 py-7">
      <PageHeader
        eyebrow="Agent API"
        title="JSON contracts for SOC analysts, framework specialists, and remediation agents."
        description="The same contracts the console uses. Hand them to your agents; assessment snapshots and posture stay deterministic."
        actions={
          <Badge tone="info">
            <Bot className="mr-1 h-3 w-3" /> Designed for agent + human use
          </Badge>
        }
      />
      <div className="grid gap-3 lg:grid-cols-2">
        {ROUTES.map((r) => (
          <Card key={r.path} className="overflow-hidden">
            <CardHeader>
              <CardTitle className="flex flex-wrap items-center gap-2 text-base">
                <Badge tone={r.method === "POST" ? "critical" : "ready"}>{r.method}</Badge>
                <code className="text-sm text-ink">{r.path}</code>
              </CardTitle>
              <CardDescription>{r.description}</CardDescription>
            </CardHeader>
            <div className="flex items-center justify-between gap-2 border-t border-line p-3 text-xs">
              <Badge tone={SCOPE_TONE[r.scope]}>{r.scope}</Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigator.clipboard.writeText(r.path)}
              >
                <Copy className="h-3 w-3" /> Copy path
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
