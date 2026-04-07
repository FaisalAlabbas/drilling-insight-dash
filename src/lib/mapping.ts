import { TelemetryPacket } from "./types";

/**
 * Maps TelemetryPacket to API predict payload
 * Extracts required fields and performs any necessary transformations
 */
export function mapTelemetryToPredict(
  telemetry: TelemetryPacket
): Record<string, number | string> {
  return {
    wob_klbf: telemetry.wob_klbf,
    torque_kftlb: telemetry.torque_kftlb,
    rpm: telemetry.rpm,
    vibration_g: telemetry.vibration_g,
    inclination_deg: telemetry.inclination_deg,
    azimuth_deg: telemetry.azimuth_deg,
    rop_ft_hr: telemetry.rop_ft_hr,
    dls_deg_100ft: telemetry.dls_deg_100ft,
    gamma_gapi: telemetry.gamma_gapi,
    resistivity_ohm_m: telemetry.resistivity_ohm_m,
  };
}

/**
 * Validates that a TelemetryPacket has all required fields
 */
export function validateTelemetryPacket(telemetry: Partial<TelemetryPacket>): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];
  const requiredFields = [
    "wob_klbf",
    "torque_kftlb",
    "rpm",
    "vibration_g",
    "inclination_deg",
    "azimuth_deg",
    "rop_ft_hr",
    "dls_deg_100ft",
    "gamma_gapi",
    "resistivity_ohm_m",
  ] as const;

  for (const field of requiredFields) {
    if (telemetry[field] === undefined || telemetry[field] === null) {
      errors.push(`Missing required field: ${field}`);
    } else if (typeof telemetry[field] !== "number") {
      errors.push(`Field ${field} must be a number`);
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
