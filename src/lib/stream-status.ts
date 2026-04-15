/**
 * Stream connection status utilities
 */

export interface StreamStatus {
  wsConnected: boolean;
  wsError: Error | null;
  fallbackActive: boolean;
  lastMessageTime: number;
  messageLatency: number;
  bufferSize: number;
}

export function getStreamStatus(
  wsConnected: boolean,
  wsError: Error | null,
  telemetrySourceIsWebSocket: boolean,
  lastMessageTime: number,
  telemetryLength: number
): StreamStatus {
  const now = Date.now();
  const messageLatency = now - lastMessageTime;
  const fallbackActive = !wsConnected || (telemetrySourceIsWebSocket && wsError !== null);

  return {
    wsConnected,
    wsError,
    fallbackActive,
    lastMessageTime,
    messageLatency,
    bufferSize: telemetryLength,
  };
}

export function isConnectionStale(lastMessageTime: number, threshold = 10000): boolean {
  return Date.now() - lastMessageTime > threshold;
}

export function getConnectionHealthColor(
  wsConnected: boolean,
  messageLatency: number
): "healthy" | "degraded" | "offline" {
  if (!wsConnected) {
    return "offline";
  }
  if (messageLatency > 5000) {
    return "degraded";
  }
  return "healthy";
}
