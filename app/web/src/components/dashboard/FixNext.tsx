"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { Violation } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const SEVERITY_TONE: Record<
  string,
  "critical" | "attention" | "info" | "default"
> = {
  critical: "critical",
  high: "attention",
  medium: "info",
  low: "default",
  info: "default",
};

export function FixNext({ violations }: { violations: Violation[] }) {
  const top = [...violations]
    .sort((a, b) => b.severity_score - a.severity_score)
    .slice(0, 6);

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle>Fix next</CardTitle>
        <CardDescription>
          Highest-severity open violations — the fastest path to a better score.
        </CardDescription>
      </CardHeader>
      <div className="divide-y divide-line border-t border-line">
        {top.length === 0 && (
          <div className="px-5 py-6 text-sm text-muted">
            No open violations. Posture is clean.
          </div>
        )}
        {top.map((v) => (
          <Link
            key={v.violation_id}
            href="/violations"
            className="flex items-center gap-3 px-5 py-3 transition-colors hover:bg-slate-50"
          >
            <Badge tone={SEVERITY_TONE[v.severity] ?? "default"}>
              {v.severity}
            </Badge>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-black text-ink">
                {v.control_id}
              </div>
              <div className="truncate text-[11px] text-muted">
                {v.source} · {v.event_type} · {v.environment}
              </div>
            </div>
            <ArrowRight className="h-4 w-4 shrink-0 text-muted" />
          </Link>
        ))}
      </div>
    </Card>
  );
}
