import React from "react";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Wifi, WifiOff } from "lucide-react";
import type { StreamStatus } from "@/lib/stream-status";

interface StreamStatusIndicatorProps {
  status: StreamStatus;
  compact?: boolean;
}

/**
 * Visual indicator for WebSocket stream connection status
 * Shows connection health, latency, and buffer size
 */
export function StreamStatusIndicator({
  status,
  compact = false,
}: StreamStatusIndicatorProps) {
  const getStatusColor = () => {
    if (status.wsError) return "destructive";
    if (!status.wsConnected && status.fallbackActive) return "secondary";
    if (!status.wsConnected) return "destructive";
    if (status.messageLatency > 5000) return "outline";
    return "default";
  };

  const getStatusIcon = () => {
    if (status.wsError || !status.wsConnected) {
      return !status.fallbackActive ? (
        <WifiOff className="w-3 h-3" />
      ) : (
        <AlertTriangle className="w-3 h-3" />
      );
    }
    return <Wifi className="w-3 h-3" />;
  };

  const getStatusText = () => {
    if (status.wsError) return "Stream Error";
    if (!status.wsConnected && status.fallbackActive) return "Fallback Mode";
    if (!status.wsConnected) return "Disconnected";
    return "Live";
  };

  if (compact) {
    return (
      <div className="flex items-center gap-1">
        {getStatusIcon()}
        <span className="text-xs">{getStatusText()}</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Badge variant={getStatusColor()} className="flex items-center gap-1">
        {getStatusIcon()}
        <span>{getStatusText()}</span>
      </Badge>

      <span className="text-xs text-muted-foreground">
        {status.bufferSize > 0 && `${status.bufferSize} pts`}
        {status.messageLatency > 0 && ` • ${status.messageLatency.toFixed(0)}ms`}
      </span>

      {status.messageLatency > 5000 && (
        <AlertTriangle
          className="w-4 h-4 text-yellow-600"
          title="High latency detected"
        />
      )}
    </div>
  );
}
