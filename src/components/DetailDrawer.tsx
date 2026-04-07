import { X, Clock, Tag, Activity } from "lucide-react";
import { useDashboard } from "@/lib/dashboard-context";
import { cn } from "@/lib/utils";
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";

export function DetailDrawer() {
  const { drawerOpen, setDrawerOpen, selectedDecision, selectedAlert, telemetry } =
    useDashboard();

  if (!drawerOpen) return null;

  const decision = selectedDecision;
  const alert = selectedAlert;

  // Get nearby telemetry for context
  const contextData = telemetry.slice(-60).map((p) => ({
    time: new Date(p.timestamp).toLocaleTimeString("en-US", {
      hour12: false,
      second: "2-digit",
      minute: "2-digit",
      hour: "2-digit",
    }),
    wob: p.wob_klbf,
    vibration: p.vibration_g,
    rpm: p.rpm,
  }));

  return (
    <>
      <div
        className="fixed inset-0 bg-background/60 z-40"
        onClick={() => setDrawerOpen(false)}
      />
      <div className="fixed right-0 top-0 h-full w-full max-w-md bg-card border-l border-border z-50 flex flex-col overflow-hidden animate-in slide-in-from-right duration-200">
        <div className="flex items-center justify-between p-4 border-b border-border shrink-0">
          <h2 className="text-sm font-semibold">
            {decision ? "Decision Details" : alert ? "Alert Details" : "Details"}
          </h2>
          <button
            onClick={() => setDrawerOpen(false)}
            className="p-1 hover:bg-muted rounded"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {decision && (
            <>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-bold">{decision.steering_command}</span>
                  <span
                    className={cn(
                      "text-xs font-semibold px-2 py-0.5 rounded-full",
                      decision.gate_outcome === "ACCEPTED"
                        ? "bg-signal-green/15 text-signal-green"
                        : "bg-signal-red/15 text-signal-red"
                    )}
                  >
                    {decision.gate_outcome}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-muted rounded-md p-2">
                    <p className="text-muted-foreground">Confidence</p>
                    <p className="font-mono font-semibold">
                      {(decision.confidence_score * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="bg-muted rounded-md p-2">
                    <p className="text-muted-foreground">Execution</p>
                    <p className="font-semibold">{decision.execution_status}</p>
                  </div>
                  {decision.rejection_reason && (
                    <div className="bg-muted rounded-md p-2">
                      <p className="text-muted-foreground">Rejection</p>
                      <p className="font-mono text-signal-red">
                        {decision.rejection_reason}
                      </p>
                    </div>
                  )}
                  {decision.fallback_mode && (
                    <div className="bg-muted rounded-md p-2">
                      <p className="text-muted-foreground">Fallback</p>
                      <p className="font-mono text-signal-amber">
                        {decision.fallback_mode}
                      </p>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  {new Date(decision.timestamp).toLocaleString()}
                </div>

                {decision.event_tags.length > 0 && (
                  <div className="flex items-center gap-1 flex-wrap">
                    <Tag className="h-3 w-3 text-muted-foreground" />
                    {decision.event_tags.map((t) => (
                      <span
                        key={t}
                        className="text-[10px] px-1.5 py-0.5 bg-primary/10 text-primary rounded"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="border-t border-border pt-4">
                <h4 className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider">
                  Feature Summary
                </h4>
                <div className="grid grid-cols-2 gap-1.5 text-[11px]">
                  {Object.entries(decision.feature_summary).map(([k, v]) => (
                    <div
                      key={k}
                      className="flex justify-between bg-muted/50 rounded px-2 py-1"
                    >
                      <span className="text-muted-foreground font-mono">{k}</span>
                      <span className="font-mono">
                        {typeof v === "number" ? v.toFixed(2) : v}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {alert && (
            <>
              <div className="space-y-3">
                <h3 className="text-lg font-semibold">{alert.title}</h3>
                <p className="text-sm text-muted-foreground">{alert.description}</p>
                <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  {new Date(alert.timestamp).toLocaleString()}
                </div>
                {alert.related_signals.length > 0 && (
                  <div className="flex gap-1 flex-wrap">
                    {alert.related_signals.map((s) => (
                      <span
                        key={s}
                        className="text-[10px] px-2 py-1 bg-muted rounded-md text-muted-foreground font-mono"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}

          {/* Linked Telemetry */}
          <div className="border-t border-border pt-4">
            <h4 className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider">
              Linked Telemetry
            </h4>
            <div className="h-[150px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={contextData}>
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 8 }}
                    tickLine={false}
                    axisLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fontSize: 8 }}
                    tickLine={false}
                    axisLine={false}
                    width={30}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(220, 18%, 12%)",
                      border: "1px solid hsl(220, 14%, 18%)",
                      borderRadius: "6px",
                      fontSize: "10px",
                      color: "hsl(210, 20%, 92%)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="vibration"
                    stroke="hsl(0, 72%, 55%)"
                    strokeWidth={1}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="wob"
                    stroke="hsl(187, 85%, 53%)"
                    strokeWidth={1}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
