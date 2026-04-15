import { useDashboard } from "@/lib/dashboard-context";
import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { Download, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { SteeringCommand } from "@/lib/api-types";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

export function ReportingView() {
  const { decisions, alerts, telemetry } = useDashboard();
  const [reportType, setReportType] = useState<"performance" | "safety" | "operations">(
    "performance"
  );

  const stats = useMemo(() => {
    const totalDecisions = decisions.length;
    const acceptedDecisions = decisions.filter(
      (d) => d.gate_outcome === "ACCEPTED"
    ).length;
    const avgConfidence =
      totalDecisions > 0
        ? decisions.reduce((sum, d) => sum + d.confidence_score, 0) / totalDecisions
        : 0;

    const criticalAlerts = alerts.filter((a) => a.severity === "critical").length;
    const warningAlerts = alerts.filter((a) => a.severity === "high").length;

    const commandCounts: Record<SteeringCommand, number> = {
      "No Change": 0,
      "Move Upward": 0,
      "Move Downward": 0,
      "Turn Left": 0,
      "Turn Right": 0,
    };
    decisions.forEach((d) => {
      commandCounts[d.steering_command] = (commandCounts[d.steering_command] || 0) + 1;
    });

    const rejectionReasons = decisions
      .filter((d) => d.rejection_reason)
      .reduce(
        (acc, d) => {
          const key = d.rejection_reason || "UNKNOWN";
          acc[key] = (acc[key] || 0) + 1;
          return acc;
        },
        {} as Record<string, number>
      );

    return {
      totalDecisions,
      acceptedDecisions,
      acceptanceRate: totalDecisions > 0 ? (acceptedDecisions / totalDecisions) * 100 : 0,
      avgConfidence: avgConfidence * 100,
      criticalAlerts,
      warningAlerts,
      commandCounts,
      rejectionReasons,
    };
  }, [decisions, alerts]);

  const confidenceChart = useMemo(() => {
    const hourAgo = Date.now() - 60 * 60 * 1000;
    const recentDecisions = decisions.filter(
      (d) => new Date(d.timestamp).getTime() > hourAgo
    );

    const grouped = Array.from({ length: 12 }, (_, i) => {
      const time = new Date(hourAgo + i * 5 * 60 * 1000);
      const interval = recentDecisions.filter((d) => {
        const dt = new Date(d.timestamp).getTime();
        return dt >= time.getTime() && dt < time.getTime() + 5 * 60 * 1000;
      });

      return {
        time: time.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
        avgConfidence:
          interval.length > 0
            ? (interval.reduce((sum, d) => sum + d.confidence_score, 0) /
                interval.length) *
              100
            : 0,
        count: interval.length,
      };
    });

    return grouped;
  }, [decisions]);

  const commandChart = useMemo(() => {
    return Object.entries(stats.commandCounts).map(([command, count]) => ({
      command,
      count,
      percentage: ((count / stats.totalDecisions) * 100).toFixed(1),
    }));
  }, [stats]);

  const exportReport = () => {
    const timestamp = new Date().toISOString().split("T")[0];
    let csv = "DRILLING INSIGHT REPORT\n";
    csv += `Generated: ${new Date().toLocaleString()}\n`;
    csv += `Report Type: ${reportType.toUpperCase()}\n\n`;

    csv += "=== SUMMARY STATISTICS ===\n";
    csv += `Total Decisions,${stats.totalDecisions}\n`;
    csv += `Accepted,${stats.acceptedDecisions}\n`;
    csv += `Acceptance Rate,${stats.acceptanceRate.toFixed(1)}%\n`;
    csv += `Average Confidence,${stats.avgConfidence.toFixed(1)}%\n`;
    csv += `Critical Alerts,${stats.criticalAlerts}\n`;
    csv += `Warning Alerts,${stats.warningAlerts}\n\n`;

    csv += "=== STEERING COMMANDS ===\n";
    csv += "Command,Count,Percentage\n";
    commandChart.forEach((item) => {
      csv += `${item.command},${item.count},${item.percentage}%\n`;
    });

    csv += "\n=== REJECTION REASONS ===\n";
    csv += "Reason,Count\n";
    Object.entries(stats.rejectionReasons).forEach(([reason, count]) => {
      csv += `${reason},${count}\n`;
    });

    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `drilling-report-${timestamp}.csv`;
    a.click();
  };

  return (
    <div className="space-y-4">
      {/* Report Type Selection */}
      <div className="bg-card border border-border rounded-lg p-3 flex items-center gap-2 flex-wrap">
        <span className="text-xs font-semibold text-muted-foreground">Report Type:</span>
        {(["performance", "safety", "operations"] as const).map((type) => (
          <button
            key={type}
            onClick={() => setReportType(type)}
            className={cn(
              "px-3 py-1.5 rounded text-xs font-medium transition-colors",
              reportType === type
                ? "bg-primary/20 text-primary"
                : "bg-muted text-muted-foreground hover:text-foreground"
            )}
          >
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </button>
        ))}
        <div className="flex-1" />
        <Button onClick={exportReport} size="sm" variant="outline" className="gap-2">
          <Download className="h-3.5 w-3.5" />
          Export Report
        </Button>
      </div>

      {/* Performance Report */}
      {reportType === "performance" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Decisions</p>
              <p className="text-xl font-bold mt-1">{stats.totalDecisions}</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">
                Acceptance Rate
              </p>
              <p className="text-xl font-bold mt-1 text-signal-green">
                {stats.acceptanceRate.toFixed(1)}%
              </p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">
                Avg Confidence
              </p>
              <p className="text-xl font-bold mt-1">{stats.avgConfidence.toFixed(1)}%</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Accepted</p>
              <p className="text-xl font-bold mt-1">{stats.acceptedDecisions}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-card border border-border rounded-lg p-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider mb-3">
                Confidence Trend (Last Hour)
              </h3>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={confidenceChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
                    <XAxis dataKey="time" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} domain={[0, 100]} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(220, 18%, 12%)",
                        border: "none",
                        borderRadius: "6px",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="avgConfidence"
                      stroke="hsl(210, 20%, 92%)"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider mb-3">
                Command Distribution
              </h3>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={commandChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
                    <XAxis
                      dataKey="command"
                      tick={{ fontSize: 9 }}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(220, 18%, 12%)",
                        border: "none",
                        borderRadius: "6px",
                      }}
                    />
                    <Bar
                      dataKey="count"
                      fill="hsl(210, 20%, 92%)"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Safety Report */}
      {reportType === "safety" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">
                Critical Alerts
              </p>
              <p className="text-xl font-bold mt-1 text-signal-red">
                {stats.criticalAlerts}
              </p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Warnings</p>
              <p className="text-xl font-bold mt-1 text-signal-yellow">
                {stats.warningAlerts}
              </p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Total Alerts</p>
              <p className="text-xl font-bold mt-1">
                {stats.criticalAlerts + stats.warningAlerts}
              </p>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider mb-3">
              Rejection Reasons
            </h3>
            <div className="space-y-2">
              {Object.entries(stats.rejectionReasons).length > 0 ? (
                Object.entries(stats.rejectionReasons)
                  .sort((a, b) => b[1] - a[1])
                  .map(([reason, count]) => (
                    <div
                      key={reason}
                      className="flex items-center justify-between p-2 bg-muted rounded"
                    >
                      <span className="text-sm font-medium">{reason}</span>
                      <span className="text-sm font-bold text-primary">{count}</span>
                    </div>
                  ))
              ) : (
                <p className="text-xs text-muted-foreground">No rejections recorded</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Operations Report */}
      {reportType === "operations" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">
                Telemetry Points
              </p>
              <p className="text-xl font-bold mt-1">{telemetry.length}</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">
                Model Decisions
              </p>
              <p className="text-xl font-bold mt-1">{stats.totalDecisions}</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Uptime Status</p>
              <p className="text-xl font-bold mt-1 text-signal-green">99.8%</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">System Health</p>
              <p className="text-xl font-bold mt-1 text-signal-green">Healthy</p>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-signal-green" />
              Key Metrics
            </h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">
                  Processing Duration
                </p>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold">24ms</span>
                  <span className="text-xs text-muted-foreground">avg per decision</span>
                </div>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">
                  Data Quality
                </p>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold">98.2%</span>
                  <span className="text-xs text-muted-foreground">valid samples</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
