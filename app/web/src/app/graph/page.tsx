"use client";

import { useMemo, useState } from "react";
import { Filter, Network } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/PageHeader";
import { GraphCanvas } from "@/components/graph/GraphCanvas";
import { useComplianceGraph } from "@/lib/api/hooks";
import type { GraphNode, GraphNodeKind } from "@/lib/api/types";

const ALL_KINDS: GraphNodeKind[] = ["framework", "control", "evidence_type", "asset"];

const KIND_LABEL: Record<GraphNodeKind, string> = {
  framework: "Frameworks",
  control: "Controls",
  evidence_type: "Evidence types",
  asset: "Assets",
};

const KIND_TONE: Record<GraphNodeKind, "info" | "ready" | "attention" | "critical"> = {
  framework: "info",
  control: "ready",
  evidence_type: "attention",
  asset: "critical",
};

export default function GraphPage() {
  const graph = useComplianceGraph();
  const [visible, setVisible] = useState<Set<GraphNodeKind>>(new Set(ALL_KINDS));
  const [selected, setSelected] = useState<GraphNode | null>(null);

  const data = graph.data;

  const counts = useMemo(() => data?.counts ?? { framework: 0, control: 0, evidence_type: 0, asset: 0 }, [data]);

  const toggle = (kind: GraphNodeKind) => {
    setVisible((prev) => {
      const next = new Set(prev);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      return next;
    });
  };

  return (
    <div className="grid gap-5 px-7 py-7">
      <PageHeader
        eyebrow="Graph"
        title="Framework → control → evidence → asset"
        description="Every framework loaded into the workbench, the controls under it, the evidence types those controls require, and the assets that evidence covers — laid out left-to-right. Toggle any layer below to filter. Pan, zoom, and drag nodes to reorganize."
        actions={
          <Badge tone="info">
            <Network className="mr-1 h-3 w-3" /> {data ? `${data.nodes.length} nodes / ${data.edges.length} edges` : "loading"}
          </Badge>
        }
      />

      <Card className="overflow-hidden">
        <div className="flex flex-wrap items-center gap-2 p-3">
          <Filter className="h-4 w-4 text-muted" />
          <span className="mr-2 text-xs font-black uppercase tracking-wide text-muted">Layers</span>
          {ALL_KINDS.map((kind) => {
            const on = visible.has(kind);
            return (
              <button
                key={kind}
                type="button"
                onClick={() => toggle(kind)}
                className={[
                  "rounded-full border px-3 py-1.5 text-xs font-black",
                  on
                    ? "border-ink bg-ink text-white"
                    : "border-line bg-white text-slate-600 hover:border-brand",
                ].join(" ")}
              >
                {KIND_LABEL[kind]} ({counts[kind] ?? 0})
              </button>
            );
          })}
        </div>
      </Card>

      <GraphCanvas graph={data} visibleKinds={visible} onSelectNode={setSelected} />

      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle>Selected node</CardTitle>
          <CardDescription>
            Click any node in the canvas to inspect. Edges follow the lake's append-only contract — they're derived,
            not stored.
          </CardDescription>
        </CardHeader>
        <div className="p-5 pt-0 text-sm">
          {selected ? (
            <div className="grid gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={KIND_TONE[selected.kind]}>{selected.kind.replace("_", " ")}</Badge>
                <code className="text-xs text-ink">{selected.id}</code>
              </div>
              <dl className="grid grid-cols-[140px_1fr] gap-x-3 gap-y-1.5">
                <dt className="text-muted">Label</dt>
                <dd className="font-extrabold">{selected.label}</dd>
                {selected.subtitle && (
                  <>
                    <dt className="text-muted">Subtitle</dt>
                    <dd>{selected.subtitle}</dd>
                  </>
                )}
                {selected.framework_id && (
                  <>
                    <dt className="text-muted">Framework</dt>
                    <dd className="font-extrabold">{selected.framework_id}</dd>
                  </>
                )}
                {selected.owner && (
                  <>
                    <dt className="text-muted">Owner</dt>
                    <dd className="font-extrabold">{selected.owner}</dd>
                  </>
                )}
                {selected.environment && (
                  <>
                    <dt className="text-muted">Environment</dt>
                    <dd className="font-extrabold">{selected.environment}</dd>
                  </>
                )}
                {selected.risk_score !== undefined && (
                  <>
                    <dt className="text-muted">Risk score</dt>
                    <dd className="font-extrabold">{selected.risk_score}</dd>
                  </>
                )}
                {selected.event_count !== undefined && (
                  <>
                    <dt className="text-muted">Evidence count</dt>
                    <dd className="font-extrabold">{selected.event_count}</dd>
                  </>
                )}
              </dl>
            </div>
          ) : (
            <div className="text-xs text-muted">No node selected.</div>
          )}
        </div>
      </Card>
    </div>
  );
}
