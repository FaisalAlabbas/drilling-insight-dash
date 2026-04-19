/**
 * Backend State Machine
 *
 * Replaces brittle boolean patterns (isBackendDegraded, isBackendImpaired, isMockData)
 * with explicit, mutually-exclusive union types.
 *
 * This ensures clear separation between backend connectivity states and data sources.
 */

import type { SystemMode, ActuatorStatus } from "./api-types";

/**
 * Unified backend connectivity and data source state.
 * Each variant represents a distinct operational state with clear semantics.
 */
export type BackendState =
  | {
      /** Backend is healthy and responding normally. */
      readonly type: "healthy";
      readonly systemMode: SystemMode;
      readonly actuatorStatus: ActuatorStatus | null;
    }
  | {
      /** Backend is reachable but reports impaired subsystem (e.g., no telemetry data). */
      readonly type: "degraded";
      readonly systemMode: SystemMode;
      readonly actuatorStatus: ActuatorStatus | null;
    }
  | {
      /** Backend is unreachable. Data is simulated for development/testing. */
      readonly type: "unreachable-simulated";
      readonly reason: string;
    }
  | {
      /** Backend is unreachable in production mode. UI must show unavailable state. */
      readonly type: "unreachable-production";
      readonly reason: string;
    }
  | {
      /** Backend is running in PROTOTYPE mode (read-only, limited functionality). */
      readonly type: "prototype";
      readonly systemMode: "PROTOTYPE";
      readonly actuatorStatus: ActuatorStatus | null;
    };

/**
 * Derives BackendState from raw component state.
 *
 * @param backendStatus - Health check result: "healthy", "degraded", or "unreachable"
 * @param systemMode - Operating mode from backend
 * @param actuatorStatus - Virtual actuator state
 * @param isProduction - Whether app is running in production mode
 * @returns The unified BackendState
 */
export function deriveBackendState(
  backendStatus: "healthy" | "degraded" | "unreachable",
  systemMode: SystemMode,
  actuatorStatus: ActuatorStatus | null,
  isProduction: boolean
): BackendState {
  if (systemMode === "PROTOTYPE") {
    return {
      type: "prototype",
      systemMode,
      actuatorStatus,
    };
  }

  if (backendStatus === "healthy") {
    return {
      type: "healthy",
      systemMode,
      actuatorStatus,
    };
  }

  if (backendStatus === "degraded") {
    return {
      type: "degraded",
      systemMode,
      actuatorStatus,
    };
  }

  // backendStatus === "unreachable"
  if (isProduction) {
    return {
      type: "unreachable-production",
      reason: "Backend is unreachable in production mode",
    };
  }

  // Development mode: fall back to simulated data
  return {
    type: "unreachable-simulated",
    reason: "Backend is unreachable; using simulated data in development",
  };
}

/**
 * Predicate: backend is reachable and responding.
 */
export function isBackendAvailable(state: BackendState): boolean {
  return (
    state.type === "healthy" ||
    state.type === "degraded" ||
    state.type === "prototype"
  );
}

/**
 * Predicate: backend is unreachable.
 */
export function isBackendUnreachable(state: BackendState): boolean {
  return (
    state.type === "unreachable-production" ||
    state.type === "unreachable-simulated"
  );
}

/**
 * Predicate: data being shown is from mock/simulated generation, not live backend.
 */
export function isDataSimulated(state: BackendState): boolean {
  return (
    state.type === "unreachable-simulated" ||
    state.type === "prototype"
  );
}

/**
 * Predicate: backend reported impaired subsystems.
 */
export function isBackendDegraded(state: BackendState): boolean {
  return state.type === "degraded";
}

/**
 * Predicate: production mode with unreachable backend (critical alert).
 */
export function isProductionOutage(state: BackendState): boolean {
  return state.type === "unreachable-production";
}

/**
 * Predicate: backend is in prototype/read-only mode.
 */
export function isPrototypeMode(state: BackendState): boolean {
  return state.type === "prototype";
}

/**
 * Human-readable status message for UI display.
 */
export function getBackendStatusMessage(state: BackendState): string {
  switch (state.type) {
    case "healthy":
      return "Backend online";
    case "degraded":
      return "Backend degraded - limited functionality";
    case "unreachable-simulated": {
      return `Development mode: ${state.reason}`;
    }
    case "unreachable-production": {
      return `CRITICAL: ${state.reason}`;
    }
    case "prototype":
      return "Prototype mode - read-only";
    default: {
      const _exhaustive: never = state;
      return _exhaustive;
    }
  }
}

/**
 * Backend health indicator color for UI badge/indicator.
 * Useful for color-coding status displays.
 */
export function getBackendStatusColor(state: BackendState): "green" | "yellow" | "red" | "gray" {
  switch (state.type) {
    case "healthy":
      return "green";
    case "degraded":
      return "yellow";
    case "unreachable-simulated":
      return "gray";
    case "unreachable-production":
      return "red";
    case "prototype":
      return "gray";
    default: {
      const _exhaustive: never = state;
      return _exhaustive;
    }
  }
}
