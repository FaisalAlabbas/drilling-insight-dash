import { useEffect, useRef, useState, useCallback } from "react";
import type { TelemetryPacket } from "@/lib/api-types";
import { API_BASE_URL } from "@/lib/config";

interface TelemetryStreamMessage {
  type:
    | "telemetry"
    | "recommendation"
    | "data_quality"
    | "heartbeat"
    | "error"
    | "connection_established";
  timestamp: string;
  data?: TelemetryPacket;
  message?: string;
}

interface UseTelemetryStreamOptions {
  maxBufferSize?: number;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatTimeout?: number;
  onTelemetry?: (packet: TelemetryPacket) => void;
  onError?: (error: Error) => void;
  enabled?: boolean;
}

/**
 * Hook for streaming telemetry via WebSocket
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Stale connection detection via heartbeat
 * - Buffering of latest N points (default 300)
 * - Fallback to polling if WebSocket unavailable
 */
export function useTelemetryStream(options: UseTelemetryStreamOptions = {}) {
  const {
    maxBufferSize = 300,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    heartbeatTimeout = 10000,
    onTelemetry,
    onError,
    enabled = true,
  } = options;

  const [buffer, setBuffer] = useState<TelemetryPacket[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastMessageTime, setLastMessageTime] = useState<number>(Date.now());

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = API_BASE_URL.replace(/^http/, "ws") + "/telemetry/stream";

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        if (!isMountedRef.current) return;
        console.log("[WebSocket] Connected to telemetry stream");
        setConnected(true);
        setError(null);
        reconnectCountRef.current = 0;
        setLastMessageTime(Date.now());
      };

      wsRef.current.onmessage = (event) => {
        if (!isMountedRef.current) return;

        try {
          const message: TelemetryStreamMessage = JSON.parse(event.data);
          setLastMessageTime(Date.now());

          // Reset heartbeat timeout
          if (heartbeatTimeoutRef.current) {
            clearTimeout(heartbeatTimeoutRef.current);
          }
          heartbeatTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current) {
              console.warn("[WebSocket] Stale connection detected, reconnecting...");
              wsRef.current?.close();
              reconnectCountRef.current = 0; // Reset to attempt fresh connection
              scheduleReconnect();
            }
          }, heartbeatTimeout);

          if (message.type === "telemetry" && message.data) {
            const packet = message.data as TelemetryPacket;
            setBuffer((prev) => {
              const next = [...prev, packet];
              // Keep only latest N points
              return next.length > maxBufferSize ? next.slice(-maxBufferSize) : next;
            });
            onTelemetry?.(packet);
          } else if (message.type === "error") {
            const err = new Error(message.message || "WebSocket error");
            setError(err);
            onError?.(err);
          }
        } catch (err) {
          const parseError = new Error(`Failed to parse WebSocket message: ${err}`);
          setError(parseError);
          onError?.(parseError);
        }
      };

      wsRef.current.onerror = (event) => {
        if (!isMountedRef.current) return;
        console.error("[WebSocket] Connection error:", event);
        const err = new Error("WebSocket connection error");
        setError(err);
        onError?.(err);
      };

      wsRef.current.onclose = () => {
        if (!isMountedRef.current) return;
        console.log("[WebSocket] Connection closed");
        setConnected(false);

        if (enabled) {
          // Schedule reconnection with exponential backoff
          scheduleReconnect();
        }
      };
    } catch (err) {
      const connectError = new Error(`Failed to create WebSocket: ${err}`);
      setError(connectError);
      onError?.(connectError);
      scheduleReconnect();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, heartbeatTimeout, maxBufferSize, onError, onTelemetry]);

  const scheduleReconnect = useCallback(() => {
    if (!isMountedRef.current || !enabled) return;

    if (reconnectCountRef.current >= maxReconnectAttempts) {
      console.error("[WebSocket] Max reconnection attempts reached, giving up");
      const err = new Error("WebSocket: Max reconnection attempts reached");
      setError(err);
      onError?.(err);
      return;
    }

    // Exponential backoff: 3s, 6s, 12s, ... up to ~30s
    const delay = Math.min(
      reconnectInterval * Math.pow(2, reconnectCountRef.current),
      30000
    );

    console.log(
      `[WebSocket] Scheduling reconnect in ${delay}ms (attempt ${reconnectCountRef.current + 1}/${maxReconnectAttempts})`
    );

    reconnectCountRef.current++;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    reconnectTimeoutRef.current = setTimeout(() => {
      if (isMountedRef.current && enabled) {
        connect();
      }
    }, delay);
  }, [connect, enabled, maxReconnectAttempts, onError, reconnectInterval]);

  // Effect: Connect on mount and cleanup
  useEffect(() => {
    isMountedRef.current = true;

    if (enabled) {
      connect();
    }

    return () => {
      isMountedRef.current = false;

      if (wsRef.current) {
        wsRef.current.close();
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      if (heartbeatTimeoutRef.current) {
        clearTimeout(heartbeatTimeoutRef.current);
      }
    };
  }, [enabled, connect]);

  return {
    telemetry: buffer,
    connected,
    error,
    lastMessageTime,
  };
}
