/**
 * Centralized type definitions for the Drilling Insight Dashboard
 * Re-exports types from api-types.ts for backward compatibility
 */

export * from "./api-types";

// Keep legacy type definitions for backward compatibility
export type UserRole = "Operator" | "Engineer" | "Admin";
export type EdgeHealth = "Healthy" | "Degraded";
export type SamplingRate = "1Hz" | "10Hz";

