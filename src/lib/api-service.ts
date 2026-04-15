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
export async function fetchConfig(): Promise<ConfigResponse | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/config`);

    if (!response.ok) {
      throw new Error(`Failed to fetch config: ${response.statusText}`);
    }

    const data = await response.json();

    // Validate using Zod schema
    const validated = parseResponseVerbose<ConfigResponse>(
      ConfigResponseSchema,
      data,
      "fetchConfig"
    );

    return validated;
  } catch (error) {
    if (error instanceof Error) {
      console.error(`Config fetch failed: ${error.message}`);
    } else {
      console.error("Config fetch failed with unknown error");
    }
    return null;
  }
}

/**
 * Fetch telemetry data from backend with validation
 */
export async function fetchTelemetry(): Promise<TelemetryPacket | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/telemetry/next`);

    if (!response.ok) {
      throw new Error(`Failed to fetch telemetry: ${response.statusText}`);
    }

    const data = await response.json();

    // Validate using Zod schema
    const validated = parseResponseVerbose<TelemetryPacket>(
      TelemetryPacketSchema,
      data,
      "fetchTelemetry"
    );

    return validated;
  } catch (error) {
    if (error instanceof Error) {
      console.error(`Telemetry fetch failed: ${error.message}`);
    } else {
      console.error("Telemetry fetch failed with unknown error");
    }
    return null;
  }
}

/**
 * Fetch data quality metrics from backend with validation
 */
export async function fetchDataQuality(): Promise<DataQualityMetrics | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/telemetry/quality`);

    if (!response.ok) {
      throw new Error(`Failed to fetch data quality: ${response.statusText}`);
    }

    const data = await response.json();

    // Validate using Zod schema
    const validated = parseResponseVerbose<DataQualityMetrics>(
      DataQualityMetricsSchema,
      data,
      "fetchDataQuality"
    );

    return validated;
  } catch (error) {
    if (error instanceof Error) {
      console.error(`Data quality fetch failed: ${error.message}`);
    } else {
      console.error("Data quality fetch failed with unknown error");
    }
    return null;
  }
}

/**
 * Fetch model metrics from backend with validation
 */
export async function fetchModelMetrics(): Promise<ModelMetrics | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/model/metrics`);

    if (!response.ok) {
      throw new Error(`Failed to fetch model metrics: ${response.statusText}`);
    }

    const data = await response.json();

    // Validate using Zod schema
    const validated = parseResponseVerbose<ModelMetrics>(
      ModelMetricsSchema,
      data,
      "fetchModelMetrics"
    );

    return validated;
  } catch (error) {
    if (error instanceof Error) {
      console.error(`Model metrics fetch failed: ${error.message}`);
    } else {
      console.error("Model metrics fetch failed with unknown error");
    }
    return null;
  }
}

/**
 * Health check for backend with timeout
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    const response = await fetch(`${API_BASE_URL}/health`, {
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return response.ok && response.status === 200;
  } catch {
    return false;
  }
}
