import { describe, it, expect } from "vitest";
import { mapTelemetryToPredict, validateTelemetryPacket } from "./mapping";
import { TelemetryPacket } from "./types";

const mockTelemetry: TelemetryPacket = {
  timestamp: "2024-04-07T12:00:00Z",
  depth_ft: 10000,
  wob_klbf: 50,
  torque_kftlb: 100,
  rpm: 150,
  vibration_g: 0.5,
  inclination_deg: 45,
  azimuth_deg: 90,
  rop_ft_hr: 50,
  dls_deg_100ft: 1.5,
  gamma_gapi: 100,
  resistivity_ohm_m: 10,
  phif: 0.25,
  vsh: 0.35,
  sw: 0.45,
  klogh: 0.55,
  formation_class: "sandstone",
};

describe("mapTelemetryToPredict", () => {
  it("returns all required fields", () => {
    const result = mapTelemetryToPredict(mockTelemetry);

    expect(result).toHaveProperty("wob_klbf");
    expect(result).toHaveProperty("torque_kftlb");
    expect(result).toHaveProperty("rpm");
    expect(result).toHaveProperty("vibration_g");
    expect(result).toHaveProperty("inclination_deg");
    expect(result).toHaveProperty("azimuth_deg");
    expect(result).toHaveProperty("rop_ft_hr");
    expect(result).toHaveProperty("dls_deg_100ft");
    expect(result).toHaveProperty("gamma_gapi");
    expect(result).toHaveProperty("resistivity_ohm_m");
  });

  it("maps values correctly", () => {
    const result = mapTelemetryToPredict(mockTelemetry);

    expect(result.wob_klbf).toBe(50);
    expect(result.torque_kftlb).toBe(100);
    expect(result.rpm).toBe(150);
    expect(result.vibration_g).toBe(0.5);
    expect(result.inclination_deg).toBe(45);
    expect(result.azimuth_deg).toBe(90);
    expect(result.rop_ft_hr).toBe(50);
    expect(result.dls_deg_100ft).toBe(1.5);
    expect(result.gamma_gapi).toBe(100);
    expect(result.resistivity_ohm_m).toBe(10);
  });

  it("does not include timestamp field", () => {
    const result = mapTelemetryToPredict(mockTelemetry);
    expect(result).not.toHaveProperty("timestamp");
  });

  it("excludes non-numeric fields", () => {
    const result = mapTelemetryToPredict(mockTelemetry);
    const keys = Object.keys(result);
    expect(keys.length).toBe(10);
  });
});

describe("validateTelemetryPacket", () => {
  it("validates correct telemetry packet", () => {
    const result = validateTelemetryPacket(mockTelemetry);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it("detects missing fields", () => {
    const invalid = { ...mockTelemetry };
    delete (invalid as Record<string, unknown>).wob_klbf;

    const result = validateTelemetryPacket(invalid);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Missing required field: wob_klbf");
  });

  it("detects non-numeric fields", () => {
    const invalid = { ...mockTelemetry, wob_klbf: "invalid" } as Record<string, unknown>;

    const result = validateTelemetryPacket(invalid as Partial<TelemetryPacket>);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Field wob_klbf must be a number");
  });

  it("detects multiple missing fields", () => {
    const invalid: Partial<TelemetryPacket> = {
      wob_klbf: 50,
      rpm: 150,
    };

    const result = validateTelemetryPacket(invalid);
    expect(result.valid).toBe(false);
    expect(result.errors.length).toBeGreaterThan(1);
  });
});
