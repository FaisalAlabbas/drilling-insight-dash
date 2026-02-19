import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import type { UserRole, EdgeHealth, SamplingRate, TelemetryPacket, DecisionRecord, AlertEvent } from './types';
import { generateTelemetrySeries, generateDecisionSeries, generateAlerts, generateTelemetryPacket, generateDecisionRecord } from './mock-data';

type SidebarModule = 'live' | 'alerts' | 'history' | 'reporting' | 'admin';

interface DashboardContextType {
  role: UserRole;
  setRole: (r: UserRole) => void;
  edgeHealth: EdgeHealth;
  setEdgeHealth: (h: EdgeHealth) => void;
  activeModule: SidebarModule;
  setActiveModule: (m: SidebarModule) => void;
  samplingRate: SamplingRate;
  setSamplingRate: (r: SamplingRate) => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  telemetry: TelemetryPacket[];
  decisions: DecisionRecord[];
  alerts: AlertEvent[];
  selectedDecision: DecisionRecord | null;
  setSelectedDecision: (d: DecisionRecord | null) => void;
  selectedAlert: AlertEvent | null;
  setSelectedAlert: (a: AlertEvent | null) => void;
  drawerOpen: boolean;
  setDrawerOpen: (o: boolean) => void;
}

const DashboardContext = createContext<DashboardContextType | null>(null);

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [role, setRole] = useState<UserRole>('Engineer');
  const [edgeHealth, setEdgeHealth] = useState<EdgeHealth>('Healthy');
  const [activeModule, setActiveModule] = useState<SidebarModule>('live');
  const [samplingRate, setSamplingRate] = useState<SamplingRate>('1Hz');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDecision, setSelectedDecision] = useState<DecisionRecord | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<AlertEvent | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const [telemetry, setTelemetry] = useState<TelemetryPacket[]>(() => generateTelemetrySeries(180, 10000));
  const [decisions, setDecisions] = useState<DecisionRecord[]>(() => generateDecisionSeries(50));
  const [alerts] = useState<AlertEvent[]>(() => generateAlerts(25));

  // Auto-stream telemetry
  const telemetryRef = useRef(telemetry);
  telemetryRef.current = telemetry;
  
  useEffect(() => {
    const interval = setInterval(() => {
      const newPacket = generateTelemetryPacket(new Date());
      setTelemetry(prev => {
        const next = [...prev, newPacket];
        return next.length > 300 ? next.slice(-300) : next;
      });
    }, samplingRate === '10Hz' ? 100 : 1000);
    return () => clearInterval(interval);
  }, [samplingRate]);

  // Auto-stream decisions
  useEffect(() => {
    const interval = setInterval(() => {
      const packets = telemetryRef.current.slice(-5);
      if (packets.length > 0) {
        const newDecision = generateDecisionRecord(new Date(), packets);
        setDecisions(prev => {
          const next = [...prev, newDecision];
          return next.length > 200 ? next.slice(-200) : next;
        });
      }
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <DashboardContext.Provider value={{
      role, setRole, edgeHealth, setEdgeHealth,
      activeModule, setActiveModule, samplingRate, setSamplingRate,
      searchQuery, setSearchQuery,
      telemetry, decisions, alerts,
      selectedDecision, setSelectedDecision,
      selectedAlert, setSelectedAlert,
      drawerOpen, setDrawerOpen,
    }}>
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard() {
  const ctx = useContext(DashboardContext);
  if (!ctx) throw new Error('useDashboard must be used within DashboardProvider');
  return ctx;
}
