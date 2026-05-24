"use client";

import { useEffect } from "react";
import { Camera, RefreshCw, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { NotificationBell } from "./NotificationBell";
import { UserMenu } from "./UserMenu";
import { useHealth } from "@/lib/api/hooks";

interface Props {
  onRefresh: () => void;
  onSnapshot: () => void;
  onOpenPalette: () => void;
}

export function TopBar({ onRefresh, onSnapshot, onOpenPalette }: Props) {
  const { data } = useHealth();
  const live = data?.ok ?? null;

  // cmd/ctrl + K opens the palette anywhere in the app.
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const isPalette =
        (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k";
      if (isPalette) {
        event.preventDefault();
        onOpenPalette();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onOpenPalette]);

  return (
    <header className="flex h-[78px] items-center justify-between gap-4 border-b border-railLine bg-rail px-7 text-slate-100">
      <div className="flex items-center gap-3 text-[25px] font-black">
        <span className="grid h-[38px] w-[38px] place-items-center rounded-xl bg-gradient-to-br from-brand to-brand-cyan text-base text-white">
          T
        </span>
        TrustOps
      </div>
      <button
        type="button"
        onClick={onOpenPalette}
        className="group flex flex-1 max-w-[640px] items-center gap-3 rounded-lg border border-[#27364a] bg-[#101926] py-2.5 pl-3.5 pr-2 text-left text-sm text-[#7d8ca3] hover:border-[#3b4d68]"
      >
        <Search className="h-4 w-4 text-[#5b6a7e]" />
        <span className="flex-1 truncate">
          Search controls, evidence, owners, assets, workflows…
        </span>
        <kbd className="rounded border border-[#27364a] bg-[#0b1118] px-1.5 py-0.5 text-[10px] font-bold text-[#9aa9bc]">
          ⌘K
        </kbd>
      </button>
      <div className="flex items-center gap-2.5">
        <UserMenu />
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
        <NotificationBell />
        <Button variant="default" onClick={onRefresh}>
          <RefreshCw className="h-4 w-4" /> Refresh
        </Button>
        <Button variant="primary" onClick={onSnapshot}>
          <Camera className="h-4 w-4" /> Snapshot
        </Button>
      </div>
    </header>
  );
}
