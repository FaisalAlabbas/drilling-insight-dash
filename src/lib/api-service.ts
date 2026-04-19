/**
 * API service for communicating with the Python backend AI service
 * Uses validated types and Zod schemas for type safety
 */

import {
  TelemetryPacket,
  ConfigResponse,
  DecisionRecord,
  DataQualityMetrics,
  ModelMetrics,
  PredictResponse,
  ActuatorStatus,
  DecisionStats,
} from "./api-types";
import {
  TelemetryPacketSchema,
  ConfigResponseSchema,
  DataQualityMetricsSchema,
  ModelMetricsSchema,
  PredictResponseSchema,
  ActuatorStatusSchema,
  DecisionStatsSchema,
  parseResponseVerbose,
} from "./zod-schemas";
import { predictDecision, type PredictPayload } from "./aiApi";
import { API_BASE_URL } from "./config";
import { ZodSchema } from "zod";

const FETCH_TIMEOUT_MS = 8000;

/**
 * Reusable helper for fetch + timeout + JSON parse + schema validation.
 * Every data-fetch endpoint goes through here so timeout, error handling,
 * and response parsing are consistent.
 */
async function fetchAndValidate<T>(
  endpoint: string,
  schema: ZodSchema,
  functionName: string
): Promise<T | null> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Failed to fetch ${functionName}: ${response.statusText}`);
    }

    const data = await response.json();
    const validated = parseResponseVerbose<T>(schema, data, functionName);
    return validated;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      console.error(`${functionName} timed out after ${FETCH_TIMEOUT_MS}ms`);
    } else if (error instanceof Error) {
      console.error(`${functionName} failed: ${error.message}`);
    } else {
      console.error(`${functionName} failed with unknown error`);
    }
    return null;
  }
}

/**
 * Map telemetry packet to model input format
 * Uses consistent field mapping for all predictions
 */
export function mapTelemetryToModelInput(telemetry: TelemetryPacket): PredictPayload {
  // Generate geological features based on telemetry characteristics
  const vibrationNormalized = Math.min(telemetry.vibration_g / 5.0, 1.0);

  return {
    WOB_klbf: telemetry.wob_klbf,
    RPM_demo: telemetry.rpm,
    ROP_ft_hr: telemetry.rop_ft_hr,
    // Estimate PHIF (porosity) from gamma ray
    PHIF: Math.max(0.1, 0.4 - (telemetry.gamma_gapi / 150) * 0.3),
    // Estimate VSH (shale volume) from gamma ray
    VSH: Math.max(0.1, (telemetry.gamma_gapi / 150) * 0.6),
    // Estimate SW (water saturation) from resistivity
    SW: Math.max(0.2, 1.0 - (telemetry.resistivity_ohm_m / 120) * 0.8),
    // Estimate KLOGH (permeability) inversely related to porosity
    KLOGH: 0.3 + vibrationNormalized * 0.5,
    Torque_kftlb: telemetry.torque_kftlb,
    Vibration_g: telemetry.vibration_g,
    DLS_deg_per_100ft: telemetry.dls_deg_100ft,
    Inclination_deg: telemetry.inclination_deg,
    Azimuth_deg: telemetry.azimuth_deg,
    // Set formation class based on VSH (shale volume) — matches model training classes
    Formation_Class:
      telemetry.vsh > 0.45
        ? "Shale-prone"
        : telemetry.vsh > 0.25
          ? "Transition"
          : "Cleaner sand",
    // Include optional fields from telemetry if available
    Depth_ft: telemetry.depth_ft,
  };
}

/**
 * Get AI recommendation from backend with robust error handling
 */
export async function getRecommendation(
  telemetry: TelemetryPacket
): Promise<DecisionRecord | null> {
  try {
    const payload = mapTelemetryToModelInput(telemetry);
    const response = await predictDecision(payload);

    // Validate the response using Zod schema
    const validated = parseResponseVerbose<PredictResponse>(
      PredictResponseSchema,
      response,
      "getRecommendation"
    );

    if (!validated) {
      console.warn("Invalid API response format for prediction");
      return null;
    }

    // Return the validated decision record from the API response
    return validated.decision_record;
  } catch (error) {
    if (error instanceof Error) {
      console.warn(`API recommendation failed (${error.message}), using fallback`, error);
    } else {
      console.warn("API recommendation failed, using fallback");
    }
    // Return null to trigger fallback logic in the dashboard context
    return null;
  }
}

/**
 * Fetch config from backend with validation
 */
export async function fetchConfig(): Promise<ConfigResponse | null> {
  return fetchAndValidate<ConfigResponse>(
    "/config",
    ConfigResponseSchema,
    "fetchConfig"
  );
}

/**
 * Fetch telemetry data from backend with validation
 */
export async function fetchTelemetry(): Promise<TelemetryPacket | null> {
  return fetchAndValidate<TelemetryPacket>(
    "/telemetry/next",
    TelemetryPacketSchema,
    "fetchTelemetry"
  );
}

/**
 * Fetch data quality metrics from backend with validation
 */
export async function fetchDataQuality(): Promise<DataQualityMetrics | null> {
  return fetchAndValidate<DataQualityMetrics>(
    "/telemetry/quality",
    DataQualityMetricsSchema,
    "fetchDataQuality"
  );
}

/**
 * Fetch model metrics from backend with validation
 */
export async function fetchModelMetrics(): Promise<ModelMetrics | null> {
  return fetchAndValidate<ModelMetrics>(
    "/model/metrics",
    ModelMetricsSchema,
    "fetchModelMetrics"
  );
}

/**
 * Fetch virtual actuator status from backend
 */
export async function fetchActuatorStatus(): Promise<ActuatorStatus | null> {
  return fetchAndValidate<ActuatorStatus>(
    "/actuator/status",
    ActuatorStatusSchema,
    "fetchActuatorStatus"
  );
}

/**
 * Fetch decision statistics for the verification page
 */
export async function fetchDecisionStats(): Promise<DecisionStats | null> {
  return fetchAndValidate<DecisionStats>(
    "/decisions/stats",
    DecisionStatsSchema,
    "fetchDecisionStats"
  );
}

import type { SystemMode } from "./api-types";

export type BackendHealthStatus = "healthy" | "degraded" | "unreachable";

export interface BackendHealthResult {
  status: BackendHealthStatus;
  systemMode: SystemMode | null;
}

/**
 * Health check for backend with timeout.
 * Returns the real status and system operating mode.
 */
export async function checkBackendHealth(): Promise<BackendHealthResult> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${API_BASE_URL}/health`, {
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return { status: "unreachable", systemMode: null };
    }

    const health = await response.json() as { status?: string; system_mode?: string };
    const systemMode = (health.system_mode === "SIMULATION" || health.system_mode === "PROTOTYPE")
      ? health.system_mode as SystemMode
      : null;

    if (health.status === "healthy") return { status: "healthy", systemMode };
    if (health.status === "degraded") return { status: "degraded", systemMode };
    return { status: "unreachable", systemMode };
  } catch {
    return { status: "unreachable", systemMode: null };
  }
}
