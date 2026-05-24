"use client";

import { useState } from "react";
import { LayoutTemplate, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import {
  WORKFLOW_TEMPLATES,
  type WorkflowTemplate,
} from "@/lib/workflow/templates";

interface Props {
  open: boolean;
  onClose: () => void;
  onPick: (template: WorkflowTemplate) => void;
}

export function TemplateGallery({ open, onClose, onPick }: Props) {
  const [selected, setSelected] = useState<string>(
    WORKFLOW_TEMPLATES[0]?.id ?? "",
  );
  const active =
    WORKFLOW_TEMPLATES.find((t) => t.id === selected) ?? WORKFLOW_TEMPLATES[0];

  return (
    <Modal
      open={open}
      onOpenChange={(o) => !o && onClose()}
      title="Workflow templates"
      description="Start from a vetted story instead of an empty canvas. Each template is editable after you load it."
      footer={
        <div className="flex items-center justify-end gap-2">
          <Button variant="default" onClick={onClose}>
            <X className="h-4 w-4" /> Close
          </Button>
          {active && (
            <Button
              variant="primary"
              onClick={() => {
                onPick(active);
                onClose();
              }}
            >
              <LayoutTemplate className="h-4 w-4" /> Load &quot;{active.name}
              &quot;
            </Button>
          )}
        </div>
      }
    >
      <div className="grid grid-cols-[200px_minmax(0,1fr)] gap-3">
        <div className="grid gap-1.5">
          {WORKFLOW_TEMPLATES.map((template) => (
            <button
              key={template.id}
              type="button"
              onClick={() => setSelected(template.id)}
              className={[
                "rounded-lg border px-3 py-2 text-left text-xs font-extrabold transition-colors",
                template.id === selected
                  ? "border-ink bg-ink text-white"
                  : "border-line bg-white text-ink hover:border-brand",
              ].join(" ")}
            >
              {template.name}
            </button>
          ))}
        </div>
        {active && (
          <div className="grid gap-3 rounded-xl border border-line bg-slate-50/60 p-3 text-sm">
            <div>
              <div className="text-xs font-black uppercase tracking-wide text-muted">
                Name
              </div>
              <div className="font-black text-ink">{active.name}</div>
            </div>
            <div>
              <div className="text-xs font-black uppercase tracking-wide text-muted">
                Description
              </div>
              <div className="text-ink">{active.description}</div>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {active.tags.map((tag) => (
                <Badge key={tag}>{tag}</Badge>
              ))}
            </div>
            <div>
              <div className="text-xs font-black uppercase tracking-wide text-muted">
                Composition
              </div>
              <div className="mt-1 grid gap-1 font-mono text-[11px] text-ink">
                {active.nodes.map((node) => (
                  <div
                    key={node.id}
                    className="rounded border border-line bg-white px-2 py-1"
                  >
                    <span className="text-muted">{node.id}</span> →{" "}
                    {node.node_type}
                  </div>
                ))}
                {active.edges.map((edge, idx) => (
                  <div
                    key={idx}
                    className="rounded border border-line bg-white px-2 py-1 text-muted"
                  >
                    {edge.source} ──{edge.condition ?? "always"}──▶{" "}
                    {edge.target}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
