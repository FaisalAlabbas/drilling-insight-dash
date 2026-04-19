/**
 * Frontend smoke tests for dashboard functionality
 * Uses Vitest + React Testing Library
 */

import { describe, it, expect } from 'vitest';
import * as backendState from '@/lib/backend-state';

describe('Frontend Smoke Tests', () => {
  describe('Backend State Machine', () => {
    it('should identify healthy backend state correctly', () => {
      const state = backendState.deriveBackendState(
        'healthy',
        'SIMULATION',
        null,
        false
      );

      expect(state.type).toBe('healthy');
      expect(backendState.isBackendAvailable(state)).toBe(true);
      expect(backendState.isDataSimulated(state)).toBe(false);
      expect(backendState.isProductionOutage(state)).toBe(false);
    });

    it('should identify degraded backend state correctly', () => {
      const state = backendState.deriveBackendState(
        'degraded',
        'SIMULATION',
        null,
        false
      );

      expect(state.type).toBe('degraded');
      expect(backendState.isBackendAvailable(state)).toBe(true);
      expect(backendState.isBackendDegraded(state)).toBe(true);
    });

    it('should identify production outage correctly', () => {
      const state = backendState.deriveBackendState(
        'unreachable',
        'SIMULATION',
        null,
        true
      );

      expect(state.type).toBe('unreachable-production');
      expect(backendState.isProductionOutage(state)).toBe(true);
      expect(backendState.isBackendAvailable(state)).toBe(false);
    });

    it('should identify development fallback correctly', () => {
      const state = backendState.deriveBackendState(
        'unreachable',
        'SIMULATION',
        null,
        false
      );

      expect(state.type).toBe('unreachable-simulated');
      expect(backendState.isDataSimulated(state)).toBe(true);
    });

    it('should identify prototype mode correctly', () => {
      const state = backendState.deriveBackendState(
        'healthy',
        'PROTOTYPE',
        null,
        false
      );

      expect(state.type).toBe('prototype');
      expect(backendState.isPrototypeMode(state)).toBe(true);
    });
  });

  describe('Status Display Helpers', () => {
    it('should generate appropriate status messages', () => {
      const healthyState = backendState.deriveBackendState(
        'healthy',
        'SIMULATION',
        null,
        false
      );
      expect(backendState.getBackendStatusMessage(healthyState)).toBe(
        'Backend online'
      );

      const degradedState = backendState.deriveBackendState(
        'degraded',
        'SIMULATION',
        null,
        false
      );
      expect(backendState.getBackendStatusMessage(degradedState)).toBe(
        'Backend degraded - limited functionality'
      );

      const productionOutage = backendState.deriveBackendState(
        'unreachable',
        'SIMULATION',
        null,
        true
      );
      expect(backendState.getBackendStatusMessage(productionOutage)).toContain(
        'CRITICAL'
      );
    });

    it('should assign appropriate status colors', () => {
      const healthyState = backendState.deriveBackendState(
        'healthy',
        'SIMULATION',
        null,
        false
      );
      expect(backendState.getBackendStatusColor(healthyState)).toBe('green');

      const degradedState = backendState.deriveBackendState(
        'degraded',
        'SIMULATION',
        null,
        false
      );
      expect(backendState.getBackendStatusColor(degradedState)).toBe('yellow');

      const outageState = backendState.deriveBackendState(
        'unreachable',
        'SIMULATION',
        null,
        true
      );
      expect(backendState.getBackendStatusColor(outageState)).toBe('red');

      const devFallbackState = backendState.deriveBackendState(
        'unreachable',
        'SIMULATION',
        null,
        false
      );
      expect(backendState.getBackendStatusColor(devFallbackState)).toBe('gray');
    });
  });
});
