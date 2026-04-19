import { useMemo } from "react";
import { useDashboard } from "@/lib/dashboard-context";
import { TelemetryChart } from "@/components/TelemetryChart";
import { AIRecommendationCard } from "@/components/AIRecommendationCard";
import { ActuatorStatusCard } from "@/components/ActuatorStatusCard";
import { StatsCard } from "@/components/StatsCard";
import { RecentDecisions } from "@/components/RecentDecisions";

export function LiveMonitoringView() {
  const { telemetry } = useDashboard();

  const stats = useMemo(() => {
    const recent = telemetry.slice(-30);
    const prev = telemetry.slice(-60, -30);
    const avg = (arr: number[]) =>
      arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;

    const latest = recent[recent.length - 1];
    if (!latest) return [];

    const items = [
      {
        title: "WOB",
        key: "wob_klbf" as const,
        unit: "klbf",
        color: "hsl(187, 85%, 53%)",
      },
      {
        title: "Torque",
        key: "torque_kftlb" as const,
        unit: "kft·lb",
        color: "hsl(142, 70%, 49%)",
      },
      { title: "RPM", key: "rpm" as const, unit: "rpm", color: "hsl(45, 93%, 58%)" },
      {
        title: "Vibration",
        key: "vibration_g" as const,
        unit: "g",
        color: "hsl(0, 72%, 55%)",
        warn: 5.0,
      },
      {
        title: "ROP",
        key: "rop_ft_hr" as const,
        unit: "ft/hr",
        color: "hsl(32, 95%, 55%)",
      },
      {
        title: "Gamma Ray",
        key: "gamma_gapi" as const,
        unit: "gAPI",
        color: "hsl(54, 80%, 50%)",
      },
      {
        title: "Resistivity",
        key: "resistivity_ohm_m" as const,
        unit: "Ω·m",
        color: "hsl(200, 80%, 48%)",
      },
      {
        title: "DLS",
        key: "dls_deg_100ft" as const,
        unit: "°/100ft",
        color: "hsl(330, 70%, 55%)",
        warn: 8.0,
      },
    ];

    return items.map((item) => ({
      ...item,
      value: latest[item.key].toFixed(1),
      delta: avg(recent.map((p) => p[item.key])) - avg(prev.map((p) => p[item.key])),
      sparkData: recent.map((p) => p[item.key]),
      warning: item.warn ? latest[item.key] > item.warn : false,
    }));
  }, [telemetry]);

  return (
    <div className="space-y-4">
      {/* Main chart + AI card + Actuator */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <TelemetryChart />
        </div>
        <div className="space-y-4">
          <AIRecommendationCard />
          <ActuatorStatusCard />
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {stats.map((s) => (
          <StatsCard
            key={s.title}
            title={s.title}
            value={s.value}
            unit={s.unit}
            delta={s.delta}
            sparkData={s.sparkData}
            color={s.color}
            warning={s.warning}
          />
        ))}
      </div>

      {/* Recent decisions */}
      <RecentDecisions />
    </div>
  );
}
