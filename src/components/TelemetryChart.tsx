import { useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { useDashboard } from '@/lib/dashboard-context';
import { OPERATING_LIMITS } from '@/lib/mock-data';
import { cn } from '@/lib/utils';

const SIGNALS = [
  { key: 'wob_klbf', label: 'WOB', unit: 'klbf', color: 'hsl(187, 85%, 53%)', limit: OPERATING_LIMITS.wob_range[1] },
  { key: 'torque_kftlb', label: 'Torque', unit: 'kft·lb', color: 'hsl(142, 70%, 49%)', limit: OPERATING_LIMITS.torque_range[1] },
  { key: 'rpm', label: 'RPM', unit: 'rpm', color: 'hsl(45, 93%, 58%)', limit: OPERATING_LIMITS.rpm_range[1] },
  { key: 'vibration_g', label: 'Vibration', unit: 'g', color: 'hsl(0, 72%, 55%)', limit: OPERATING_LIMITS.max_vibration_g },
  { key: 'inclination_deg', label: 'Inclination', unit: '°', color: 'hsl(270, 70%, 60%)' },
  { key: 'azimuth_deg', label: 'Azimuth', unit: '°', color: 'hsl(210, 90%, 60%)' },
  { key: 'rop_ft_hr', label: 'ROP', unit: 'ft/hr', color: 'hsl(32, 95%, 55%)' },
  { key: 'dls_deg_100ft', label: 'DLS', unit: '°/100ft', color: 'hsl(330, 70%, 55%)', limit: OPERATING_LIMITS.max_dls_deg_100ft },
] as const;

export function TelemetryChart() {
  const { telemetry, samplingRate, setSamplingRate } = useDashboard();
  const [activeSignal, setActiveSignal] = useState(0);
  const signal = SIGNALS[activeSignal];

  const chartData = useMemo(() => {
    const sliceCount = samplingRate === '10Hz' ? 600 : 180;
    return telemetry.slice(-sliceCount).map((p) => ({
      time: new Date(p.timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      value: (p as any)[signal.key],
    }));
  }, [telemetry, signal.key, samplingRate]);

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Telemetry</h3>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setSamplingRate('1Hz')}
            className={cn("text-[10px] px-2 py-1 rounded font-medium transition-colors",
              samplingRate === '1Hz' ? "bg-primary/20 text-primary" : "text-muted-foreground hover:text-foreground"
            )}
          >Last 30m (1Hz)</button>
          <button
            onClick={() => setSamplingRate('10Hz')}
            className={cn("text-[10px] px-2 py-1 rounded font-medium transition-colors",
              samplingRate === '10Hz' ? "bg-primary/20 text-primary" : "text-muted-foreground hover:text-foreground"
            )}
          >Last 60s (10Hz)</button>
        </div>
      </div>

      <div className="flex gap-1 mb-3 flex-wrap">
        {SIGNALS.map((s, i) => (
          <button
            key={s.key}
            onClick={() => setActiveSignal(i)}
            className={cn(
              "text-[10px] px-2 py-1 rounded-md font-medium transition-all",
              i === activeSignal
                ? "text-foreground border border-border"
                : "text-muted-foreground hover:text-foreground"
            )}
            style={i === activeSignal ? { backgroundColor: `${s.color}20`, borderColor: `${s.color}40` } : {}}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div className="h-[240px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
            <XAxis
              dataKey="time"
              tick={{ fontSize: 9, fill: 'hsl(215, 15%, 55%)' }}
              tickLine={false}
              axisLine={{ stroke: 'hsl(220, 14%, 18%)' }}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 9, fill: 'hsl(215, 15%, 55%)' }}
              tickLine={false}
              axisLine={false}
              width={40}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(220, 18%, 12%)',
                border: '1px solid hsl(220, 14%, 18%)',
                borderRadius: '6px',
                fontSize: '11px',
                color: 'hsl(210, 20%, 92%)',
              }}
              labelStyle={{ color: 'hsl(215, 15%, 55%)', fontSize: '10px' }}
              formatter={(v: number) => [`${v.toFixed(2)} ${signal.unit}`, signal.label]}
            />
            {'limit' in signal && signal.limit && (
              <ReferenceLine
                y={signal.limit}
                stroke="hsl(0, 72%, 55%)"
                strokeDasharray="4 4"
                strokeOpacity={0.5}
              />
            )}
            <Line
              type="monotone"
              dataKey="value"
              stroke={signal.color}
              strokeWidth={1.5}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
