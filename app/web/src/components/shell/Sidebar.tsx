"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Zap,
  ShieldCheck,
  AlertOctagon,
  FileSearch,
  Plug,
  Sparkles,
  Bot,
  BookOpen,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface RailItem {
  href: string;
  label: string;
  Icon: typeof LayoutDashboard;
  badge?: string;
  group: "Operate" | "Configure";
}

const ITEMS: RailItem[] = [
  { href: "/dashboard", label: "Dashboard", Icon: LayoutDashboard, badge: "live", group: "Operate" },
  { href: "/controls", label: "Controls", Icon: ShieldCheck, group: "Operate" },
  { href: "/violations", label: "Violations", Icon: AlertOctagon, group: "Operate" },
  { href: "/evidence", label: "Evidence", Icon: FileSearch, group: "Operate" },
  { href: "/automation", label: "Workflows", Icon: Zap, group: "Operate" },
  { href: "/audit-log", label: "Audit log", Icon: Activity, group: "Operate" },
  { href: "/connectors", label: "Connectors", Icon: Plug, group: "Configure" },
  { href: "/frameworks", label: "Frameworks", Icon: BookOpen, group: "Configure" },
  { href: "/trust-center", label: "Trust center", Icon: Sparkles, group: "Configure" },
  { href: "/agents", label: "Agent API", Icon: Bot, badge: "JSON", group: "Configure" },
];

export function Sidebar() {
  const pathname = usePathname() ?? "/dashboard";
  const groups: RailItem["group"][] = ["Operate", "Configure"];

  return (
    <aside className="grid w-[286px] content-start gap-2 border-r border-railLine bg-rail p-4 text-slate-300">
      {groups.map((group) => (
        <div key={group}>
          <div className="px-3 pb-1.5 pt-4 text-[12px] font-black uppercase tracking-[0.08em] text-[#708198]">
            {group}
          </div>
          <div className="grid gap-1.5">
            {ITEMS.filter((i) => i.group === group).map(({ href, label, Icon, badge }) => {
              const active = pathname === href || pathname.startsWith(href + "/");
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "flex h-[46px] items-center justify-between gap-2.5 rounded-xl border px-3 text-[15px] font-extrabold transition-colors",
                    active
                      ? "border-[#31435c] bg-[#172436] text-white"
                      : "border-transparent text-[#c6d1df] hover:bg-[#152030]",
                  )}
                >
                  <span className="flex items-center gap-2.5">
                    <span
                      className={cn(
                        "grid h-[27px] w-[27px] place-items-center rounded-lg",
                        active ? "bg-[#eff6ff] text-[#1d4ed8]" : "bg-[#1d2b3d] text-[#9cc2ff]",
                      )}
                    >
                      <Icon className="h-4 w-4" />
                    </span>
                    {label}
                  </span>
                  {badge && (
                    <b className="rounded-full bg-[#26364b] px-2 py-0.5 text-[12px] text-[#cfe0f5]">
                      {badge}
                    </b>
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </aside>
  );
}
