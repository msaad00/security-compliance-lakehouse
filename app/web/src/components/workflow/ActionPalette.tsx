"use client";

import { useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { ActionSpec } from "@/lib/api/types";

interface Props {
  catalog: ActionSpec[];
  onAdd: (spec: ActionSpec) => void;
}

const KIND_ORDER: ActionSpec["kind"][] = ["trigger", "check", "action"];

const KIND_LABEL: Record<ActionSpec["kind"], string> = {
  trigger: "Triggers",
  check: "Checks",
  action: "Actions",
};

const KIND_TONE: Record<ActionSpec["kind"], "info" | "attention" | "ready"> = {
  trigger: "info",
  check: "attention",
  action: "ready",
};

export function ActionPalette({ catalog, onAdd }: Props) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!query) return catalog;
    const lower = query.toLowerCase();
    return catalog.filter((a) =>
      `${a.label} ${a.description} ${a.node_type}`.toLowerCase().includes(lower),
    );
  }, [catalog, query]);

  const byKind = (kind: ActionSpec["kind"]) =>
    filtered.filter((a) => a.kind === kind);

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle>Action library</CardTitle>
        <CardDescription>Click any action to drop it into the canvas.</CardDescription>
      </CardHeader>
      <div className="px-5 pb-3">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search actions…"
            className="w-full rounded-lg border border-line bg-white py-2 pl-9 pr-3 text-xs focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>
      </div>
      <div className="grid gap-4 p-5 pt-0">
        {KIND_ORDER.map((kind) => (
          <section key={kind}>
            <div className="mb-2 text-[11px] font-black uppercase tracking-wide text-muted">
              {KIND_LABEL[kind]}
            </div>
            <div className="grid gap-2">
              {byKind(kind).map((action) => (
                <button
                  key={action.node_type}
                  type="button"
                  onClick={() => onAdd(action)}
                  className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-start gap-3 rounded-lg border border-line bg-white px-3 py-2 text-left transition-colors hover:border-brand hover:shadow-card"
                >
                  <span
                    className={[
                      "mt-0.5 grid h-7 w-7 place-items-center rounded-md text-[11px] font-black uppercase",
                      KIND_TONE[kind] === "info"
                        ? "bg-blue-50 text-blue-700"
                        : KIND_TONE[kind] === "attention"
                          ? "bg-amber-50 text-amber-700"
                          : "bg-emerald-50 text-emerald-700",
                    ].join(" ")}
                  >
                    {kind.charAt(0)}
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-black text-ink">
                      {action.label}
                    </span>
                    <span className="block truncate text-[11px] text-muted">
                      {action.description}
                    </span>
                  </span>
                  <Plus className="mt-0.5 h-4 w-4 text-muted" />
                </button>
              ))}
            </div>
          </section>
        ))}
      </div>
    </Card>
  );
}
