import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useRef,
} from "react";
import type {
  TelemetryPacket,
  DecisionRecord,
  AlertEvent,
  AlertSeverity,
} from "./api-types";
import {
  generateTelemetrySeries,
  generateDecisionSeries,
  generateAlerts,
  generateTelemetryPacket,
  generateDecisionRecord,
  generateAlertsFromData,
  createManualAlert,
} from "./mock-data";
import { getRecommendation, checkBackendHealth } from "./api-service";
import { useConfig } from "./configApi";
import { DASHBOARD_MODULES, getAccessibleModules, hasAccess, type ModuleId } from "./dashboard-modules";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";

type SidebarModule = ModuleId;

export interface DashboardContextType {
  role: string;
  setRole: (r: string) => void;
  edgeHealth: "Healthy" | "Degraded";
  setEdgeHealth: (h: "Healthy" | "Degraded") => void;
  activeModule: SidebarModule;
  setActiveModule: (m: SidebarModule) => void;
  samplingRate: string;
  setSamplingRate: (r: string) => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  telemetry: TelemetryPacket[];
  decisions: DecisionRecord[];
  alerts: AlertEvent[];
  accessibleModules: typeof DASHBOARD_MODULES;
  hasModuleAccess: (moduleId: ModuleId) => boolean;
  addAlert: (
    title: string,
    description: string,
    severity?: AlertSeverity
  ) => void;
  markAlertsAsRead: () => void;
  unreadAlertCount: number;
  selectedDecision: DecisionRecord | null;
  setSelectedDecision: (d: DecisionRecord | null) => void;
  selectedAlert: AlertEvent | null;
  setSelectedAlert: (a: AlertEvent | null) => void;
  drawerOpen: boolean;
  setDrawerOpen: (o: boolean) => void;
}

