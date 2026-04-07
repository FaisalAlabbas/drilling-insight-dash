/**
 * API service for communicating with the Python backend AI service
 */

import { predictDecision, type PredictPayload } from "./aiApi";
import type { TelemetryPacket, DecisionRecord } from "./types";

const API_BASE_URL = import.meta.env.VITE_AI_BASE_URL || "http://localhost:8000";

/**
 * Map telemetry packet to model input format
 * Generates geological features based on telemetry characteristics
 */
export function mapTelemetryToModelInput(telemetry: TelemetryPacket): PredictPayload {
  // Generate geological features based on depth and formation characteristics
  const vibrationNormalized = Math.min(telemetry.vibration_g / 5.0, 1.0);
  const dlsNormalized = Math.min(telemetry.dls_deg_100ft / 6.0, 1.0);

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
  };
}

/**
 * Get AI recommendation from backend with robust error handling
 */
export async function getRecommendation(
  telemetry: TelemetryPacket
): Promise<DecisionRecord | null> {
  try {
    const payload: PredictPayload = {
      WOB_klbf: telemetry.wob_klbf,
      RPM_demo: telemetry.rpm,
      ROP_ft_hr: telemetry.rop_ft_hr,
      PHIF: 0.18, // Default values for missing fields
      VSH: 0.25,
      SW: 0.35,
      KLOGH: 120,
      Formation_Class: "Sandstone",
      Torque_kftlb: telemetry.torque_kftlb,
      Vibration_g: telemetry.vibration_g,
      DLS_deg_per_100ft: telemetry.dls_deg_100ft,
      Inclination_deg: telemetry.inclination_deg,
      Azimuth_deg: telemetry.azimuth_deg,
    };

    const response = await predictDecision(payload);

    // Return the decision record directly from the API response
    return response.decision_record;
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
 * Health check for backend with timeout
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout for health check

    const response = await fetch(`${API_BASE_URL}/health`, {
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return response.ok && response.status === 200;
  } catch {
    return false;
  }
}
