# WebSocket Telemetry Streaming

## Overview

The frontend has been refactored to use WebSocket-based telemetry streaming instead of HTTP polling. This provides real-time data delivery with automatic reconnection, heartbeat detection, and graceful fallback mechanisms.

## Architecture

### Backend (FastAPI)

**Endpoint**: `ws://localhost:8000/telemetry/stream`

```python
@app.websocket("/telemetry/stream")
async def telemetry_stream(websocket: WebSocket, db = Depends(get_db)):
    """Stream live telemetry with heartbeat and recommendations"""
```

**Features**:
- Real-time telemetry packets (1Hz by default)
- AI recommendations included in stream
- Data quality metrics (periodic)
- Heartbeat every 5 seconds for stale connection detection
- Full error handling with reconnection support

**Message Types**:
- `connection_established`: Initial connection confirmation
- `telemetry`: New telemetry packet with all sensor readings
- `recommendation`: AI decision/recommendation for the packet
- `data_quality`: Periodic data quality metrics (every 10 messages)
- `heartbeat`: Periodic keepalive message (every 5 seconds)
- `error`: Error notification
- `no_data`: No telemetry available in database

### Frontend Hook

**Hook**: `useTelemetryStream` in `src/hooks/useTelemetryStream.ts`

```typescript
const {
  telemetry,        // TelemetryPacket[] - Latest 300 points
  connected,        // boolean - WebSocket connection state
  error,            // Error | null - Connection/parsing errors
  lastMessageTime,  // number - Unix timestamp of last message
} = useTelemetryStream({
  maxBufferSize: 300,              // Default buffer size
  reconnectInterval: 3000,         // Initial reconnect delay (ms)
  maxReconnectAttempts: 10,        // Max reconnection attempts
  heartbeatTimeout: 10000,         // Stale connection threshold (ms)
  onTelemetry: (packet) => {},     // Optional callback per packet
  onError: (error) => {},          // Optional error callback
  enabled: true,                   // Enable/disable streaming
});
```

## Features

### 1. Automatic Reconnection
- Exponential backoff: 3s → 6s → 12s → ... up to 30s
- Max 10 reconnection attempts before giving up
- Full reset on successful reconnection
- Configurable delays and attempt limits

### 2. Stale Connection Detection
- Server sends heartbeat every 5 seconds
- Client cancels reconnection if no message for 10 seconds
- Automatic reconnection triggered on timeout
- Prevents zombie connections

### 3. Buffer Management
- Maintains latest 300 telemetry points by default
- Automatic cleanup of old data
- Efficient memory usage for long-running applications
- Configurable buffer size

### 4. Fallback Mechanism
- Falls back to HTTP polling if WebSocket unavailable
- Falls back to mock data generation if backend unavailable
- Transparent to consuming components
- Maintains data continuity across connection changes

### 5. Error Handling
- Detailed error logging with context
- Graceful error callbacks for UI notification
- Connection state available for UI display
- Distinguishes between connection and parsing errors

## Integration with Dashboard Context

### Current Flow

1. **WebSocket Priority**: Dashboard context tries WebSocket first
2. **Smart Fallback**: If WebSocket fails or unavailable, switches to polling
3. **Data Continuity**: Same data structure regardless of source
4. **Automatic Decisions**: AI recommendations generated from telemetry
5. **Alert Generation**: Alerts created based on telemetry + decision data

### Usage in Components

```typescript
import { useDashboard } from "@/lib/dashboard-context";

function MyComponent() {
  const { telemetry, alerts, decisions } = useDashboard();
  
  // Telemetry is automatically populated from WebSocket or fallback
  // Components don't need to know the source
  return (
    <div>
      <p>Latest packet: {telemetry[telemetry.length - 1]?.timestamp}</p>
    </div>
  );
}
```

## Monitoring Stream Status

Use the `StreamStatusIndicator` component to display stream health:

```typescript
import { StreamStatusIndicator } from "@/components/StreamStatusIndicator";
import { getStreamStatus } from "@/lib/stream-status";

// In dashboard header or status bar
<StreamStatusIndicator 
  status={getStreamStatus(
    wsConnected,
    wsError,
    telemetrySourceIsWebSocket,
    lastMessageTime,
    telemetry.length
  )}
/>
```

### Status Information

- **connection**: Live (WebSocket), Fallback Mode (polling), Disconnected
- **latency**: Message delivery time in milliseconds
- **buffer**: Number of buffered telemetry points
- **health indicator**: Green (healthy), Yellow (degraded >5s latency), Red (offline)

## Performance Characteristics

### Bandwidth
- Single telemetry packet: ~500-800 bytes
- At 1Hz: ~500-800 bytes/sec
- 300-point buffer: ~150-240 KB

### Latency
- Typical: 50-200ms from sensor to frontend
- Heartbeat: 5-second interval
- Stale detection: 10-second threshold

### CPU Usage
- Buffer management: O(1) insertion, O(n) cleanup
- Message parsing: JSON.parse + type validation
- Minimal processing in browser

## Configuration

### Server-side (.env)

```
VITE_AI_BASE_URL=http://localhost:8000
```

### Client-side customization

```typescript
// In dashboard-context.tsx
const {
  telemetry: wstelemetry,
  connected: wsConnected,
  error: wsError,
} = useTelemetryStream({
  maxBufferSize: 500,          // Increase from 300
  reconnectInterval: 5000,     // Slower reconnection
  maxReconnectAttempts: 20,    // More attempts
  heartbeatTimeout: 15000,     // Longer timeout
});
```

## Troubleshooting

### Connection Fails Immediately
1. Check backend is running: `curl http://localhost:8000/health`
2. Check WebSocket URL in browser console
3. Verify CORS configuration on server
4. Check firewall/network settings

### Heartbeat Timeouts
1. Server may be overloaded (check logs)
2. Network latency (check `messageLatency` in status)
3. Increase `heartbeatTimeout` if network is slow
4. Check for firewall rate limiting

### Memory Issues
1. Reduce `maxBufferSize` if telemetry packets are large
2. Check for message handler leaks in consuming components
3. Monitor memory usage in DevTools

### Data Inconsistency
1. Check conversion between telemetry formats
2. Verify Zod schemas validate incoming data
3. Check timestamps align between packets
4. Debug stale connection reconnections

## Migration Guide

### For Existing Components
No changes needed! Components using `useDashboard()` hook automatically benefit from WebSocket streaming.

### For New Components
Use the dashboard context hook instead of direct API calls:

```typescript
// Old way (polling)
const [telemetry, setTelemetry] = useState([]);
useEffect(() => {
  fetchTelemetry().then(setTelemetry);
}, []);

// New way (streaming)
const { telemetry } = useDashboard();
// Automatically streams from WebSocket or fallback
```

## Future Enhancements

1. **Adaptive Streaming**: Adjust sample rate based on network conditions
2. **Compression**: Implement message compression for slow connections
3. **Authentication**: Add JWT auth to WebSocket connections
4. **Multi-channel**: Stream multiple wells/sensors simultaneously
5. **Metrics**: Add Prometheus metrics for stream health monitoring
6. **Local Storage**: Cache buffer to IndexedDB for offline replay
