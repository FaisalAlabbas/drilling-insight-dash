/**
 * API service for communicating with the Python backend AI service
 */

import axios, { AxiosInstance } from 'axios';
import type { TelemetryPacket, DecisionRecord, FeatureVector } from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Initialize axios instance with base URL
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

interface PredictRequest {
  WOB_klbf: number;
  RPM_demo: number;
  ROP_ft_hr: number;
  PHIF: number;
  VSH: number;
  SW: number;
  KLOGH: number;
  Torque_kftlb: number;
  Vibration_g: number;
  DLS_deg_per_100ft: number;
  Inclination_deg: number;
  Azimuth_deg: number;
  Formation_Class: string;
}

interface PredictResponse {
  recommendation: string;
  confidence: number;
  gate_status: string;
  alert_message: string;
  decision_record: DecisionRecord;
}

/**
 * Map telemetry packet to model input format
 * Generates geological features based on telemetry characteristics
 */
export function mapTelemetryToModelInput(telemetry: TelemetryPacket): PredictRequest {
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
    Formation_Class: telemetry.inclination_deg > 60 ? 'Sandstone' : 
                     telemetry.inclination_deg > 30 ? 'Limestone' : 'Shale',
  };
}

/**
 * Get AI recommendation from backend
 */
export async function getRecommendation(telemetry: TelemetryPacket): Promise<DecisionRecord | null> {
  try {
    const input = mapTelemetryToModelInput(telemetry);
    const response = await apiClient.post<PredictResponse>('/predict', input);

    // Transform backend response to DecisionRecord format
    return {
      timestamp: new Date().toISOString(),
      model_version: 'rf-trained-v1',
      feature_summary: {
        mean_wob: input.WOB_klbf,
        std_wob: 0,
        mean_torque: input.Torque_kftlb,
        std_torque: 0,
        mean_rpm: input.RPM_demo,
        std_rpm: 0,
        mean_vibration: input.Vibration_g,
        std_vibration: 0,
        trend_inclination: 0,
        trend_azimuth: 0,
        instability_proxy: input.Vibration_g * input.DLS_deg_per_100ft,
      },
      steering_command: response.data.recommendation as any,
      confidence_score: response.data.confidence,
      gate_outcome: response.data.gate_status === 'REJECTED' ? 'REJECTED' : 'ACCEPTED',
      rejection_reason: response.data.gate_status !== 'ACCEPTED' ? 'LIMIT_EXCEEDED' : null,
      execution_status: response.data.gate_status === 'REJECTED' ? 'BLOCKED' : 'SENT',
      fallback_mode: response.data.gate_status === 'REJECTED' ? 'HOLD_STEERING' : null,
      event_tags: response.data.alert_message ? [response.data.alert_message] : [],
    };
  } catch (error) {
    console.error('Failed to get recommendation from backend:', error);
    return null;
  }
}

/**
 * Health check for backend
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await apiClient.get('/health');
    return response.data?.ok === true;
  } catch {
    return false;
  }
}

export default apiClient;
