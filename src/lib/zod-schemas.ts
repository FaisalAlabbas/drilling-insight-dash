/**
 * Zod validation schemas for all API responses
 * Ensures type safety and runtime validation of backend responses
 */

import { z } from "zod";

// ============================================================================
// Telemetry Schemas
// ============================================================================

export const TelemetryPacketSchema = z.object({
  timestamp: z.string().datetime(),
  depth_ft: z.number(),
  wob_klbf: z.number(),
  torque_kftlb: z.number(),
  rpm: z.number(),
  vibration_g: z.number(),
  inclination_deg: z.number(),
  azimuth_deg: z.number(),
  rop_ft_hr: z.number(),
  dls_deg_100ft: z.number(),
  gamma_gapi: z.number(),
  resistivity_ohm_m: z.number(),
  phif: z.number(),
  vsh: z.number(),
  sw: z.number(),
  klogh: z.number(),
  formation_class: z.string(),
});

export type TelemetryPacket = z.infer<typeof TelemetryPacketSchema>;

export const DataQualityMetricsSchema = z.object({
  total_rows: z.number().int().nonnegative(),
  missing_rate_by_column: z.record(z.string(), z.number().min(0).max(1)),
  gaps_detected: z.number().int().nonnegative(),
  outlier_counts: z.record(z.string(), z.number().int().nonnegative()),
});

export type DataQualityMetrics = z.infer<typeof DataQualityMetricsSchema>;

// ============================================================================
// Configuration Schemas
// ============================================================================

export const LimitsSchema = z.object({
  confidence_reject_threshold: z.number().min(0).max(1),
  confidence_reduce_threshold: z.number().min(0).max(1),
  dls_reject_threshold: z.number().positive(),
  dls_reduce_threshold: z.number().positive(),
  vibration_reject_threshold: z.number().positive(),
  vibration_reduce_threshold: z.number().positive(),
  max_vibration_g: z.number().positive(),
  max_dls_deg_100ft: z.number().positive(),
  wob_range: z.tuple([z.number(), z.number()]),
  torque_range: z.tuple([z.number(), z.number()]),
  rpm_range: z.tuple([z.number(), z.number()]),
});

export type Limits = z.infer<typeof LimitsSchema>;

export const ConfigResponseSchema = z.object({
  sampling_rate_hz: z.number().positive(),
  limits: LimitsSchema,
  units: z.record(z.string(), z.string()),
});

export type ConfigResponse = z.infer<typeof ConfigResponseSchema>;

// ============================================================================
// Decision & Model Schemas
// ============================================================================

export const SteeringCommandSchema = z.enum([
  "No Change",
  "Move Upward",
  "Move Downward",
  "Turn Left",
  "Turn Right",
]);

export type SteeringCommand = z.infer<typeof SteeringCommandSchema>;

export const GateOutcomeSchema = z.enum(["ACCEPTED", "REDUCED", "REJECTED"]);

export type GateOutcome = z.infer<typeof GateOutcomeSchema>;

export const FeatureVectorSchema = z.record(
  z.string(),
  z.union([z.number(), z.string()])
);

export type FeatureVector = z.infer<typeof FeatureVectorSchema>;

export const DecisionRecordSchema = z.object({
  timestamp: z.string().datetime(),
  model_version: z.string(),
  feature_summary: FeatureVectorSchema,
  steering_command: SteeringCommandSchema,
  confidence_score: z.number().min(0).max(1),
  gate_outcome: GateOutcomeSchema,
  rejection_reason: z.string().nullable().optional(),
  execution_status: z.string(),
  fallback_mode: z.string().nullable().optional(),
  event_tags: z.array(z.string()),
});

export type DecisionRecord = z.infer<typeof DecisionRecordSchema>;

export const PredictResponseSchema = z.object({
  recommendation: z.string(),
  confidence: z.number().min(0).max(1),
  gate_status: GateOutcomeSchema,
  alert_message: z.string(),
  decision_record: DecisionRecordSchema,
});

export type PredictResponse = z.infer<typeof PredictResponseSchema>;

