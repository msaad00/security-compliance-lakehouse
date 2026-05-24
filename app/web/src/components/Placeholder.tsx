import { Sparkles } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  title: string;
  body: string;
}

export function Placeholder({ title, body }: Props) {
  return (
    <div className="grid gap-5 px-7 py-7">
      <Card>
        <CardHeader>
          <div className="text-[12px] font-black uppercase tracking-wider text-brand">
            <span className="inline-flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5" /> Coming in PR 2
            </span>
          </div>
          <CardTitle className="mt-1 text-2xl">{title}</CardTitle>
          <CardDescription>{body}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted">
            PR 1 ships the Next.js + shadcn/Radix + TanStack + Recharts + Visx +
            framer-motion shell and the Trust dashboard. The remaining views
            are ported in PR 2 over the same /api endpoints, then PR 3 adds
            interactive drawers, triage, evidence verification, and auditor mode.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
