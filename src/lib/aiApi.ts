/**
 * AI API client for prediction requests with robust error handling and timeout
 */

const baseUrl = import.meta.env.VITE_AI_BASE_URL || "http://localhost:8000";
const API_TIMEOUT = 15000; // 15 seconds

export interface PredictPayload {
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

export interface PredictResponse {
  recommendation: string;
  confidence: number;
  gate_status: "ACCEPTED" | "REDUCED" | "REJECTED";
  alert_message: string;
  decision_record: {
    timestamp: string;
    model_version: string;
    feature_summary: { [key: string]: number };
    steering_command: string;
    confidence_score: number;
    gate_outcome: "ACCEPTED" | "REDUCED" | "REJECTED";
    rejection_reason: string | null;
    execution_status: string;
    fallback_mode: string | null;
    event_tags: string[];
  };
}

export class APIError extends Error {
  constructor(
    public code: string,
    message: string,
    public statusCode?: number
  ) {
    super(message);
    this.name = "APIError";
  }
}

/**
 * Make a request with timeout and proper error handling
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeoutMs: number = API_TIMEOUT
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof TypeError && error.name === "AbortError") {
      throw new APIError(
        "TIMEOUT",
        `Request timed out after ${timeoutMs}ms. Backend may be unavailable.`
      );
    }
    throw error;
  }
}

export async function predictDecision(payload: PredictPayload): Promise<PredictResponse> {
  try {
    const response = await fetchWithTimeout(
      `${baseUrl}/predict`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
      API_TIMEOUT
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(
        "HTTP_ERROR",
        errorData.detail ||
          `API request failed: ${response.status} ${response.statusText}`,
        response.status
      );
    }

    return response.json();
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof TypeError) {
      if (error.message.includes("fetch")) {
        throw new APIError(
          "NETWORK_ERROR",
          "Network error: Unable to reach the backend. Please check your connection."
        );
      }
    }

    throw new APIError(
      "UNKNOWN_ERROR",
      error instanceof Error ? error.message : "An unknown error occurred"
    );
  }
}
