import { useDashboard } from "@/lib/dashboard-context";
import { AlertsFeed } from "@/components/AlertsFeed";
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";
import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { AlertCircle } from "lucide-react";
import type { AlertSeverity } from "@/lib/types";

export function AlertsView() {
  const { alerts, selectedAlert, telemetry, unreadAlertCount } = useDashboard();
  const [filter, setFilter] = useState<AlertSeverity | "ALL" | "UNREAD">("ALL");

  const unreadAlerts = useMemo(() => alerts.filter((a) => !a.isRead), [alerts]);

  const contextData = useMemo(() => {
    return telemetry.slice(-60).map((p) => ({
      time: new Date(p.timestamp).toLocaleTimeString("en-US", {
        hour12: false,
        second: "2-digit",
        minute: "2-digit",
        hour: "2-digit",
      }),
      vibration: p.vibration_g,
      rpm: p.rpm,
      wob: p.wob_klbf,
    }));
  }, [telemetry]);

  const filters: {
    label: string;
    value: AlertSeverity | "ALL" | "UNREAD";
    count?: number;
  }[] = [
    { label: "All", value: "ALL", count: alerts.length },
    {
      label: "Critical",
      value: "CRITICAL",
      count: alerts.filter((a) => a.severity === "CRITICAL").length,
    },
    {
      label: "Warning",
      value: "WARN",
      count: alerts.filter((a) => a.severity === "WARN").length,
    },
    {
      label: "Info",
      value: "INFO",
      count: alerts.filter((a) => a.severity === "INFO").length,
    },
    { label: "Unread", value: "UNREAD", count: unreadAlertCount },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
      <div className="lg:col-span-5 space-y-3">
        {/* Unread Section */}
        {unreadAlerts.length > 0 && (
          <div className="bg-signal-red/10 border border-signal-red/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="h-4 w-4 text-signal-red" />
              <h3 className="text-sm font-semibold text-signal-red">
                Unread Alerts ({unreadAlertCount})
              </h3>
            </div>
            <div className="space-y-2 max-h-[150px] overflow-y-auto">
              <AlertsFeed filter="UNREAD" />
            </div>
          </div>
        )}

        {/* Alert Stream */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold">Alert Stream</h2>
            <div className="flex gap-1 flex-wrap">
              {filters.map((f) => (
                <button
                  key={f.value}
                  onClick={() => setFilter(f.value)}
                  className={cn(
                    "text-[10px] px-2 py-1 rounded font-medium transition-colors flex items-center gap-1",
                    filter === f.value
                      ? "bg-primary/20 text-primary"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {f.label}
                  {f.count !== undefined && f.count > 0 && (
                    <span
                      className={cn(
                        "text-[8px] font-bold px-1 py-0 rounded-full",
                        filter === f.value ? "bg-primary/30" : "bg-muted"
                      )}
                    >
                      {f.count}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
          <div className="max-h-[calc(100vh-380px)] overflow-y-auto pr-1">
            <AlertsFeed filter={filter} />
          </div>
        </div>
      </div>

      <div className="lg:col-span-7 space-y-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
            Signal Context
          </h3>
          {["vibration", "rpm", "wob"].map((signal, idx) => (
            <div key={signal} className="mb-4">
              <p className="text-[10px] text-muted-foreground uppercase mb-1">{signal}</p>
              <div className="h-[80px]">
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
                      dataKey={signal}
                      stroke={
                        ["hsl(0, 72%, 55%)", "hsl(45, 93%, 58%)", "hsl(187, 85%, 53%)"][
                          idx
                        ]
                      }
                      strokeWidth={1.5}
                      dot={false}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          ))}
        </div>

        {selectedAlert && (
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
              Selected Alert
            </h3>
            <p className="text-sm font-medium">{selectedAlert.title}</p>
            <p className="text-xs text-muted-foreground mt-1">
              {selectedAlert.description}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
