"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { Edge } from "@xyflow/react";
import { Loader2, Play, Save } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/PageHeader";
import { ActionPalette } from "@/components/workflow/ActionPalette";
import { NodeConfigDrawer } from "@/components/workflow/NodeConfigDrawer";
import {
  WorkflowCanvas,
  toFlowNode,
  type FlowNode,
} from "@/components/workflow/WorkflowCanvas";
import {
  useActionCatalog,
  useRunWorkflow,
  useSaveWorkflow,
  useWorkflowRuns,
  useWorkflows,
} from "@/lib/api/hooks";
import type { ActionSpec, Workflow, WorkflowNode } from "@/lib/api/types";
import { useAuditorMode } from "@/lib/state/auditor";

const NEW_WORKFLOW_ID = "__new__";

let counter = 0;
const nextNodeId = () => `n${Date.now()}_${counter++}`;

interface Editor {
  workflow_id: string | null;
  name: string;
  description: string;
  nodes: FlowNode[];
  edges: Edge[];
}

function emptyEditor(): Editor {
  return { workflow_id: null, name: "Untitled workflow", description: "", nodes: [], edges: [] };
}

function fromWorkflow(w: Workflow, catalog: ActionSpec[]): Editor {
  const byType = new Map(catalog.map((a) => [a.node_type, a]));
  return {
    workflow_id: w.workflow_id,
    name: w.name,
    description: w.description,
    nodes: w.nodes.map((n) => toFlowNode(n, byType.get(n.node_type))),
    edges: w.edges.map((e) => ({
      id: `${e.source}-${e.target}`,
      source: e.source,
      target: e.target,
      animated: true,
    })),
  };
}

function toApiNodes(nodes: FlowNode[]): WorkflowNode[] {
  return nodes.map((n) => ({
    id: n.id,
    node_type: n.data.node_type,
    params: n.data.params,
    position: n.position,
  }));
}

