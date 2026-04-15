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
} from "./api-types";
import {
  TelemetryPacketSchema,
  ConfigResponseSchema,
  DataQualityMetricsSchema,
  ModelMetricsSchema,
  PredictResponseSchema,
  parseResponseVerbose,
} from "./zod-schemas";
import { predictDecision, type PredictPayload } from "./aiApi";
import { API_BASE_URL } from "./config";
import { ZodSchema } from "zod";

/**
 * Reusable helper for fetch + JSON parse + schema validation
 * Provides consistent error handling and logging across all API endpoints
 */
async function fetchAndValidate<T>(
  endpoint: string,
  schema: ZodSchema,
  functionName: string
): Promise<T | null> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch ${functionName}: ${response.statusText}`);
    }

    const data = await response.json();
    const validated = parseResponseVerbose<T>(schema, data, functionName);
    return validated;
  } catch (error) {
    if (error instanceof Error) {
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
    // Set formation class based on inclination
    Formation_Class:
      telemetry.inclination_deg > 60
        ? "Sandstone"
        : telemetry.inclination_deg > 30
          ? "Limestone"
          : "Shale",
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
 * Fetch configuration from backend with validation
 */
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
 * Health check for backend with timeout
 * Returns true only if backend is fully healthy (not degraded/unhealthy)
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    const response = await fetch(`${API_BASE_URL}/health`, {
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok || response.status !== 200) {
      return false;
    }

    // Parse JSON payload to check actual health status
    const health = await response.json() as { status?: string };
    return health.status === "healthy";
  } catch {
    return false;
  }
}
