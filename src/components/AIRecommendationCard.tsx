import { useDashboard } from "@/lib/dashboard-context";
import { cn } from "@/lib/utils";
import { AlertTriangle, CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export function AIRecommendationCard() {
  const { decisions, edgeHealth, addAlert } = useDashboard();
  const [sending, setSending] = useState(false);
  const latest = decisions[decisions.length - 1];
  if (!latest) return null;

  const conf = latest.confidence_score;
  const confColor =
    conf >= 0.75
      ? "text-signal-green"
      : conf >= 0.5
        ? "text-signal-yellow"
        : "text-signal-red";
  const confBg =
    conf >= 0.75
      ? "bg-signal-green/15"
      : conf >= 0.5
        ? "bg-signal-yellow/15"
        : "bg-signal-red/15";

  const handleSendAlert = async () => {
    setSending(true);
    try {
      // Create alert based on current recommendation
      const alertMsg =
        latest.gate_outcome === "REJECTED"
          ? `Safety alert: Command ${latest.steering_command} was REJECTED. Reason: ${latest.rejection_reason}`
          : `AI Recommendation sent: ${latest.steering_command} (Confidence: ${(conf * 100).toFixed(0)}%)`;

      addAlert(
        latest.gate_outcome === "REJECTED"
          ? "⚠️ Safety Gate Rejected"
          : "✓ Command Approved",
        alertMsg,
        latest.gate_outcome === "REJECTED" ? "CRITICAL" : "INFO"
      );
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          AI Recommendation
        </h3>
        <span className="text-[10px] font-mono text-muted-foreground">
          {latest.model_version}
        </span>
      </div>

      <div className="text-center py-2">
        <p className="text-3xl font-bold tracking-tight">{latest.steering_command}</p>
        <div
          className={cn(
            "inline-flex items-center gap-1.5 mt-2 px-3 py-1 rounded-full text-xs font-semibold",
            confBg,
            confColor
          )}
        >
          <span>{(conf * 100).toFixed(0)}% confidence</span>
        </div>
      </div>

      <div className="space-y-2 border-t border-border pt-3">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Gate Outcome</span>
          <span
            className={cn(
              "flex items-center gap-1 font-semibold",
              latest.gate_outcome === "ACCEPTED"
                ? "text-signal-green"
                : latest.gate_outcome === "REDUCED"
                  ? "text-signal-yellow"
                  : "text-signal-red"
            )}
          >
            {latest.gate_outcome === "ACCEPTED" ? (
              <CheckCircle2 className="h-3.5 w-3.5" />
            ) : latest.gate_outcome === "REDUCED" ? (
              <AlertTriangle className="h-3.5 w-3.5" />
            ) : (
              <XCircle className="h-3.5 w-3.5" />
            )}
            {latest.gate_outcome}
          </span>
        </div>

        {/* PETE Operating Envelope Status */}
        {latest.pete_status && (
          <>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">PETE Envelope</span>
              <span
                className={cn(
                  "flex items-center gap-1 font-semibold px-2 py-0.5 rounded-full text-[10px]",
                  latest.pete_status.overall_status === "WITHIN_LIMITS"
                    ? "bg-signal-green/15 text-signal-green"
                    : latest.pete_status.overall_status === "NEAR_LIMIT"
                      ? "bg-signal-yellow/15 text-signal-yellow"
                      : "bg-signal-red/15 text-signal-red"
                )}
              >
                {latest.pete_status.overall_status === "WITHIN_LIMITS" ? (
                  <CheckCircle2 className="h-3 w-3" />
                ) : latest.pete_status.overall_status === "NEAR_LIMIT" ? (
                  <AlertTriangle className="h-3 w-3" />
                ) : (
                  <XCircle className="h-3 w-3" />
                )}
                {latest.pete_status.overall_status.replace(/_/g, " ")}
              </span>
            </div>
            {latest.pete_status.violations.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {latest.pete_status.violations.map((v) => (
                  <span
                    key={v}
                    className="inline-block px-1.5 py-0.5 rounded bg-signal-red/10 text-signal-red text-[10px] font-mono"
                  >
                    {v}
                  </span>
                ))}
              </div>
            )}
            {latest.pete_status.formation_sensitivity && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Formation</span>
                <span className="font-mono text-[11px] capitalize">
                  {latest.pete_status.formation_sensitivity}
                </span>
              </div>
            )}
          </>
        )}

        {latest.rejection_reason && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Reason</span>
            <span className="text-signal-red font-mono text-[11px]">
              {latest.rejection_reason}
            </span>
          </div>
        )}

        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Execution</span>
          <span
            className={cn(
              "font-semibold",
              latest.execution_status === "SENT"
                ? "text-signal-green"
                : latest.execution_status === "SIMULATED_SENT"
                  ? "text-cyan-400"
                  : "text-signal-amber"
            )}
          >
            {latest.execution_status === "SIMULATED_SENT"
              ? "SIMULATED"
              : latest.execution_status}
          </span>
        </div>

        {latest.system_mode && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Mode</span>
            <span
              className={cn(
                "font-mono text-[11px] px-1.5 py-0.5 rounded-sm",
                latest.system_mode === "PROTOTYPE"
                  ? "bg-signal-green/15 text-signal-green"
                  : "bg-cyan-500/15 text-cyan-400"
              )}
            >
              {latest.system_mode}
            </span>
          </div>
        )}

        {latest.fallback_mode && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Fallback</span>
            <span className="text-signal-amber font-mono text-[11px]">
              {latest.fallback_mode}
            </span>
          </div>
        )}

        {latest.actuator_outcome && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Actuator</span>
            <span
              className={cn(
                "font-mono text-[11px] font-semibold",
                latest.actuator_outcome === "ACK_EXECUTED"
                  ? "text-signal-green"
                  : latest.actuator_outcome === "ACK_REDUCED"
                    ? "text-signal-amber"
                    : latest.actuator_outcome === "ACK_BLOCKED"
                      ? "text-muted-foreground"
                      : "text-signal-red"
              )}
            >
              {latest.actuator_outcome.replace("ACK_", "")}
            </span>
          </div>
        )}
      </div>

      <div className="border-t border-border pt-3">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Edge Health</span>
          <span
            className={cn(
              "flex items-center gap-1 font-semibold",
              edgeHealth === "Healthy" ? "text-signal-green" : "text-signal-yellow"
            )}
          >
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full signal-pulse",
                edgeHealth === "Healthy" ? "bg-signal-green" : "bg-signal-yellow"
              )}
            />
            {edgeHealth}
          </span>
        </div>
      </div>

      <Button
        onClick={handleSendAlert}
        disabled={sending}
        className="w-full mt-3 bg-primary/80 hover:bg-primary text-xs"
        size="sm"
      >
        <AlertCircle className="h-3 w-3 mr-1.5" />
        {sending ? "Sending Alert..." : "Send Alert"}
      </Button>
    </div>
  );
}
