import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Activity,
  ShieldCheck,
  Cpu,
  TrendingDown,
  Info,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import { fetchModelMetrics, fetchDecisionStats, checkBackendHealth } from "@/lib/api-service";

const OUTCOME_COLORS: Record<string, string> = {
  ACCEPTED: "#10b981",
  REDUCED: "#f59e0b",
  REJECTED: "#ef4444",
};

const ACTUATOR_COLORS: Record<string, string> = {
  ACK_EXECUTED: "#10b981",
  ACK_REDUCED: "#f59e0b",
  ACK_REJECTED: "#ef4444",
  ACK_BLOCKED: "#6b7280",
  ACK_MANUAL_FALLBACK: "#f97316",
};

function MetricCard({
  label,
  value,
  sub,
  estimated,
  color,
}: {
  label: string;
  value: string | number;
  sub?: string;
  estimated?: boolean;
  color?: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
          {label}
          {estimated && (
            <Badge variant="outline" className="text-[9px] px-1 py-0 font-normal">
              Estimated
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${color ?? ""}`}>{value}</div>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </CardContent>
    </Card>
  );
}

export function Verification() {
  const {
    data: metrics,
    isLoading: metricsLoading,
    error: metricsError,
  } = useQuery({
    queryKey: ["model-metrics"],
    queryFn: async () => {
      const result = await fetchModelMetrics();
      if (!result) throw new Error("Failed to fetch model metrics");
      return result;
    },
    retry: 3,
    retryDelay: 2000,
    refetchInterval: 30000,
  });

  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery({
    queryKey: ["decision-stats"],
    queryFn: async () => {
      const result = await fetchDecisionStats();
      if (!result) throw new Error("Failed to fetch decision stats");
      return result;
    },
    retry: 3,
    retryDelay: 2000,
    refetchInterval: 15000,
  });

  const { data: health } = useQuery({
    queryKey: ["backend-health"],
    queryFn: () => checkBackendHealth(),
    refetchInterval: 30000,
  });

  const isLoading = metricsLoading || statsLoading;
  const hasError = metricsError || statsError;

  // Derive gate outcome chart data
  const outcomeData = stats?.by_outcome
    ? Object.entries(stats.by_outcome).map(([name, value]) => ({
        name,
        count: value,
        fill: OUTCOME_COLORS[name] ?? "#6b7280",
      }))
    : [];

  // Derive actuator outcome chart data
  const actuatorData = stats?.actuator_counts
    ? Object.entries(stats.actuator_counts).map(([name, value]) => ({
        name: name.replace("ACK_", ""),
        fullName: name,
        count: value,
        fill: ACTUATOR_COLORS[name] ?? "#6b7280",
      }))
    : [];

  // Total actuator acks
  const totalActuatorAcks = actuatorData.reduce((s, d) => s + d.count, 0);

  // Estimated metrics (clearly labeled)
  const totalDecisions = stats?.total_decisions ?? 0;
  const acceptedCount = stats?.by_outcome?.ACCEPTED ?? 0;
  // Estimated system availability: % of time backend healthy (simple proxy)
  const estimatedAvailability = health?.status === "healthy" ? 99.5 : health?.status === "degraded" ? 95.0 : 0;
  // Estimated NPT reduction: based on rejection rate avoidance
  const rejectedCount = stats?.by_outcome?.REJECTED ?? 0;
  const estimatedNptReduction = totalDecisions > 0
    ? ((rejectedCount / totalDecisions) * 15).toFixed(1) // Each rejection avoids ~15% of potential NPT
    : "N/A";

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <ShieldCheck className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                Verification & Attainment
              </h1>
              <p className="text-muted-foreground">
                Engineering evidence for system performance and safety compliance
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {stats?.system_mode && (
              <Badge
                variant="outline"
                className={
                  stats.system_mode === "PROTOTYPE"
                    ? "border-signal-green text-signal-green"
                    : "border-cyan-400 text-cyan-400"
                }
              >
                {stats.system_mode} Mode
              </Badge>
            )}
            {health && (
              <Badge
                variant="outline"
                className={
                  health.status === "healthy"
                    ? "border-signal-green text-signal-green"
                    : health.status === "degraded"
                      ? "border-signal-yellow text-signal-yellow"
                      : "border-signal-red text-signal-red"
                }
              >
                Backend: {health.status}
              </Badge>
            )}
            {metrics?.model_version && (
              <Badge variant="outline">Model: {metrics.model_version}</Badge>
            )}
          </div>
        </div>

        {/* Error State */}
        {hasError && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Unable to load some metrics. Ensure the backend is running.
              {metricsError && " Model metrics unavailable."}
              {statsError && " Decision stats unavailable."}
            </AlertDescription>
          </Alert>
        )}

        {/* Loading State */}
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-muted-foreground">Loading verification data...</div>
          </div>
        ) : (
          <>
            {/* ===== Section 1: Model Performance ===== */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-signal-green" />
                  Model Performance
                </CardTitle>
                <CardDescription>
                  Metrics from model training evaluation on held-out test set
                </CardDescription>
              </CardHeader>
              <CardContent>
                {metrics?.available === false ? (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Info className="h-4 w-4" />
                    <span>Model not trained yet. Run train.py to generate metrics.</span>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <MetricCard
                      label="Accuracy"
                      value={
                        metrics?.accuracy != null
                          ? (metrics.accuracy * 100).toFixed(1) + "%"
                          : "N/A"
                      }
                      sub={`Test set (${metrics?.dataset_info?.test_samples ?? "?"} samples)`}
                    />
                    <MetricCard
                      label="Macro F1"
                      value={metrics?.macro_f1 != null ? metrics.macro_f1.toFixed(4) : "N/A"}
                      sub="Unweighted average across classes"
                    />
                    <MetricCard
                      label="Weighted F1"
                      value={
                        metrics?.weighted_f1 != null ? metrics.weighted_f1.toFixed(4) : "N/A"
                      }
                      sub="Sample-weighted average"
                    />
                    <MetricCard
                      label="Training Samples"
                      value={metrics?.dataset_info?.total_samples ?? "N/A"}
                      sub={`${metrics?.dataset_info?.train_samples ?? "?"} train / ${metrics?.dataset_info?.test_samples ?? "?"} test`}
                    />
                  </div>
                )}
              </CardContent>
            </Card>

            {/* ===== Section 2: Decision Pipeline ===== */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-primary" />
                  Decision Pipeline
                </CardTitle>
                <CardDescription>
                  Gate outcomes and decision statistics over the last{" "}
                  {stats?.time_range_days ?? 30} days
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <MetricCard
                    label="Total Decisions"
                    value={totalDecisions}
                    sub={`Last ${stats?.time_range_days ?? 30} days`}
                  />
                  <MetricCard
                    label="Accepted"
                    value={acceptedCount}
                    color="text-signal-green"
                  />
                  <MetricCard
                    label="Reduced"
                    value={stats?.by_outcome?.REDUCED ?? 0}
                    color="text-signal-yellow"
                  />
                  <MetricCard
                    label="Rejected"
                    value={rejectedCount}
                    color="text-signal-red"
                  />
                  <MetricCard
                    label="Avg Confidence"
                    value={
                      stats?.avg_confidence != null
                        ? (stats.avg_confidence * 100).toFixed(1) + "%"
                        : "N/A"
                    }
                  />
                </div>

                {/* Gate Outcome Distribution Chart */}
                {outcomeData.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold mb-3">
                      Gate Outcome Distribution
                    </h3>
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={outcomeData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis dataKey="name" tick={{ fill: "#999", fontSize: 12 }} />
                        <YAxis tick={{ fill: "#999", fontSize: 12 }} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#1a1a2e",
                            border: "1px solid #333",
                            borderRadius: "6px",
                          }}
                        />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                          {outcomeData.map((entry, i) => (
                            <Cell key={i} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* ===== Section 3: Actuator & Safety ===== */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5 text-cyan-400" />
                  Actuator & Safety
                </CardTitle>
                <CardDescription>
                  Virtual actuator acknowledgements and safety metrics
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <MetricCard
                    label="Actuator ACKs"
                    value={totalActuatorAcks}
                    sub="Total command acknowledgements"
                  />
                  <MetricCard
                    label="Anomaly Count"
                    value={stats?.anomaly_count ?? 0}
                    sub="Rejected decisions (safety triggers)"
                    color={
                      (stats?.anomaly_count ?? 0) > 0 ? "text-signal-red" : undefined
                    }
                  />
                  <MetricCard
                    label="Envelope Violations"
                    value={stats?.envelope_violations ?? 0}
                    sub="PETE operating envelope breaches"
                    color={
                      (stats?.envelope_violations ?? 0) > 0
                        ? "text-signal-red"
                        : undefined
                    }
                  />
                  <MetricCard
                    label="Actuator State"
                    value={stats?.actuator_state?.state ?? "UNKNOWN"}
                    sub={
                      stats?.actuator_state?.is_simulated
                        ? "Simulated actuator"
                        : "Hardware actuator"
                    }
                    color={
                      stats?.actuator_state?.state === "FAULT"
                        ? "text-signal-red"
                        : stats?.actuator_state?.state === "MANUAL"
                          ? "text-signal-amber"
                          : "text-signal-green"
                    }
                  />
                </div>

                {/* Actuator Outcome Pie Chart */}
                {actuatorData.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold mb-3">
                      Actuator Outcome Breakdown
                    </h3>
                    <ResponsiveContainer width="100%" height={280}>
                      <PieChart>
                        <Pie
                          data={actuatorData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, count }) => `${name}: ${count}`}
                          outerRadius={100}
                          dataKey="count"
                        >
                          {actuatorData.map((entry, i) => (
                            <Cell key={i} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#1a1a2e",
                            border: "1px solid #333",
                            borderRadius: "6px",
                          }}
                          formatter={(value: number, _name: string, props: { payload?: { fullName?: string } }) => [
                            value,
                            props.payload?.fullName ?? _name,
                          ]}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* ===== Section 4: Estimated / Derived Metrics ===== */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingDown className="h-5 w-5 text-signal-amber" />
                  Estimated Metrics
                </CardTitle>
                <CardDescription>
                  Derived values based on operational data. These are approximations,
                  not directly measured.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Alert className="mb-4">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    The metrics below are <strong>estimated</strong> from available
                    system data. They are not directly measured and should be treated as
                    indicative, not authoritative.
                  </AlertDescription>
                </Alert>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <MetricCard
                    label="System Availability"
                    value={estimatedAvailability + "%"}
                    sub="Based on current backend health status"
                    estimated
                  />
                  <MetricCard
                    label="Est. NPT Reduction"
                    value={
                      estimatedNptReduction !== "N/A"
                        ? estimatedNptReduction + "%"
                        : "N/A"
                    }
                    sub="Projected from safety gate rejection rate"
                    estimated
                  />
                  <MetricCard
                    label="Est. DLS Trend"
                    value={
                      totalDecisions > 0
                        ? acceptedCount > rejectedCount
                          ? "Stable"
                          : "Elevated"
                        : "N/A"
                    }
                    sub="Inferred from acceptance/rejection ratio"
                    estimated
                    color={
                      acceptedCount > rejectedCount
                        ? "text-signal-green"
                        : "text-signal-amber"
                    }
                  />
                </div>
              </CardContent>
            </Card>

            {/* ===== Section 5: Per-Class Performance Table ===== */}
            {metrics?.per_class_metrics && (
              <Card>
                <CardHeader>
                  <CardTitle>Per-Class Model Performance</CardTitle>
                  <CardDescription>
                    Precision, recall, and F1 for each steering command class
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-2">Class</th>
                          <th className="text-center py-2 px-2">Precision</th>
                          <th className="text-center py-2 px-2">Recall</th>
                          <th className="text-center py-2 px-2">F1-Score</th>
                          <th className="text-center py-2 px-2">Support</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(metrics.per_class_metrics).map(
                          ([cls, m], idx) => (
                            <tr
                              key={cls}
                              className={idx % 2 === 0 ? "bg-muted/50" : ""}
                            >
                              <td className="py-2 px-2 font-medium">{cls}</td>
                              <td className="text-center py-2 px-2">
                                {m.precision.toFixed(3)}
                              </td>
                              <td className="text-center py-2 px-2">
                                {m.recall.toFixed(3)}
                              </td>
                              <td className="text-center py-2 px-2">
                                {m.f1.toFixed(3)}
                              </td>
                              <td className="text-center py-2 px-2">{m.support}</td>
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default Verification;
