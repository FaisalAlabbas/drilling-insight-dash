import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useRef,
} from "react";
import type {
  UserRole,
  EdgeHealth,
  SamplingRate,
  TelemetryPacket,
  DecisionRecord,
  AlertEvent,
} from "./types";
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

type SidebarModule =
  | "live"
  | "alerts"
  | "history"
  | "data-quality"
  | "reporting"
  | "admin";

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
  addAlert: (
    title: string,
    description: string,
    severity?: "INFO" | "WARN" | "CRITICAL"
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
      severity: "INFO" | "WARN" | "CRITICAL" = "WARN"
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

  // Auto-stream telemetry from backend or mock
  const telemetryRef = useRef(telemetry);
  telemetryRef.current = telemetry;

  useEffect(() => {
    const interval = setInterval(
      async () => {
        if (backendAvailable) {
          try {
            // Try to get telemetry from backend
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
  }, [samplingRate, backendAvailable]);

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
