/**
 * Central configuration for the frontend application.
 *
 * VITE_AI_BASE_URL must be set in .env.local (see .env.example).
 * Fallback is http://localhost:8001 for local development only.
 * Do NOT rely on the fallback in production — always set the env variable.
 */
export const API_BASE_URL: string =
  import.meta.env.VITE_AI_BASE_URL ?? "http://localhost:8001";

/** True when Vite built the app in production mode (npm run build). */
export const IS_PRODUCTION: boolean = import.meta.env.PROD;
