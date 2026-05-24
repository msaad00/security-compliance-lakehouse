import type { ReactNode } from "react";

interface Props {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
}

export function PageHeader({ eyebrow, title, description, actions }: Props) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <div className="text-[12px] font-black uppercase tracking-wider text-brand">{eyebrow}</div>
        <h1 className="mt-1 text-3xl font-black text-ink">{title}</h1>
        <p className="mt-2 max-w-[780px] text-sm text-muted">{description}</p>
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}
