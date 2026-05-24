"use client";

import { useCallback, useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useQueryClient } from "@tanstack/react-query";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { api } from "@/lib/api/client";

export function Shell({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const [toast, setToast] = useState<string | null>(null);

  const flash = useCallback((msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 4200);
  }, []);

  const onRefresh = useCallback(async () => {
    await qc.invalidateQueries();
    flash("Posture refreshed from assessment data");
  }, [qc, flash]);

  const onSnapshot = useCallback(async () => {
    try {
      const r = await api.createSnapshot("console_request");
      flash(`Snapshot created: ${r.snapshot_path}`);
    } catch {
      flash(
        "Snapshot API unavailable. Run: security-lakehouse serve --lake build/lakehouse",
      );
    }
  }, [flash]);

  return (
    <div className="grid min-h-screen grid-rows-[78px_1fr] bg-rail">
      <TopBar onRefresh={onRefresh} onSnapshot={onSnapshot} />
      <div className="grid grid-cols-[286px_minmax(0,1fr)]">
        <Sidebar />
        <main className="overflow-auto bg-panel">{children}</main>
      </div>
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            className="fixed bottom-6 left-1/2 z-50 max-w-[520px] -translate-x-1/2 rounded-lg bg-[#111827] px-3.5 py-3 text-sm text-white shadow-hero"
          >
            {toast}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
