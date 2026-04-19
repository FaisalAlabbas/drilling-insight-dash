import { useDashboard } from "@/lib/dashboard-context";
import { cn } from "@/lib/utils";
import { Cpu, AlertTriangle, Hand, CheckCircle2, XCircle, MinusCircle } from "lucide-react";

const STATE_CONFIG: Record<string, { color: string; bg: string; icon: typeof Cpu; label: string }> = {
  IDLE: { color: "text-muted-foreground", bg: "bg-muted", icon: Cpu, label: "Idle" },
  COMPLETE: { color: "text-signal-green", bg: "bg-signal-green/15", icon: CheckCircle2, label: "Complete" },
  FAULT: { color: "text-signal-red", bg: "bg-signal-red/15", icon: AlertTriangle, label: "Fault" },
  MANUAL: { color: "text-signal-amber", bg: "bg-signal-amber/15", icon: Hand, label: "Manual Override" },
};

const OUTCOME_CONFIG: Record<string, { color: string; label: string }> = {
  ACK_EXECUTED: { color: "text-signal-green", label: "Executed" },
  ACK_REDUCED: { color: "text-signal-amber", label: "Reduced" },
  ACK_REJECTED: { color: "text-signal-red", label: "Rejected" },
  ACK_BLOCKED: { color: "text-muted-foreground", label: "Blocked" },
  ACK_MANUAL_FALLBACK: { color: "text-signal-amber", label: "Manual Fallback" },
};

export function ActuatorStatusCard() {
  const { actuatorStatus, systemMode } = useDashboard();

  const state = actuatorStatus?.state ?? "IDLE";
  const config = STATE_CONFIG[state] ?? STATE_CONFIG.IDLE;
  const StateIcon = config.icon;

  const outcomeKey = actuatorStatus?.last_outcome;
  const outcomeConfig = outcomeKey ? OUTCOME_CONFIG[outcomeKey] : null;

  const lastTime = actuatorStatus?.timestamp
    ? new Date(actuatorStatus.timestamp).toLocaleTimeString("en-US", {
        hour12: false,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : "—";

  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Virtual Actuator
          </h3>
        </div>
        <span
          className={cn(
            "text-[10px] font-mono px-2 py-0.5 rounded-sm",
            systemMode === "PROTOTYPE"
              ? "bg-signal-green/15 text-signal-green"
              : "bg-cyan-500/15 text-cyan-400"
          )}
        >
          {actuatorStatus?.is_simulated !== false ? "SIMULATED" : "HARDWARE"}
        </span>
      </div>

      {/* State indicator */}
      <div className={cn("flex items-center gap-2 rounded-md px-3 py-2", config.bg)}>
        <StateIcon className={cn("h-4 w-4", config.color)} />
        <span className={cn("text-sm font-semibold", config.color)}>
          {config.label}
        </span>
      </div>

      {/* Fault reason */}
      {state === "FAULT" && actuatorStatus?.fault_reason && (
        <div className="flex items-start gap-2 text-xs text-signal-red bg-signal-red/10 rounded-md px-3 py-2">
          <XCircle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
          <span>{actuatorStatus.fault_reason}</span>
        </div>
      )}

      {/* Last command + outcome */}
      {actuatorStatus?.last_command && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Last Command</span>
            <span className="font-mono font-semibold">{actuatorStatus.last_command}</span>
          </div>

          {outcomeConfig && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Outcome</span>
              <span className={cn("font-semibold", outcomeConfig.color)}>
                {outcomeConfig.label}
              </span>
            </div>
          )}

          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Timestamp</span>
            <span className="font-mono text-[11px]">{lastTime}</span>
          </div>
        </div>
      )}

      {/* No commands yet */}
      {!actuatorStatus?.last_command && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <MinusCircle className="h-3.5 w-3.5" />
          <span>No commands processed yet</span>
        </div>
      )}

      {/* Command count */}
      {actuatorStatus && actuatorStatus.command_count > 0 && (
        <div className="flex items-center justify-between text-xs pt-1 border-t border-border">
          <span className="text-muted-foreground">Commands Processed</span>
          <span className="font-mono">{actuatorStatus.command_count}</span>
        </div>
      )}
    </div>
  );
}
