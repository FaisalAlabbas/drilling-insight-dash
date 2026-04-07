import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { LineChart, Line, ResponsiveContainer } from "recharts";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  title: string;
  value: string;
  unit: string;
  delta?: number;
  sparkData?: number[];
  color?: string;
  warning?: boolean;
}

export function StatsCard({
  title,
  value,
  unit,
  delta,
  sparkData,
  color = "hsl(var(--primary))",
  warning,
}: StatsCardProps) {
  const DeltaIcon =
    delta && delta > 0 ? TrendingUp : delta && delta < 0 ? TrendingDown : Minus;

  return (
    <div className={cn("stat-card", warning && "border-signal-red/40")}>
      <div className="flex items-start justify-between mb-2">
        <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">
          {title}
        </p>
        {delta !== undefined && (
          <div
            className={cn(
              "flex items-center gap-0.5 text-[10px] font-mono",
              delta > 0
                ? "text-signal-green"
                : delta < 0
                  ? "text-signal-red"
                  : "text-muted-foreground"
            )}
          >
            <DeltaIcon className="h-3 w-3" />
            {Math.abs(delta).toFixed(1)}
          </div>
        )}
      </div>
      <div className="flex items-end justify-between">
        <div>
          <span className="text-2xl font-bold font-mono tracking-tight">{value}</span>
          <span className="text-xs text-muted-foreground ml-1">{unit}</span>
        </div>
        {sparkData && sparkData.length > 0 && (
          <div className="w-20 h-8">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sparkData.map((v, i) => ({ v, i }))}>
                <Line
                  type="monotone"
                  dataKey="v"
                  stroke={color}
                  strokeWidth={1.5}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
