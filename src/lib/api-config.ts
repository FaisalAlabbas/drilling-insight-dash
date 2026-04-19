/**
 * API Client Configuration
 * Configurable timeouts and other API settings
 */

export const API_CONFIG = {
  // Default timeout for standard endpoints
  timeout: {
    default: parseInt(import.meta.env.VITE_API_TIMEOUT || "8000"),
    heavy: parseInt(import.meta.env.VITE_API_TIMEOUT_HEAVY || "15000"),
    health: parseInt(import.meta.env.VITE_API_HEALTH_TIMEOUT || "5000"),
  },

  // Retry configuration
  retry: {
    maxAttempts: parseInt(import.meta.env.VITE_API_RETRY_ATTEMPTS || "2"),
    backoffMs: parseInt(import.meta.env.VITE_API_BACKOFF_MS || "1000"),
  },

  // Cache settings
  cache: {
    ttlSeconds: parseInt(import.meta.env.VITE_API_CACHE_TTL || "60"),
  },
} as const;

/**
 * Get timeout for a specific endpoint
 * @param endpoint API endpoint path
 * @returns timeout in milliseconds
 */
export function getTimeoutForEndpoint(endpoint: string): number {
  // Heavy endpoints that do aggregation/queries
  if (endpoint.includes("/decisions/stats") || endpoint.includes("/model/metrics")) {
    return API_CONFIG.timeout.heavy;
  }
  // Health checks should fail fast
  if (endpoint.includes("/health")) {
    return API_CONFIG.timeout.health;
  }
  // Standard endpoints
  return API_CONFIG.timeout.default;
}
