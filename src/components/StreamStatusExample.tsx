import React from "react";
import { StreamStatusIndicator } from "@/components/StreamStatusIndicator";
import { getStreamStatus } from "@/lib/stream-status";
import type { TelemetryPacket } from "@/lib/api-types";

interface StreamStatusExampleProps {
  wsConnected: boolean;
  wsError: Error | null;
  telemetrySourceIsWebSocket: boolean;
  lastMessageTime: number;
  telemetry: TelemetryPacket[];
}

/**
 * Example integration of StreamStatusIndicator in dashboard header
 *
 * Usage:
 *
 * ```typescript
 * import { useDashboard } from "@/lib/dashboard-context";
 *
 * function DashboardHeader() {
 *   const { telemetry } = useDashboard();
 *   // ... get other stream status from context/props
 *
 *   return (
 *     <header className="border-b">
 *       <div className="flex justify-between items-center p-4">
 *         <h1>Drilling Dashboard</h1>
 *         <StreamStatusIndicator status={streamStatus} />
 *       </div>
 *     </header>
 *   );
 * }
 * ```
 */
export function StreamStatusExample({
  wsConnected,
  wsError,
  telemetrySourceIsWebSocket,
  lastMessageTime,
  telemetry,
}: StreamStatusExampleProps) {
  const streamStatus = getStreamStatus(
    wsConnected,
    wsError,
    telemetrySourceIsWebSocket,
    lastMessageTime,
    telemetry.length
  );

  return (
    <div className="border rounded-lg p-4 space-y-4">
      <h2 className="text-lg font-semibold">Stream Status Example</h2>

      {/* Full status display */}
      <div className="space-y-2">
        <p className="text-sm font-medium">Full Status:</p>
        <StreamStatusIndicator status={streamStatus} compact={false} />
      </div>

      {/* Compact status display (for headers) */}
      <div className="space-y-2">
        <p className="text-sm font-medium">Compact Status:</p>
        <StreamStatusIndicator status={streamStatus} compact={true} />
      </div>

      {/* Raw status data */}
      <div className="space-y-2 text-sm">
        <p className="font-medium">Raw Status Data:</p>
        <pre className="bg-muted p-2 rounded text-xs overflow-auto">
          {JSON.stringify(streamStatus, null, 2)}
        </pre>
      </div>

      {/* Status indicators */}
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <p className="text-muted-foreground">Connected:</p>
          <p className="font-medium">{streamStatus.wsConnected ? "Yes" : "No"}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Fallback Active:</p>
          <p className="font-medium">{streamStatus.fallbackActive ? "Yes" : "No"}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Latency:</p>
          <p className="font-medium">{streamStatus.messageLatency}ms</p>
        </div>
        <div>
          <p className="text-muted-foreground">Buffer Size:</p>
          <p className="font-medium">{streamStatus.bufferSize} points</p>
        </div>
      </div>

      {/* Error display */}
      {streamStatus.wsError && (
        <div className="bg-destructive/10 border border-destructive text-destructive p-2 rounded text-sm">
          <p className="font-medium">Error:</p>
          <p>{streamStatus.wsError.message}</p>
        </div>
      )}
    </div>
  );
}
