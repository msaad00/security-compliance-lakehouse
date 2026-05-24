"use client";

import { useEffect, useMemo, useState } from "react";
import dagre from "@dagrejs/dagre";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { FrameworkBadge } from "@/components/framework/FrameworkBadge";
import type { ComplianceGraph, GraphNode, GraphNodeKind } from "@/lib/api/types";

interface GraphNodeData extends Record<string, unknown> {
  label: string;
  subtitle: string;
  kind: GraphNodeKind;
  framework_id?: string;
  owner?: string;
  risk_score?: number;
}

type FlowGraphNode = Node<GraphNodeData, "trustops-graph">;

const KIND_STYLE: Record<GraphNodeKind, { border: string; bg: string; chip: string }> = {
  framework: { border: "#4f7cff", bg: "#eff6ff", chip: "#1d4ed8" },
  control: { border: "#16b364", bg: "#ecfdf5", chip: "#067647" },
  evidence_type: { border: "#f79009", bg: "#fffbeb", chip: "#b54708" },
  asset: { border: "#7a35ff", bg: "#f5f0ff", chip: "#6d28d9" },
};

function GraphNodeCard({ data, selected }: NodeProps<FlowGraphNode>) {
  const tone = KIND_STYLE[data.kind];
  return (
    <div
      style={{
        borderColor: selected ? "#101623" : tone.border,
        background: tone.bg,
        borderWidth: selected ? 2 : 1.5,
      }}
      className="min-w-[180px] max-w-[220px] rounded-xl px-3 py-2.5 shadow-sm transition-colors"
    >
      <div className="flex items-center justify-between gap-2">
        <span
          className="rounded-full px-2 py-0.5 text-[10px] font-black uppercase tracking-wide"
          style={{ color: tone.chip, background: "#ffffff" }}
        >
          {data.kind.replace("_", " ")}
        </span>
        {data.kind === "framework" && data.framework_id && (
          <FrameworkBadge frameworkId={data.framework_id} fallbackLabel={data.label} size={24} />
        )}
      </div>
      <div className="mt-1.5 truncate text-sm font-black text-ink">{data.label}</div>
      <div className="truncate text-[11px] text-slate-600">{data.subtitle}</div>
      {data.owner && <div className="mt-1 truncate text-[10px] text-slate-500">owner {data.owner}</div>}
    </div>
  );
}

const nodeTypes: NodeTypes = { "trustops-graph": GraphNodeCard };

function layoutGraph(
  rfNodes: FlowGraphNode[],
  rfEdges: Edge[],
): { nodes: FlowGraphNode[]; edges: Edge[] } {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "LR", nodesep: 30, ranksep: 70, marginx: 20, marginy: 20 });

  rfNodes.forEach((node) => g.setNode(node.id, { width: 200, height: 70 }));
  rfEdges.forEach((edge) => g.setEdge(edge.source, edge.target));
  dagre.layout(g);

  const laidOut = rfNodes.map((node) => {
    const pos = g.node(node.id);
    return {
      ...node,
      position: { x: pos.x - 100, y: pos.y - 35 },
    };
  });
  return { nodes: laidOut, edges: rfEdges };
}

interface Props {
  graph: ComplianceGraph | undefined;
  visibleKinds: Set<GraphNodeKind>;
  onSelectNode: (node: GraphNode | null) => void;
}

export function GraphCanvas({ graph, visibleKinds, onSelectNode }: Props) {
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => setHydrated(true), []);

  const { nodes, edges } = useMemo(() => {
    if (!graph) return { nodes: [] as FlowGraphNode[], edges: [] as Edge[] };
    const allowedNodeIds = new Set(
      graph.nodes.filter((n) => visibleKinds.has(n.kind)).map((n) => n.id),
    );
    const rfNodes: FlowGraphNode[] = graph.nodes
      .filter((n) => allowedNodeIds.has(n.id))
      .map((n) => ({
        id: n.id,
        type: "trustops-graph",
        position: { x: 0, y: 0 },
        data: {
          label: n.label,
          subtitle: n.subtitle ?? "",
          kind: n.kind,
          framework_id: n.framework_id,
          owner: n.owner,
          risk_score: n.risk_score,
        },
      }));
    const rfEdges: Edge[] = graph.edges
      .filter((e) => allowedNodeIds.has(e.source) && allowedNodeIds.has(e.target))
      .map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        animated: e.kind === "evidence_covers_asset",
        style: { stroke: "#94a3b8", strokeWidth: 1.5 },
      }));
    return layoutGraph(rfNodes, rfEdges);
  }, [graph, visibleKinds]);

  if (!hydrated) {
    return (
      <div className="h-[640px] rounded-2xl border border-line bg-white" />
    );
  }

  return (
    <div className="h-[640px] overflow-hidden rounded-2xl border border-line bg-white">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        nodesDraggable
        nodesConnectable={false}
        edgesReconnectable={false}
        fitView
        proOptions={{ hideAttribution: true }}
        onSelectionChange={({ nodes: selected }) => {
          const first = selected[0];
          if (!first) return onSelectNode(null);
          const original = graph?.nodes.find((n) => n.id === first.id) ?? null;
          onSelectNode(original);
        }}
      >
        <Background gap={20} color="#e2e8f0" />
        <MiniMap pannable zoomable maskColor="rgba(15,23,42,0.06)" />
        <Controls position="bottom-left" />
      </ReactFlow>
    </div>
  );
}
