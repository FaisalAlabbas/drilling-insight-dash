export type UserRole = 'Operator' | 'Engineer' | 'Admin';

export type SteeringCommand = 'Hold' | 'Build' | 'Drop' | 'Turn Left' | 'Turn Right';
export type GateOutcome = 'ACCEPTED' | 'REJECTED';
export type RejectionReason = 'LOW_CONFIDENCE' | 'MISSING_DATA' | 'SENSOR_ANOMALY' | 'LIMIT_EXCEEDED' | null;
export type ExecutionStatus = 'SENT' | 'BLOCKED';
export type FallbackMode = 'HOLD_STEERING' | 'MANUAL_FALLBACK' | null;
export type AlertSeverity = 'INFO' | 'WARN' | 'CRITICAL';
export type EdgeHealth = 'Healthy' | 'Degraded';
export type SamplingRate = '1Hz' | '10Hz';

export interface TelemetryPacket {
  timestamp: string;
  wob_klbf: number;
  torque_kftlb: number;
  rpm: number;
  vibration_g: number;
  inclination_deg: number;
  azimuth_deg: number;
  rop_ft_hr: number;
  dls_deg_100ft: number;
}

export interface FeatureVector {
  mean_wob: number;
  std_wob: number;
  mean_torque: number;
  std_torque: number;
  mean_rpm: number;
  std_rpm: number;
  mean_vibration: number;
  std_vibration: number;
  trend_inclination: number;
  trend_azimuth: number;
  instability_proxy: number;
}

export interface AIOutput {
  steering_command: SteeringCommand;
  confidence_score: number;
}

export interface SafetyGate {
  gate_outcome: GateOutcome;
  rejection_reason: RejectionReason;
  execution_status: ExecutionStatus;
  fallback_mode: FallbackMode;
}

export interface DecisionRecord {
  timestamp: string;
  model_version: string;
  feature_summary: FeatureVector;
  steering_command: SteeringCommand;
  confidence_score: number;
  gate_outcome: GateOutcome;
  rejection_reason: RejectionReason;
  execution_status: ExecutionStatus;
  fallback_mode: FallbackMode;
  event_tags: string[];
}

export interface AlertEvent {
  id: string;
  timestamp: string;
  severity: AlertSeverity;
  title: string;
  description: string;
  related_signals: string[];
  linked_log_timestamp: string;
}

export interface OperatingLimits {
  max_vibration_g: number;
  max_dls_deg_100ft: number;
  wob_range: [number, number];
  torque_range: [number, number];
  rpm_range: [number, number];
}

export interface RunSummary {
  id: string;
  date: string;
  well_name: string;
  count_decisions: number;
  accept_rate: number;
  reject_rate: number;
  avg_confidence: number;
  critical_alerts: number;
}

export interface UserRecord {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: 'Active' | 'Inactive';
}
