"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TelemetrySample } from "@/lib/types";

type MetricKey = "p95" | "p99" | "errorRate";

const metricConfig: Record<MetricKey, { label: string; unit: string }> = {
  p95: { label: "p95 latency", unit: "ms" },
  p99: { label: "p99 latency", unit: "ms" },
  errorRate: { label: "error rate", unit: "%" },
};

export function ComparisonChart({
  title,
  before,
  after,
  metric,
}: {
  title: string;
  before: TelemetrySample[];
  after?: TelemetrySample[] | null;
  metric: MetricKey;
}) {
  const merged = before.map((point, index) => ({
    t: point.t,
    before: point[metric],
    after: after ? after[index]?.[metric] ?? null : null,
  }));
  const config = metricConfig[metric];

  return (
    <div className="rounded-xl border border-white/10 bg-zinc-900/60 p-4">
      <div className="mb-3 flex items-baseline justify-between">
        <h3 className="text-sm font-medium text-zinc-200">{title}</h3>
        <span className="text-xs text-zinc-500">
          {config.label} ({config.unit})
        </span>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={merged} margin={{ top: 4, right: 12, bottom: 4, left: 0 }}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis
              dataKey="t"
              tick={{ fill: "#71717a", fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
              unit="s"
            />
            <YAxis
              tick={{ fill: "#71717a", fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              width={52}
            />
            <Tooltip
              contentStyle={{
                background: "#09090b",
                border: "1px solid rgba(255,255,255,0.15)",
                borderRadius: 8,
                fontSize: 12,
              }}
              labelFormatter={(value) => `t = ${value}s`}
              formatter={(value, name) => [
                `${Number(value).toFixed(1)} ${config.unit}`,
                name === "before" ? "before fix" : "after fix",
              ]}
            />
            <Legend
              formatter={(value) => (value === "before" ? "Before fix" : "After fix")}
              wrapperStyle={{ fontSize: 12 }}
            />
            <ReferenceLine
              x={30}
              stroke="#f59e0b"
              strokeDasharray="4 4"
              label={{ value: "chaos injection", fill: "#f59e0b", fontSize: 10, position: "insideTopRight" }}
            />
            <Line
              type="monotone"
              dataKey="before"
              stroke="#fb7185"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            {after ? (
              <Line
                type="monotone"
                dataKey="after"
                stroke="#34d399"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            ) : null}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
