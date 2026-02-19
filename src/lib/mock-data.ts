import type {
  TelemetryPacket, DecisionRecord, AlertEvent, FeatureVector,
  SteeringCommand, GateOutcome, RejectionReason, FallbackMode,
  AlertSeverity, RunSummary, UserRecord, OperatingLimits
} from './types';

// Utility helpers
const rand = (min: number, max: number) => Math.random() * (max - min) + min;
const randInt = (min: number, max: number) => Math.floor(rand(min, max + 1));
const pick = <T>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

let inclinationDrift = 45;
let azimuthDrift = 180;

export const OPERATING_LIMITS: OperatingLimits = {
  max_vibration_g: 5.0,
  max_dls_deg_100ft: 8.0,
  wob_range: [5, 35],
  torque_range: [2, 20],
  rpm_range: [60, 220],
};

export function generateTelemetryPacket(timestamp: Date): TelemetryPacket {
  inclinationDrift += rand(-0.05, 0.05);
  inclinationDrift = Math.max(0, Math.min(90, inclinationDrift));
  azimuthDrift += rand(-0.1, 0.1);
  azimuthDrift = ((azimuthDrift % 360) + 360) % 360;

  const vibration = Math.random() < 0.05 ? rand(4.5, 6.5) : rand(0.2, 3.5);

  return {
    timestamp: timestamp.toISOString(),
    wob_klbf: Math.round(rand(8, 30) * 10) / 10,
    torque_kftlb: Math.round(rand(4, 16) * 10) / 10,
    rpm: randInt(80, 200),
    vibration_g: Math.round(vibration * 100) / 100,
    inclination_deg: Math.round(inclinationDrift * 100) / 100,
    azimuth_deg: Math.round(azimuthDrift * 100) / 100,
    rop_ft_hr: Math.round(rand(15, 95) * 10) / 10,
    dls_deg_100ft: Math.round(rand(0.5, 7) * 100) / 100,
  };
}

export function generateTelemetrySeries(count: number, intervalMs: number): TelemetryPacket[] {
  const now = Date.now();
  return Array.from({ length: count }, (_, i) => {
    const ts = new Date(now - (count - 1 - i) * intervalMs);
    return generateTelemetryPacket(ts);
  });
}

function generateFeatureVector(packets: TelemetryPacket[]): FeatureVector {
  const mean = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;
  const std = (arr: number[]) => {
    const m = mean(arr);
    return Math.sqrt(arr.reduce((s, v) => s + (v - m) ** 2, 0) / arr.length);
  };

  const wobs = packets.map(p => p.wob_klbf);
  const torques = packets.map(p => p.torque_kftlb);
  const rpms = packets.map(p => p.rpm);
  const vibs = packets.map(p => p.vibration_g);

  return {
    mean_wob: Math.round(mean(wobs) * 100) / 100,
    std_wob: Math.round(std(wobs) * 100) / 100,
    mean_torque: Math.round(mean(torques) * 100) / 100,
    std_torque: Math.round(std(torques) * 100) / 100,
    mean_rpm: Math.round(mean(rpms) * 100) / 100,
    std_rpm: Math.round(std(rpms) * 100) / 100,
    mean_vibration: Math.round(mean(vibs) * 100) / 100,
    std_vibration: Math.round(std(vibs) * 100) / 100,
    trend_inclination: Math.round(rand(-0.5, 0.5) * 100) / 100,
    trend_azimuth: Math.round(rand(-1, 1) * 100) / 100,
    instability_proxy: Math.round((std(vibs) * std(rpms)) * 100) / 100,
  };
}

const COMMANDS: SteeringCommand[] = ['Hold', 'Build', 'Drop', 'Turn Left', 'Turn Right'];
const REJECTION_REASONS: RejectionReason[] = ['LOW_CONFIDENCE', 'MISSING_DATA', 'SENSOR_ANOMALY', 'LIMIT_EXCEEDED'];
const EVENT_TAGS = ['spike_detected', 'confidence_drop', 'high_vibration', 'dls_warning', 'torque_spike', 'rpm_fluctuation'];

export function generateDecisionRecord(timestamp: Date, packets: TelemetryPacket[]): DecisionRecord {
  const confidence = Math.round(rand(0.25, 0.98) * 100) / 100;
  const isRejected = confidence < 0.5 || Math.random() < 0.15;
  const gate_outcome: GateOutcome = isRejected ? 'REJECTED' : 'ACCEPTED';
  const rejection_reason: RejectionReason = isRejected ? pick(REJECTION_REASONS) : null;
  const fallback_mode: FallbackMode = isRejected ? pick(['HOLD_STEERING', 'MANUAL_FALLBACK'] as FallbackMode[]) : null;

  const tags: string[] = [];
  if (confidence < 0.5) tags.push('confidence_drop');
  if (packets.some(p => p.vibration_g > 4.5)) tags.push('spike_detected', 'high_vibration');
  if (tags.length === 0 && Math.random() < 0.2) tags.push(pick(EVENT_TAGS));

  return {
    timestamp: timestamp.toISOString(),
    model_version: 'edge-ai-rss-v1.3.2',
    feature_summary: generateFeatureVector(packets),
    steering_command: pick(COMMANDS),
    confidence_score: confidence,
    gate_outcome,
    rejection_reason,
    execution_status: isRejected ? 'BLOCKED' : 'SENT',
    fallback_mode,
    event_tags: tags,
  };
}

