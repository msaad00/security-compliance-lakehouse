"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Loader2, Play, ShieldAlert, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Drawer } from "@/components/ui/drawer";
import { useTestAction } from "@/lib/api/hooks";
import type { ActionSchemaField, ActionSpec } from "@/lib/api/types";
import type { FlowNode } from "./WorkflowCanvas";

interface Props {
  node: FlowNode | null;
  spec: ActionSpec | null;
  onClose: () => void;
  onUpdateParams: (id: string, params: Record<string, unknown>) => void;
  onDelete: (id: string) => void;
}

function coerce(value: string, field: ActionSchemaField): string | number | boolean {
  if (field.type === "number") {
    const n = Number(value);
    return Number.isFinite(n) ? n : 0;
  }
  if (field.type === "boolean") return value === "true";
  return value;
}

export function NodeConfigDrawer({ node, spec, onClose, onUpdateParams, onDelete }: Props) {
  const test = useTestAction();
  const [params, setParams] = useState<Record<string, unknown>>({});
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setParams(node?.data.params ?? {});
    setResult(null);
    setError(null);
  }, [node?.id]);

  if (!node || !spec) {
    return (
      <Drawer open={false} onOpenChange={() => undefined} title="Node">
        <></>
      </Drawer>
    );
  }

  const fields = Object.entries(spec.input_schema);

  const persist = (next: Record<string, unknown>) => {
    setParams(next);
    onUpdateParams(node.id, next);
  };

  const runTest = async () => {
    setError(null);
    setResult(null);
    try {
      const out = await test.mutateAsync({ node_type: spec.node_type, params });
      setResult(out.output);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <Drawer
      open={true}
      onOpenChange={(o) => !o && onClose()}
      title={spec.label}
      description={spec.description}
      width="lg"
      footer={
        <div className="flex items-center justify-between gap-2">
          <Button
            variant="default"
            onClick={() => {
              onDelete(node.id);
              onClose();
            }}
          >
            <Trash2 className="h-4 w-4" /> Remove node
          </Button>
          <Button variant="primary" onClick={runTest} disabled={test.isPending}>
            {test.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}{" "}
            Test action
          </Button>
        </div>
      }
    >
      <div className="grid gap-5 text-sm">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="info">{spec.kind}</Badge>
          <code className="text-xs text-ink">{spec.node_type}</code>
        </div>

        <section className="grid gap-3">
          <div className="text-xs font-black uppercase tracking-wide text-muted">Parameters</div>
          {fields.length === 0 ? (
            <div className="rounded-lg border border-dashed border-line p-3 text-xs text-muted">
              This action takes no parameters.
            </div>
          ) : (
            fields.map(([name, field]) => {
              const value = params[name];
              const inputValue =
                value === undefined || value === null ? "" : String(value);
              return (
                <label
                  key={name}
                  className="grid gap-1 text-xs font-black uppercase tracking-wide text-muted"
                >
                  {field.label}
                  {field.required && <span className="text-rose-600">*</span>}
                  <input
                    value={inputValue}
                    placeholder={field.default !== undefined ? String(field.default) : ""}
                    onChange={(e) => {
                      const next = { ...params, [name]: coerce(e.target.value, field) };
                      persist(next);
                    }}
                    className="rounded-lg border border-line bg-white px-3 py-2 text-sm normal-case text-ink focus:outline-none focus:ring-1 focus:ring-brand"
                  />
                </label>
              );
            })
          )}
        </section>

        <section className="rounded-xl border border-line bg-slate-50/60 p-3">
          <div className="text-xs font-black uppercase tracking-wide text-muted">
            Output schema (downstream nodes can read)
          </div>
          <div className="mt-2 grid gap-1 text-xs">
            {Object.entries(spec.output_schema).map(([key, kind]) => (
              <div key={key} className="flex items-center justify-between rounded border border-line bg-white px-2 py-1">
                <code className="text-ink">{key}</code>
                <span className="text-muted">{kind}</span>
              </div>
            ))}
          </div>
        </section>

        {(result || error) && (
          <section
            className={[
              "rounded-xl border p-3 text-xs",
              error
                ? "border-rose-200 bg-rose-50 text-rose-900"
                : "border-emerald-200 bg-emerald-50 text-emerald-900",
            ].join(" ")}
          >
            <div className="flex items-center gap-2 font-black">
              {error ? (
                <>
                  <ShieldAlert className="h-4 w-4" /> Action errored
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4" /> Action returned
                </>
              )}
            </div>
            <pre className="mt-2 overflow-auto rounded bg-white p-2 font-mono text-[11px] text-ink">
{error ?? JSON.stringify(result, null, 2)}
            </pre>
          </section>
        )}
      </div>
    </Drawer>
  );
}