// ============================================================================
// Model Metrics Schemas
// ============================================================================

export const ModelMetricsSchema = z.object({
  available: z.boolean(),
  message: z.string().optional(),
  model_loaded: z.boolean().optional(),
  model_version: z.string().optional(),
  accuracy: z.number().min(0).max(1).optional(),
  precision: z.number().min(0).max(1).optional(),
  recall: z.number().min(0).max(1).optional(),
  f1_score: z.number().min(0).max(1).optional(),
});

export type ModelMetrics = z.infer<typeof ModelMetricsSchema>;

// ============================================================================
// Health Check Schemas
// ============================================================================

export const HealthCheckResponseSchema = z.object({
  status: z.enum(["healthy", "degraded", "unhealthy"]),
  timestamp: z.string().datetime(),
  checks: z.record(
    z.string(),
    z.object({
      status: z.string(),
      details: z.string().optional(),
    })
  ),
});

export type HealthCheckResponse = z.infer<typeof HealthCheckResponseSchema>;

// ============================================================================
// Authentication Schemas
// ============================================================================

export const TokenSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
});

export type Token = z.infer<typeof TokenSchema>;

export const UserSchema = z.object({
  username: z.string(),
  role: z.string(),
  disabled: z.boolean().optional(),
});

export type User = z.infer<typeof UserSchema>;

export const UserCredentialsSchema = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
});

export type UserCredentials = z.infer<typeof UserCredentialsSchema>;

// ============================================================================
// Alert Schemas
// ============================================================================

export const AlertSeveritySchema = z.enum(["low", "medium", "high", "critical"]);

export type AlertSeverity = z.infer<typeof AlertSeveritySchema>;

export const AlertStatusSchema = z.enum(["ACTIVE", "ACKNOWLEDGED", "RESOLVED"]);

export type AlertStatus = z.infer<typeof AlertStatusSchema>;

export const AlertEventSchema = z.object({
  id: z.string(),
  timestamp: z.string().datetime(),
  severity: AlertSeveritySchema,
  status: AlertStatusSchema,
  title: z.string(),
  message: z.string().optional(),
  alert_type: z.string().optional(),
  threshold_value: z.number().optional(),
  actual_value: z.number().optional(),
});

export type AlertEvent = z.infer<typeof AlertEventSchema>;

// ============================================================================
// Operating Limits Schemas
// ============================================================================

export const OperatingLimitsSchema = z.object({
  max_vibration_g: z.number().positive(),
  max_dls_deg_100ft: z.number().positive(),
  wob_range: z.tuple([z.number(), z.number()]),
  torque_range: z.tuple([z.number(), z.number()]),
  rpm_range: z.tuple([z.number(), z.number()]),
});

export type OperatingLimits = z.infer<typeof OperatingLimitsSchema>;

// ============================================================================
// Run Summary Schemas
// ============================================================================

export const RunSummarySchema = z.object({
  id: z.string(),
  date: z.string(),
  well_name: z.string(),
  count_decisions: z.number().int().nonnegative(),
  accept_rate: z.number().min(0).max(1),
  reject_rate: z.number().min(0).max(1),
  avg_confidence: z.number().min(0).max(1),
  critical_alerts: z.number().int().nonnegative(),
});

export type RunSummary = z.infer<typeof RunSummarySchema>;

// ============================================================================
// Unified API Response Parsers
// ============================================================================

/**
 * Safe response parser with fallback to unknown type
 */
export function parseResponse<T>(schema: z.ZodSchema, data: unknown): T | null {
  try {
    return schema.parse(data) as T;
  } catch (error) {
    console.error("Response validation error:", error);
    return null;
  }
}

/**
 * Parse and log response with detailed error information
 */
export function parseResponseVerbose<T>(
  schema: z.ZodSchema,
  data: unknown,
  context: string
): T | null {
  try {
    return schema.parse(data) as T;
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error(`[${context}] Response validation failed:`, {
        errors: error.errors,
        data,
      });
    } else {
      console.error(`[${context}] Unexpected validation error:`, error, data);
    }
    return null;
  }
}
