"use client";

import { useCallback, useEffect, useMemo } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  type Connection,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
  type NodeProps,
  type NodeTypes,
  type ReactFlowProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { ActionSpec, WorkflowNode } from "@/lib/api/types";

interface NodeData extends Record<string, unknown> {
  label: string;
  kind: "trigger" | "check" | "action";
  node_type: string;
  params: Record<string, unknown>;
}

export type FlowNode = Node<NodeData, "trustops">;

const KIND_STYLE: Record<NodeData["kind"], { border: string; bg: string; chip: string }> = {
  trigger: { border: "#4f7cff", bg: "#eff6ff", chip: "#1d4ed8" },
  check: { border: "#f79009", bg: "#fffbeb", chip: "#b54708" },
  action: { border: "#16b364", bg: "#ecfdf5", chip: "#067647" },
};

function NodeCard({ data, selected }: NodeProps<FlowNode>) {
  const tone = KIND_STYLE[data.kind];
  return (
    <div
      style={{
        borderColor: selected ? "#101623" : tone.border,
        background: tone.bg,
        borderWidth: selected ? 2 : 1.5,
      }}
      className="min-w-[200px] rounded-xl px-3 py-2.5 text-left shadow-sm transition-colors"
    >
      <div className="flex items-center justify-between gap-2">
        <span
          className="rounded-full px-2 py-0.5 text-[10px] font-black uppercase tracking-wide"
          style={{ color: tone.chip, background: "#ffffff" }}
        >
          {data.kind}
        </span>
        <code className="text-[10px] text-slate-500">{data.node_type}</code>
      </div>
      <div className="mt-1.5 text-sm font-black text-ink">{data.label}</div>
      {Object.keys(data.params).length > 0 && (
        <div className="mt-1 truncate text-[11px] text-slate-600">
          {Object.entries(data.params)
            .map(([k, v]) => `${k}: ${String(v)}`)
            .slice(0, 2)
            .join(" · ")}
        </div>
      )}
    </div>
  );
}

const nodeTypes: NodeTypes = { trustops: NodeCard };

function toFlowNode(node: WorkflowNode, action: ActionSpec | undefined): FlowNode {
  return {
    id: node.id,
    type: "trustops",
    position: node.position ?? { x: 0, y: 0 },
    data: {
      label: action?.label ?? node.node_type,
      kind: (action?.kind ?? "action") as NodeData["kind"],
      node_type: node.node_type,
      params: node.params ?? {},
    },
  };
}

interface Props {
  nodes: FlowNode[];
  edges: Edge[];
  catalog: ActionSpec[];
  onNodesChange: (nodes: FlowNode[]) => void;
  onEdgesChange: (edges: Edge[]) => void;
  onSelectNode: (id: string | null) => void;
  fitTrigger?: number;
}

export function WorkflowCanvas({
  nodes,
  edges,
  catalog,
  onNodesChange,
  onEdgesChange,
  onSelectNode,
  fitTrigger,
}: Props) {
  const handleNodesChange = useCallback(
    (changes: NodeChange[]) => {
      const next = applyNodeChanges(changes, nodes) as FlowNode[];
      onNodesChange(next);
    },
    [nodes, onNodesChange],
  );

  const handleEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      onEdgesChange(applyEdgeChanges(changes, edges));
    },
    [edges, onEdgesChange],
  );

  const handleConnect = useCallback(
    (params: Connection) => {
      onEdgesChange(addEdge({ ...params, animated: true }, edges));
    },
    [edges, onEdgesChange],
  );

  const handleSelection = useCallback<NonNullable<ReactFlowProps["onSelectionChange"]>>(
    ({ nodes: selected }) => {
      onSelectNode(selected[0]?.id ?? null);
    },
    [onSelectNode],
  );

  // Keep node labels in sync with catalog updates.
  const decoratedNodes = useMemo(() => {
    const byType = new Map(catalog.map((a) => [a.node_type, a]));
    return nodes.map((node) => ({
      ...node,
      data: {
        ...node.data,
        kind: byType.get(node.data.node_type)?.kind ?? node.data.kind,
        label: byType.get(node.data.node_type)?.label ?? node.data.label,
      },
    }));
  }, [nodes, catalog]);

  useEffect(() => {
    // touch fitTrigger so consumers can ask for a refit via state change
    void fitTrigger;
  }, [fitTrigger]);

  return (
    <div className="h-[560px] overflow-hidden rounded-2xl border border-line bg-white">
      <ReactFlow
        nodes={decoratedNodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={handleConnect}
        onSelectionChange={handleSelection}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={20} color="#e2e8f0" />
        <MiniMap pannable zoomable maskColor="rgba(15,23,42,0.06)" />
        <Controls position="bottom-left" />
      </ReactFlow>
    </div>
  );
}

export { toFlowNode };