const DashboardContext = createContext<DashboardContextType | null>(null);

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [role, setRole] = useState<UserRole>("Engineer");
  const [edgeHealth, setEdgeHealth] = useState<EdgeHealth>("Healthy");
  const [activeModule, setActiveModule] = useState<SidebarModule>("live");
  const [samplingRate, setSamplingRate] = useState<SamplingRate>("1Hz");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDecision, setSelectedDecision] = useState<DecisionRecord | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<AlertEvent | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [backendAvailable, setBackendAvailable] = useState(false);

  // Use config from backend
  const { data: config, isLoading: configLoading } = useConfig();

  const [telemetry, setTelemetry] = useState<TelemetryPacket[]>(() =>
    generateTelemetrySeries(180, 10000)
  );
  const [decisions, setDecisions] = useState<DecisionRecord[]>(() =>
    generateDecisionSeries(50)
  );

  // Initialize alerts from localStorage
  const [alerts, setAlerts] = useState<AlertEvent[]>(() => {
    try {
      const saved = localStorage.getItem("drilling_alerts");
      return saved ? JSON.parse(saved) : generateAlerts(25);
    } catch {
      return generateAlerts(25);
    }
  });

  // Persist alerts to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem("drilling_alerts", JSON.stringify(alerts));
    } catch (error) {
      console.error("Failed to save alerts to localStorage:", error);
    }
  }, [alerts]);

  // Add alert function (for manual alerts)
  const addAlert = useCallback(
    (
      title: string,
      description: string,
      severity: AlertSeverity = "medium"
    ) => {
      const newAlert = createManualAlert(title, description, severity);
      setAlerts((prev) => [newAlert, ...prev].slice(0, 100)); // Keep last 100 alerts
    },
    []
  );

  // Mark all alerts as read
  const markAlertsAsRead = useCallback(() => {
    setAlerts((prev) => prev.map((alert) => ({ ...alert, isRead: true })));
  }, []);

  // Calculate unread count
  const unreadAlertCount = alerts.filter((a) => !a.isRead).length;

  // Mark alerts as read when entering alerts module
  useEffect(() => {
    if (activeModule === "alerts") {
      markAlertsAsRead();
    }
  }, [activeModule, markAlertsAsRead]);

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth().then(setBackendAvailable);
  }, []);

  // Stream telemetry via WebSocket with fallback to mock generation
  const {
    telemetry: wstelemetry,
    connected: wsConnected,
    error: wsError,
  } = useTelemetryStream({
    maxBufferSize: 300,
    onError: (error) => {
      console.error("WebSocket telemetry stream error:", error);
      // Will fallback to polling
    },
  });

  // Initialize telemetry with WebSocket data or mock
  const [telemetrySourceIsWebSocket, setTelemetrySourceIsWebSocket] = useState(
    false
  );

  // Integrate WebSocket telemetry into state
  useEffect(() => {
    if (wstelemetry.length > 0) {
      setTelemetry(wstelemetry);
      setTelemetrySourceIsWebSocket(true);
    }
  }, [wstelemetry]);

  // Auto-stream telemetry from backend polling as fallback or mock
  const telemetryRef = useRef(telemetry);
  telemetryRef.current = telemetry;

  // Polling fallback when WebSocket is not connected
  useEffect(() => {
    // Skip polling if WebSocket is connected and has data
    if (telemetrySourceIsWebSocket && wsConnected && wstelemetry.length > 0) {
      return;
    }

    const interval = setInterval(
      async () => {
        // Only try backend polling if WebSocket isn't available
        if (!wsConnected && backendAvailable) {
          try {
            // Try to get telemetry from backend REST endpoint
            const response = await fetch(
              `${import.meta.env.VITE_AI_BASE_URL || "http://localhost:8000"}/telemetry/next`
            );
            if (response.ok) {
              const newPacket: TelemetryPacket = await response.json();
              setTelemetry((prev) => {
                const next = [...prev, newPacket];
                return next.length > 300 ? next.slice(-300) : next;
              });
              return;
            }
          } catch (error) {
            console.warn(
              "Failed to fetch telemetry from backend, falling back to mock:",
              error
            );
          }
        }

        // Fallback to mock generation
        const newPacket = generateTelemetryPacket(new Date());
        setTelemetry((prev) => {
          const next = [...prev, newPacket];
          return next.length > 300 ? next.slice(-300) : next;
        });
      },
      samplingRate === "10Hz" ? 100 : 1000
    );
    return () => clearInterval(interval);
  }, [samplingRate, backendAvailable, wsConnected, telemetrySourceIsWebSocket, wstelemetry.length]);

  // Auto-stream decisions from backend or mock
  useEffect(() => {
    const interval = setInterval(async () => {
      const packets = telemetryRef.current.slice(-5);
      if (packets.length > 0) {
        let newDecision: DecisionRecord;

        // Try to get prediction from backend if available
        if (backendAvailable && packets.length > 0) {
          const latestTelemetry = packets[packets.length - 1];
          const apiDecision = await getRecommendation(latestTelemetry);
          newDecision = apiDecision || generateDecisionRecord(new Date(), packets);
        } else {
          // Fall back to mock generation
          newDecision = generateDecisionRecord(new Date(), packets);
        }

        setDecisions((prev) => {
          const next = [...prev, newDecision];
          return next.length > 200 ? next.slice(-200) : next;
        });

        // Generate alerts based on real telemetry and decision data
        const latestTelemetry = packets[packets.length - 1];
        const newAlerts = generateAlertsFromData(
          latestTelemetry,
          newDecision,
          config?.limits
        );

        if (newAlerts.length > 0) {
          setAlerts((prev) => [...newAlerts, ...prev].slice(0, 100)); // Keep last 100 alerts
        }
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [backendAvailable, config]);

  // Get accessible modules based on current role
  const accessibleModules = getAccessibleModules(role);

  // Check if user has access to a specific module
  const hasModuleAccess = useCallback(
    (moduleId: ModuleId) => {
      const module = DASHBOARD_MODULES[moduleId];
      return module && module.enabled && hasAccess(role, module.requiredRole);
    },
    [role]
  );

  return (
    <DashboardContext.Provider
      value={{
        role,
        setRole,
        edgeHealth,
        setEdgeHealth,
        activeModule,
        setActiveModule,
        samplingRate,
        setSamplingRate,
        searchQuery,
        setSearchQuery,
        telemetry,
        decisions,
        alerts,
        addAlert,
        markAlertsAsRead,
        unreadAlertCount,
        selectedDecision,
        setSelectedDecision,
        selectedAlert,
        setSelectedAlert,
        drawerOpen,
        setDrawerOpen,
        accessibleModules,
        hasModuleAccess,
      }}
    >
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard() {
  const ctx = useContext(DashboardContext);
  if (!ctx) throw new Error("useDashboard must be used within DashboardProvider");
  return ctx;
}