export default function AutomationPage() {
  const auditor = useAuditorMode();
  const workflows = useWorkflows();
  const catalog = useActionCatalog();
  const save = useSaveWorkflow();
  const run = useRunWorkflow();
  const [activeId, setActiveId] = useState<string>(NEW_WORKFLOW_ID);
  const [editor, setEditor] = useState<Editor>(emptyEditor);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const runs = useWorkflowRuns(editor.workflow_id);

  const flash = useCallback((msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 4200);
  }, []);

  // Sync the editor whenever the user selects a different workflow or the
  // server returns a new version after save.
  useEffect(() => {
    if (activeId === NEW_WORKFLOW_ID) return;
    const w = (workflows.data ?? []).find((x) => x.workflow_id === activeId);
    if (w) setEditor(fromWorkflow(w, catalog.data ?? []));
  }, [activeId, workflows.data, catalog.data]);

  const specByType = useMemo(
    () => new Map((catalog.data ?? []).map((a) => [a.node_type, a])),
    [catalog.data],
  );

  const addNode = useCallback(
    (spec: ActionSpec) => {
      const id = nextNodeId();
      const node: FlowNode = {
        id,
        type: "trustops",
        position: { x: 120 + (editor.nodes.length % 4) * 220, y: 140 + Math.floor(editor.nodes.length / 4) * 130 },
        data: {
          label: spec.label,
          kind: spec.kind,
          node_type: spec.node_type,
          params: {},
        },
      };
      setEditor((e) => ({ ...e, nodes: [...e.nodes, node] }));
      setSelectedNode(id);
    },
    [editor.nodes.length],
  );

  const updateNodeParams = useCallback((id: string, params: Record<string, unknown>) => {
    setEditor((e) => ({
      ...e,
      nodes: e.nodes.map((n) => (n.id === id ? { ...n, data: { ...n.data, params } } : n)),
    }));
  }, []);

  const deleteNode = useCallback((id: string) => {
    setEditor((e) => ({
      ...e,
      nodes: e.nodes.filter((n) => n.id !== id),
      edges: e.edges.filter((edge) => edge.source !== id && edge.target !== id),
    }));
  }, []);

  const persist = async () => {
    if (!editor.name.trim()) {
      flash("Workflow needs a name");
      return;
    }
    if (editor.nodes.length === 0) {
      flash("Add at least one node before saving");
      return;
    }
    try {
      const { workflow } = await save.mutateAsync({
        workflow_id: editor.workflow_id ?? undefined,
        name: editor.name.trim(),
        description: editor.description.trim(),
        nodes: toApiNodes(editor.nodes),
        edges: editor.edges.map((e) => ({ source: String(e.source), target: String(e.target) })),
      });
      setActiveId(workflow.workflow_id);
      flash(`Saved ${workflow.name} v${workflow.version}.`);
    } catch (err) {
      flash(`Save failed: ${(err as Error).message}`);
    }
  };

  const execute = async () => {
    if (!editor.workflow_id) {
      flash("Save the workflow first.");
      return;
    }
    try {
      const { run: result } = await run.mutateAsync(editor.workflow_id);
      flash(`Run ${result.result.toUpperCase()} — ${result.node_results.length} nodes executed.`);
    } catch (err) {
      flash(`Run failed: ${(err as Error).message}`);
    }
  };

  const selected = editor.nodes.find((n) => n.id === selectedNode) ?? null;
  const selectedSpec = selected ? specByType.get(selected.data.node_type) ?? null : null;

  return (
    <div className="grid gap-5 px-7 py-7">
      <PageHeader
        eyebrow="Workflows"
        title="Workflow canvas"
        description="Drag actions from the library onto the canvas, connect them, then save and run. Every action publishes its input/output schema so connections are typed and individual nodes are testable live against the lake."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={activeId}
              onChange={(e) => {
                const next = e.target.value;
                setActiveId(next);
                if (next === NEW_WORKFLOW_ID) setEditor(emptyEditor());
                setSelectedNode(null);
              }}
              className="rounded-lg border border-line bg-white px-3 py-2 text-sm font-extrabold focus:outline-none focus:ring-1 focus:ring-brand"
            >
              <option value={NEW_WORKFLOW_ID}>+ New workflow</option>
              {(workflows.data ?? []).map((w) => (
                <option key={w.workflow_id} value={w.workflow_id}>
                  {w.name} · v{w.version}
                </option>
              ))}
            </select>
            {!auditor && (
              <>
                <Button variant="default" onClick={persist} disabled={save.isPending}>
                  {save.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}{" "}
                  Save
                </Button>
                <Button
                  variant="primary"
                  onClick={execute}
                  disabled={run.isPending || !editor.workflow_id}
                >
                  {run.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}{" "}
                  Run
                </Button>
              </>
            )}
          </div>
        }
      />

      <Card className="overflow-hidden">
        <div className="grid gap-3 p-4 sm:grid-cols-[1fr_2fr]">
          <label className="grid gap-1 text-xs font-black uppercase tracking-wide text-muted">
            Name
            <input
              value={editor.name}
              onChange={(e) => setEditor((ed) => ({ ...ed, name: e.target.value }))}
              className="rounded-lg border border-line bg-white px-3 py-2 text-sm font-extrabold text-ink focus:outline-none focus:ring-1 focus:ring-brand"
              disabled={auditor}
            />
          </label>
          <label className="grid gap-1 text-xs font-black uppercase tracking-wide text-muted">
            Description
            <input
              value={editor.description}
              onChange={(e) => setEditor((ed) => ({ ...ed, description: e.target.value }))}
              className="rounded-lg border border-line bg-white px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-brand"
              disabled={auditor}
            />
          </label>
        </div>
      </Card>

      <div className="grid gap-5 lg:grid-cols-[280px_minmax(0,1fr)]">
        <ActionPalette catalog={catalog.data ?? []} onAdd={addNode} />
        <WorkflowCanvas
          nodes={editor.nodes}
          edges={editor.edges}
          catalog={catalog.data ?? []}
          onNodesChange={(n) => setEditor((e) => ({ ...e, nodes: n }))}
          onEdgesChange={(es) => setEditor((e) => ({ ...e, edges: es }))}
          onSelectNode={setSelectedNode}
        />
      </div>

      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle>Run history</CardTitle>
          <CardDescription>
            Latest runs for {editor.workflow_id ? <code>{editor.workflow_id}</code> : "this canvas"}.
          </CardDescription>
        </CardHeader>
        <div className="grid gap-2 p-5 pt-0">
          {(runs.data ?? []).length === 0 ? (
            <div className="rounded-lg border border-dashed border-line p-3 text-xs text-muted">
              No runs yet. Save the workflow then click Run.
            </div>
          ) : (
            (runs.data ?? []).slice(0, 10).map((r) => (
              <div
                key={r.started_at + r.actor}
                className="rounded-lg border border-line bg-white p-3 text-xs"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-black">
                    v{r.workflow_version} · {r.node_results.length} nodes
                  </span>
                  <Badge tone={r.result === "ok" ? "ready" : "critical"}>{r.result}</Badge>
                </div>
                <div className="mt-1 text-muted">
                  actor <b className="text-ink">{r.actor}</b> · {r.started_at}
                </div>
                <div className="mt-2 grid gap-1">
                  {r.node_results.map((nr) => (
                    <div
                      key={nr.node_id}
                      className="grid grid-cols-[120px_minmax(0,1fr)_auto] items-center gap-2"
                    >
                      <code className="text-[10px] text-muted">{nr.node_id}</code>
                      <code className="truncate text-[10px] text-ink">{nr.node_type}</code>
                      <Badge tone={nr.result === "ok" ? "ready" : "critical"}>{nr.result}</Badge>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </Card>

      <NodeConfigDrawer
        node={selected}
        spec={selectedSpec}
        onClose={() => setSelectedNode(null)}
        onUpdateParams={updateNodeParams}
        onDelete={deleteNode}
      />

      {toast && (
        <div className="fixed bottom-6 left-1/2 z-[70] -translate-x-1/2 rounded-lg bg-ink px-3.5 py-3 text-sm text-white shadow-hero">
          {toast}
        </div>
      )}
    </div>
  );
}
