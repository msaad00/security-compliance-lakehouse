"use client";

import { Search, RefreshCw, Camera } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useHealth } from "@/lib/api/hooks";

interface Props {
  onRefresh: () => void;
  onSnapshot: () => void;
}

export function TopBar({ onRefresh, onSnapshot }: Props) {
  const { data } = useHealth();
  const live = data?.ok ?? null;

  return (
    <header className="flex h-[78px] items-center justify-between gap-4 border-b border-railLine bg-rail px-7 text-slate-100">
      <div className="flex items-center gap-3 text-[25px] font-black">
        <span className="grid h-[38px] w-[38px] place-items-center rounded-xl bg-gradient-to-br from-brand to-brand-cyan text-base text-white">
          T
        </span>
        TrustOps
      </div>
      <div className="relative flex-1 min-w-[420px] max-w-[720px]">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#5b6a7e]" />
        <input
          className="w-full rounded-lg border border-[#27364a] bg-[#101926] py-3 pl-10 pr-4 text-[#b9c6d6] placeholder:text-[#5b6a7e] focus:outline-none focus:ring-1 focus:ring-brand"
          placeholder="Search controls, evidence, owners, assets…"
        />
      </div>
      <div className="flex items-center gap-2.5">
        <span className="rounded-lg border border-[#27364a] bg-[#101926] px-3 py-2.5 text-sm font-extrabold text-[#d9e4f2]">
          Acme Co · Prod
        </span>
        <span
          className={[
            "inline-flex items-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-extrabold",
            live
              ? "border-emerald-300 bg-emerald-50 text-emerald-700"
              : "border-amber-300 bg-amber-50 text-amber-700",
          ].join(" ")}
        >
          <span
            className={[
              "h-2.5 w-2.5 rounded-full",
              live ? "bg-emerald-500" : "bg-amber-500",
            ].join(" ")}
          />
          {live === null ? "API checking" : live ? "API live" : "static mode"}
        </span>
        <Button variant="default" onClick={onRefresh}>
          <RefreshCw className="h-4 w-4" /> Refresh
        </Button>
        <Button variant="primary" onClick={onSnapshot}>
          <Camera className="h-4 w-4" /> Create snapshot
        </Button>
      </div>
    </header>
  );
}
