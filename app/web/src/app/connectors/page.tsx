"use client";

import { CheckCircle2, Database, Lock, Plug } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/PageHeader";

interface Mode {
  name: string;
  tone: "ready" | "attention" | "info";
  pill: string;
  body: string;
  icon: typeof Plug;
}

const MODES: Mode[] = [
  {
    name: "Existing security lake",
    tone: "ready",
    pill: "recommended",
    body: "Read Snowflake, ClickHouse, object storage, SIEM exports, scanner output, and GRC evidence with scoped read-only roles.",
    icon: Database,
  },
  {
    name: "Managed evidence objects",
    tone: "info",
    pill: "starter mode",
    body: "Create bronze, silver, gold, mart, and snapshot objects when the company does not have an existing normalized lake.",
    icon: Plug,
  },
  {
    name: "Direct tool connectors",
    tone: "attention",
    pill: "controlled",
    body: "Use short-lived tokens or customer-managed service accounts only when the source system is the evidence authority.",
    icon: Lock,
  },
];

const NAMES = [
  "Snowflake",
  "ClickHouse",
  "AWS",
  "GitHub",
  "Okta",
  "Jira",
  "SIEM",
  "Scanner",
  "Runtime",
  "Model Registry",
];

const COLORS = [
  "from-orange-500 to-orange-600",
  "from-slate-700 to-slate-900",
  "from-blue-500 to-blue-700",
  "from-emerald-600 to-emerald-800",
  "from-purple-500 to-purple-700",
];

export default function ConnectorsPage() {
  return (
    <div className="grid gap-5 px-7 py-7">
      <PageHeader
        eyebrow="Connectors"
        title="Read-only first integrations"
        description="The default customer-safe path is read-only credentials into existing evidence stores. Direct connectors are used only when no existing lake-backed source exists."
        actions={
          <span className="rounded-full border border-line bg-white px-3 py-1.5 text-xs font-black text-slate-600">
            <CheckCircle2 className="mr-1 inline h-3 w-3 text-emerald-600" />
            Least-privilege roles
          </span>
        }
      />
      <div className="grid gap-5 lg:grid-cols-3">
        {MODES.map(({ name, tone, pill, body, icon: Icon }) => (
          <Card key={name} className="overflow-hidden">
            <CardHeader>
              <div className="flex items-center gap-3">
                <span className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand to-brand-cyan text-white">
                  <Icon className="h-5 w-5" />
                </span>
                <div>
                  <CardTitle>{name}</CardTitle>
                  <div className="mt-1">
                    <Badge tone={tone}>{pill}</Badge>
                  </div>
                </div>
              </div>
              <CardDescription className="mt-3">{body}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>
      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle>Connector health</CardTitle>
          <CardDescription>
            Inputs that drive assessment confidence. Health metrics arrive in PR 3 (per-source freshness SLA).
          </CardDescription>
        </CardHeader>
        <div className="grid gap-3 p-5 pt-0 sm:grid-cols-2 lg:grid-cols-5">
          {NAMES.map((n, i) => (
            <div key={n} className="rounded-xl border border-line bg-slate-50/40 p-4">
              <div
                className={`mb-3 grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br ${COLORS[i % COLORS.length]} font-black text-white`}
              >
                {n.charAt(0)}
              </div>
              <div className="font-black text-ink">{n}</div>
              <div className="text-xs text-muted">{i < 2 ? "lake object route" : "evidence connector"}</div>
              <div className="mt-2">
                <Badge tone={i < 7 ? "ready" : "attention"}>{i < 7 ? "connected" : "planned"}</Badge>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
