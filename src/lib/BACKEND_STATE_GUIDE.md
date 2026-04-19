# Backend State Machine Guide

## Overview

The `BackendState` type replaces the brittle boolean pattern (`isMockData`, `isBackendDegraded`, `isBackendImpaired`) with an explicit, type-safe union type that represents all possible backend connectivity states.

## State Machine Design

Five mutually-exclusive states:

### 1. **`healthy`** — Backend is responsive and functional
```typescript
{
  type: "healthy";
  systemMode: "SIMULATION" | "PROTOTYPE";
  actuatorStatus: ActuatorStatus | null;
}
```
- Backend returns 200 and reports `status: "healthy"`
- All subsystems operational
- Real telemetry and predictions available

### 2. **`degraded`** — Backend responsive but reports impaired subsystems
```typescript
{
  type: "degraded";
  systemMode: "SIMULATION" | "PROTOTYPE";
  actuatorStatus: ActuatorStatus | null;
}
```
- Backend returns 200 but reports `status: "degraded"`
- Some subsystem impaired (e.g., no telemetry data, model unavailable)
- Predictions may still work; telemetry stream may be paused

### 3. **`prototype`** — Backend in prototype/read-only mode
```typescript
{
  type: "prototype";
  systemMode: "PROTOTYPE";
  actuatorStatus: ActuatorStatus | null;
}
```
- Backend reports `system_mode: "PROTOTYPE"`
- Read-only operations only
- Limited functionality (no write commands, no actuator control)

### 4. **`unreachable-simulated`** — Backend unreachable; development mode fallback
```typescript
{
  type: "unreachable-simulated";
  reason: string;
}
```
- Backend is unreachable (network error, timeout, etc.)
- App is running in **development** mode
- Synthetic telemetry and mock decisions generated for convenience
- Safe for development/testing

### 5. **`unreachable-production`** — Backend unreachable; production critical
```typescript
{
  type: "unreachable-production";
  reason: string;
}
```
- Backend is unreachable
- App is running in **production** mode
- No synthetic data generated
- UI must show data unavailable (critical alert)

## Using the State Machine

### In Components

Import and use predicates from `backend-state.ts`:

```typescript
import { useDashboard } from "@/lib/dashboard-context";
import {
  isBackendAvailable,
  isDataSimulated,
  isProductionOutage,
  getBackendStatusMessage,
  getBackendStatusColor,
} from "@/lib/backend-state";

export function MyComponent() {
  const { backendState } = useDashboard();

  // Check if backend is reachable
  if (!isBackendAvailable(backendState)) {
    return <div>Backend unavailable</div>;
  }

  // Check if data is synthetic
  if (isDataSimulated(backendState)) {
    return <div>Showing simulated data</div>;
  }

  // Check for critical production outage
  if (isProductionOutage(backendState)) {
    return <AlertBanner message="CRITICAL: Backend unavailable in production" />;
  }

  return <div>Normal operation</div>;
}
```

### Available Predicates

| Predicate | Returns | Purpose |
|-----------|---------|---------|
| `isBackendAvailable(state)` | boolean | Backend is reachable (healthy, degraded, or prototype) |
| `isBackendUnreachable(state)` | boolean | Backend is unreachable (either type) |
| `isDataSimulated(state)` | boolean | Data shown is from mock generation (unreachable-simulated or prototype) |
| `isBackendDegraded(state)` | boolean | Backend is up but reports impaired subsystems |
| `isProductionOutage(state)` | boolean | Production-critical: unreachable in production mode |
| `isPrototypeMode(state)` | boolean | Backend is in prototype/read-only mode |

### Status Messages and Indicators

Use `getBackendStatusMessage()` and `getBackendStatusColor()` for UI display:

```typescript
import { getBackendStatusMessage, getBackendStatusColor } from "@/lib/backend-state";

const message = getBackendStatusMessage(backendState);
// "Backend online"
// "Backend degraded - limited functionality"
// "Backend unavailable - development mode (simulated data)"
// "Backend unavailable - production mode (data unavailable)"
// "Prototype mode - read-only"

const color = getBackendStatusColor(backendState);
// "green" | "yellow" | "red" | "gray"
```

## Type Safety

The state machine is exhaustively typed. Using a switch statement is safe:

```typescript
function handleState(state: BackendState): string {
  switch (state.type) {
    case "healthy":
      return `Backend healthy, system mode: ${state.systemMode}`;
    case "degraded":
      return `Backend degraded, system mode: ${state.systemMode}`;
    case "prototype":
      return "Prototype mode";
    case "unreachable-simulated":
      return `Development mode: ${state.reason}`;
    case "unreachable-production":
      return `CRITICAL: ${state.reason}`;
    default:
      const _exhaustive: never = state;
      return _exhaustive;
  }
}
```

If you add a new state variant but forget to handle it, TypeScript will error on the `default` case.

## Migrating from Old API

### Old Pattern (Don't Use)
```typescript
// ❌ Brittle boolean combinations
if (isMockData && isBackendDegraded) { /* ? */ }
if (!isBackendDegraded && isBackendImpaired) { /* ? */ }
if (!isMockData && !isBackendDegraded) { /* ? */ }
```

### New Pattern (Do Use)
```typescript
// ✅ Explicit states with clear semantics
if (isDataSimulated(backendState)) { /* synthetic data */ }
if (isProductionOutage(backendState)) { /* critical alert */ }
if (isBackendDegraded(backendState)) { /* impaired subsystems */ }
```

## Context API

The dashboard context still provides raw state for components that need it:

```typescript
const {
  backendState,           // The unified BackendState
  authToken,
  authUser,
  login,
  logout,
  // ... other context properties
} = useDashboard();
```

The context no longer exposes:
- ~~`isMockData`~~ → Use `isDataSimulated(backendState)` instead
- ~~`isBackendDegraded`~~ → Use `isProductionOutage(backendState)` instead
- ~~`isBackendImpaired`~~ → Use `isBackendDegraded(backendState)` instead
- ~~`systemMode`~~ → Access via `backendState.systemMode` (when available) or use `isPrototypeMode(backendState)`

## Design Principles

1. **Mutual Exclusion**: Exactly one state is active at any time. No boolean combinations.
2. **Exhaustiveness**: TypeScript enforces handling all state variants.
3. **Semantics**: State names clearly describe backend connectivity and data source.
4. **Completeness**: Each state carries all data needed to render UI correctly.
5. **Fallback Predictability**: Development mode has safe fallback; production mode has none.

## Testing

When testing components that use `backendState`:

```typescript
import { render } from "@testing-library/react";
import { DashboardProvider } from "@/lib/dashboard-context";

// Override context with specific state via mock or test provider
const mockState: BackendState = {
  type: "healthy",
  systemMode: "SIMULATION",
  actuatorStatus: null,
};

// Then test UI behavior for each state variant
```

## Files Modified

- `src/lib/backend-state.ts` — New file with state machine definition and predicates
- `src/lib/dashboard-context.tsx` — Updated to use `deriveBackendState()` instead of boolean logic
- `src/components/DashboardHeader.tsx` — Updated to use predicates instead of booleans

## Benefits

✓ **No more boolean bugs**: States are mutually exclusive  
✓ **Self-documenting**: State names explain what's happening  
✓ **Type-safe**: TypeScript enforces exhaustive handling  
✓ **Clearer logic**: No more `!a && !b && c` conditionals  
✓ **Easier testing**: Can test each state independently  
✓ **Scalable**: Adding new states is safe and detected at compile time
