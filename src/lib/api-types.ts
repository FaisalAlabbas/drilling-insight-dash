/**
 * Shared TypeScript types that match FastAPI response contracts exactly
 * These types are generated from the FastAPI Pydantic models
 */

// ============================================================================
// Telemetry Types
// ============================================================================

export interface TelemetryPacket {
  timestamp: string;
  depth_ft: number;
  wob_klbf: number;
  torque_kftlb: number;
  rpm: number;
  vibration_g: number;
  inclination_deg: number;
  azimuth_deg: number;
  rop_ft_hr: number;
  dls_deg_100ft: number;
  gamma_gapi: number;
  resistivity_ohm_m: number;
  phif: number;
  vsh: number;
  sw: number;
  klogh: number;
  formation_class: string;
}

export interface DataQualityMetrics {
  total_rows: number;
  missing_rate_by_column: Record<string, number>;
  gaps_detected: number;
  outlier_counts: Record<string, number>;
}

// ============================================================================
// Configuration Types
// ============================================================================

export interface Limits {
  confidence_reject_threshold: number;
  confidence_reduce_threshold: number;
  dls_reject_threshold: number;
  dls_reduce_threshold: number;
  vibration_reject_threshold: number;
  vibration_reduce_threshold: number;
  max_vibration_g: number;
  max_dls_deg_100ft: number;
  wob_range: [number, number];
  torque_range: [number, number];
  rpm_range: [number, number];
}

export interface ConfigResponse {
  sampling_rate_hz: number;
  limits: Limits;
  units: Record<string, string>;
}

// ============================================================================
// Decision & Model Types
// ============================================================================

export type SteeringCommand =
  | "No Change"
  | "Move Upward"
  | "Move Downward"
  | "Turn Left"
  | "Turn Right";

export type GateOutcome = "ACCEPTED" | "REDUCED" | "REJECTED";

export interface FeatureVector {
  [key: string]: number | string;
}

export interface DecisionRecord {
  timestamp: string;
  model_version: string;
  feature_summary: FeatureVector;
  steering_command: SteeringCommand;
  confidence_score: number;
  gate_outcome: GateOutcome;
  rejection_reason?: string | null;
  execution_status: string;
  fallback_mode?: string | null;
  event_tags: string[];
}

export interface PredictResponse {
  recommendation: string;
  confidence: number;
  gate_status: GateOutcome;
  alert_message: string;
  decision_record: DecisionRecord;
}

// ============================================================================
// Model Metrics Types
// ============================================================================

export interface PerClassMetric {
  precision: number;
  recall: number;
  f1: number;
  support: number;
}

export interface FeatureImportance {
  name: string;
  importance: number;
}

export interface ModelMetrics {
  available: boolean;
  message?: string;
  model_loaded?: boolean;
  model_version?: string;
  algorithm?: string;
  n_estimators?: number;
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  macro_f1?: number;
  weighted_f1?: number;
  per_class_metrics?: Record<string, PerClassMetric>;
  class_distribution?: Record<string, number>;
  feature_importances?: FeatureImportance[] | null;
  feature_names?: string[];
  timestamp?: string;
  dataset_info?: {
    total_samples: number;
    train_samples: number;
    test_samples: number;
    features: number;
    split_ratio?: number;
  };
}

// ============================================================================
// Health Check Types
// ============================================================================

export interface HealthCheckResponse {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  checks: Record<
    string,
    {
      status: string;
      details?: string;
    }
  >;
}

// ============================================================================
// Authentication Types
// ============================================================================

export interface Token {
  access_token: string;
  token_type: string;
}

export interface User {
  username: string;
  role: string;
  disabled?: boolean;
}

export interface UserCredentials {
  username: string;
  password: string;
}

// ============================================================================
// Alert Types
// ============================================================================

export type AlertSeverity = "low" | "medium" | "high" | "critical";
export type AlertStatus = "ACTIVE" | "ACKNOWLEDGED" | "RESOLVED";

export interface AlertEvent {
  id: string;
  timestamp: string;
  severity: AlertSeverity;
  status?: AlertStatus;
  title: string;
  description?: string;
  message?: string;
  alert_type?: string;
  threshold_value?: number;
  actual_value?: number;
  related_signals?: string[];
  linked_log_timestamp?: string;
  isRead?: boolean;
}

// ============================================================================
// Operating Limits
// ============================================================================

export interface OperatingLimits {
  max_vibration_g: number;
  max_dls_deg_100ft: number;
  wob_range: [number, number];
  torque_range: [number, number];
  rpm_range: [number, number];
}

// ============================================================================
// Run Summary & Stats
// ============================================================================

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
