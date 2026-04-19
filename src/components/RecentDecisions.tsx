import { useDashboard } from "@/lib/dashboard-context";
import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle } from "lucide-react";

export function RecentDecisions() {
  const { decisions, setSelectedDecision, setDrawerOpen } = useDashboard();
  const recent = decisions.slice(-20).reverse();

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
        Recent Decisions
      </h3>
      <div className="flex gap-2 overflow-x-auto pb-2">
        {recent.map((d, i) => {
          const conf = d.confidence_score;
          const confColor =
            conf >= 0.75
              ? "border-signal-green/40"
              : conf >= 0.5
                ? "border-signal-yellow/40"
                : "border-signal-red/40";
          return (
            <button
              key={i}
              onClick={() => {
                setSelectedDecision(d);
                setDrawerOpen(true);
              }}
              className={cn(
                "shrink-0 border rounded-md p-2 min-w-[100px] text-left transition-colors hover:bg-muted/50",
                confColor
              )}
            >
              <p className="text-xs font-semibold">{d.steering_command}</p>
              <p
                className={cn(
                  "text-[10px] font-mono",
                  conf >= 0.75
                    ? "text-signal-green"
                    : conf >= 0.5
                      ? "text-signal-yellow"
                      : "text-signal-red"
                )}
              >
                {(conf * 100).toFixed(0)}%
              </p>
              <div className="flex items-center gap-1 mt-1">
                {d.gate_outcome === "ACCEPTED" ? (
                  <CheckCircle2 className="h-3 w-3 text-signal-green" />
                ) : (
                  <XCircle className="h-3 w-3 text-signal-red" />
                )}
                {d.pete_status && (
                  <span
                    className={cn(
                      "h-2 w-2 rounded-full",
                      d.pete_status.overall_status === "WITHIN_LIMITS"
                        ? "bg-signal-green"
                        : d.pete_status.overall_status === "NEAR_LIMIT"
                          ? "bg-signal-yellow"
                          : "bg-signal-red"
                    )}
                    title={`PETE: ${d.pete_status.overall_status.replace(/_/g, " ")}`}
                  />
                )}
                <span className="text-[9px] text-muted-foreground">
                  {new Date(d.timestamp).toLocaleTimeString("en-US", {
                    hour12: false,
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  })}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