export function generateDecisionSeries(count: number): DecisionRecord[] {
  const now = Date.now();
  return Array.from({ length: count }, (_, i) => {
    const ts = new Date(now - (count - 1 - i) * 5000);
    const packets = generateTelemetrySeries(5, 1000);
    return generateDecisionRecord(ts, packets);
  });
}

const ALERT_TEMPLATES: { title: string; description: string; severity: AlertSeverity; signals: string[] }[] = [
  { title: 'Vibration spike detected', description: 'Lateral vibration exceeded 5.0g threshold at near-bit sensor', severity: 'CRITICAL', signals: ['vibration_g', 'rpm'] },
  { title: 'Confidence dropped below threshold', description: 'AI model confidence fell to 0.41, below the 0.50 operating minimum', severity: 'WARN', signals: ['confidence_score'] },
  { title: 'Gate blocked command: LIMIT_EXCEEDED', description: 'Safety gate rejected steering command due to DLS exceeding 8.0°/100ft', severity: 'CRITICAL', signals: ['dls_deg_100ft', 'inclination_deg'] },
  { title: 'RPM fluctuation detected', description: 'Rotational speed variance exceeded normal operating band (±15 RPM)', severity: 'WARN', signals: ['rpm', 'torque_kftlb'] },
  { title: 'Sensor data gap: MWD', description: 'MWD telemetry gap of 8 seconds detected, possible signal attenuation', severity: 'WARN', signals: ['inclination_deg', 'azimuth_deg'] },
  { title: 'WOB approaching upper limit', description: 'Weight on bit at 33.5 klbf, nearing 35.0 klbf operational limit', severity: 'INFO', signals: ['wob_klbf'] },
  { title: 'Torque spike: possible stall', description: 'Torque spiked to 18.7 kft·lb with corresponding RPM drop', severity: 'CRITICAL', signals: ['torque_kftlb', 'rpm'] },
  { title: 'DLS warning: approaching limit', description: 'Dogleg severity at 7.2°/100ft, approaching 8.0°/100ft limit', severity: 'WARN', signals: ['dls_deg_100ft'] },
  { title: 'Edge AI model reloaded', description: 'Model edge-ai-rss-v1.3.2 reloaded after transient error recovery', severity: 'INFO', signals: [] },
  { title: 'ROP degradation detected', description: 'Rate of penetration dropped 40% over last 5 minutes, possible formation change', severity: 'INFO', signals: ['rop_ft_hr', 'wob_klbf'] },
];

export function generateAlerts(count: number): AlertEvent[] {
  const now = Date.now();
  return Array.from({ length: count }, (_, i) => {
    const template = pick(ALERT_TEMPLATES);
    const ts = new Date(now - i * randInt(30000, 180000));
    return {
      id: `ALT-${String(1000 + i).padStart(4, '0')}`,
      timestamp: ts.toISOString(),
      severity: template.severity,
      title: template.title,
      description: template.description,
      related_signals: template.signals,
      linked_log_timestamp: ts.toISOString(),
    };
  });
}

export function generateRunSummaries(): RunSummary[] {
  const wells = ['Permian-H7', 'Eagle Ford-12', 'Bakken-A3', 'Marcellus-W9', 'Midland-D5'];
  return wells.map((well, i) => {
    const decisions = randInt(200, 800);
    const acceptRate = Math.round(rand(0.7, 0.95) * 100) / 100;
    return {
      id: `RUN-${String(100 + i).padStart(4, '0')}`,
      date: new Date(Date.now() - i * 86400000 * randInt(1, 5)).toISOString().split('T')[0],
      well_name: well,
      count_decisions: decisions,
      accept_rate: acceptRate,
      reject_rate: Math.round((1 - acceptRate) * 100) / 100,
      avg_confidence: Math.round(rand(0.6, 0.88) * 100) / 100,
      critical_alerts: randInt(0, 12),
    };
  });
}

export function generateUsers(): UserRecord[] {
  return [
    { id: '1', name: 'James Mitchell', email: 'j.mitchell@drillingops.com', role: 'Admin', status: 'Active' },
    { id: '2', name: 'Sarah Chen', email: 's.chen@drillingops.com', role: 'Engineer', status: 'Active' },
    { id: '3', name: 'Mike Rodriguez', email: 'm.rodriguez@drillingops.com', role: 'Operator', status: 'Active' },
    { id: '4', name: 'Emily Watson', email: 'e.watson@drillingops.com', role: 'Engineer', status: 'Active' },
    { id: '5', name: 'David Park', email: 'd.park@drillingops.com', role: 'Operator', status: 'Inactive' },
  ];
}
