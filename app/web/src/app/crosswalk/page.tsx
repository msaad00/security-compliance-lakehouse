"use client";

import { Layers } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/PageHeader";
import { useCrosswalk } from "@/lib/api/hooks";

export default function CrosswalkPage() {
  const crosswalk = useCrosswalk();
  const frameworks = crosswalk.data?.frameworks ?? [];
  const matrix = crosswalk.data?.matrix ?? [];

  return (
    <div className="grid gap-5 px-7 py-7">
      <PageHeader
        eyebrow="Crosswalk"
        title="Framework cross-mapping"
        description="Pairs every loaded framework against every other on shared risk domains and shared owners. Once reviewed control↔article mappings land (PR 8), this matrix swaps to the canonical mapping with auditor sign-off per cell."
        actions={
          <Badge tone="info">
            <Layers className="mr-1 h-3 w-3" /> {frameworks.length} × {frameworks.length}
          </Badge>
        }
      />

      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle>Shared risk domains</CardTitle>
          <CardDescription>
            Cells list the risk domains common to both frameworks' control catalogs.
          </CardDescription>
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className="bg-slate-50 px-3 py-2 text-left text-[11px] font-black uppercase tracking-wide text-muted">
                  Framework
                </th>
                {frameworks.map((f) => (
                  <th
                    key={f}
                    className="border-l border-line bg-slate-50 px-3 py-2 text-left text-[11px] font-black uppercase tracking-wide text-muted"
                  >
                    {f}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.map((row) => (
                <tr key={row.framework_id} className="border-t border-line">
                  <th className="bg-slate-50 px-3 py-3 text-left text-xs font-black text-ink">
                    {row.framework_id}
                  </th>
                  {row.cells.map((cell) => (
                    <td
                      key={cell.framework_id}
                      className={[
                        "border-l border-line p-3 align-top text-xs",
                        cell.is_self ? "bg-slate-100" : "bg-white",
                      ].join(" ")}
                    >
                      {cell.is_self ? (
                        <span className="text-muted">— self —</span>
                      ) : cell.shared_risk_domains.length === 0 ? (
                        <span className="text-muted">no shared risk domains</span>
                      ) : (
                        <div className="flex flex-wrap gap-1">
                          {cell.shared_risk_domains.map((d) => (
                            <Badge key={d}>{d}</Badge>
                          ))}
                        </div>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle>Shared owners</CardTitle>
          <CardDescription>
            Cells list the control owners common to both frameworks. Useful for "who is on the hook for this
            framework if we extend coverage" planning.
          </CardDescription>
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className="bg-slate-50 px-3 py-2 text-left text-[11px] font-black uppercase tracking-wide text-muted">
                  Framework
                </th>
                {frameworks.map((f) => (
                  <th
                    key={f}
                    className="border-l border-line bg-slate-50 px-3 py-2 text-left text-[11px] font-black uppercase tracking-wide text-muted"
                  >
                    {f}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.map((row) => (
                <tr key={row.framework_id} className="border-t border-line">
                  <th className="bg-slate-50 px-3 py-3 text-left text-xs font-black text-ink">
                    {row.framework_id}
                  </th>
                  {row.cells.map((cell) => (
                    <td
                      key={cell.framework_id}
                      className={[
                        "border-l border-line p-3 align-top text-xs",
                        cell.is_self ? "bg-slate-100" : "bg-white",
                      ].join(" ")}
                    >
                      {cell.is_self ? (
                        <span className="text-muted">— self —</span>
                      ) : cell.shared_owners.length === 0 ? (
                        <span className="text-muted">no shared owners</span>
                      ) : (
                        <div className="flex flex-wrap gap-1">
                          {cell.shared_owners.map((o) => (
                            <Badge tone="info" key={o}>
                              {o}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
