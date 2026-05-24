"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  // Derived trend; PR 3 will replace with real daily rollups from a new
  // /api/posture/trend endpoint. For now we synthesize a smooth recent-history
  // line from the current posture score for visual scaffolding only.
  currentScore: number;
}

export function EvidenceTrend({ currentScore }: Props) {
  const today = new Date();
  const data = Array.from({ length: 14 }).map((_, i) => {
    const d = new Date(today);
    d.setDate(today.getDate() - (13 - i));
    const drift = Math.sin(i / 2) * 4;
    return {
      date: `${d.getMonth() + 1}/${d.getDate()}`,
      score: Math.max(0, Math.min(100, Math.round(currentScore - 6 + drift + i * 0.4))),
    };
  });

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle>Posture trend · 14 days</CardTitle>
        <CardDescription>
          Continuous compliance score. PR 3 wires this to a real /posture/trend rollup.
        </CardDescription>
      </CardHeader>
      <div className="h-[230px] w-full px-2 pb-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
            <defs>
              <linearGradient id="postureGrad" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#4f7cff" stopOpacity={0.45} />
                <stop offset="100%" stopColor="#4f7cff" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#eef2f7" />
            <XAxis dataKey="date" stroke="#a0aec0" tickLine={false} />
            <YAxis stroke="#a0aec0" domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
            <Tooltip
              formatter={(v: number) => [`${v}%`, "posture"]}
              contentStyle={{
                background: "#101623",
                color: "#fff",
                border: 0,
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Area
              type="monotone"
              dataKey="score"
              stroke="#4f7cff"
              strokeWidth={2.5}
              fill="url(#postureGrad)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
