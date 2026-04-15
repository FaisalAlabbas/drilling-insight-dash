import { Search, Activity, Brain, Download, AlertTriangle } from "lucide-react";
import { useDashboard } from "@/lib/dashboard-context";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useNavigate, useLocation } from "react-router-dom";
import type { UserRole } from "@/lib/types";
import { exportToCSV } from "@/lib/export-utils";

export function DashboardHeader() {
  const { role, setRole, edgeHealth, searchQuery, setSearchQuery, telemetry, decisions, isMockData, isBackendDegraded } =
    useDashboard();
  const navigate = useNavigate();
  const location = useLocation();

  const isDashboard = location.pathname === "/";
  const isEvaluation = location.pathname === "/ai-evaluation";

  const handleExport = () => {
    exportToCSV(telemetry, decisions);
  };

  return (
    <>
      {isBackendDegraded && (
        <div className="bg-destructive/90 text-destructive-foreground flex items-center justify-center gap-2 px-4 py-1.5 text-xs font-medium">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
          <span>
            Backend unreachable — live data is unavailable. Contact your system administrator.
          </span>
        </div>
      )}
      {!isBackendDegraded && isMockData && (
        <div className="bg-signal-yellow/20 text-signal-yellow border-b border-signal-yellow/30 flex items-center justify-center gap-2 px-4 py-1 text-xs font-medium">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
          <span>Development mode — displaying simulated data (backend not connected)</span>
        </div>
      )}
      <header className="h-14 border-b border-border bg-card flex items-center px-4 gap-4 shrink-0">
      <div className="flex items-center gap-2 mr-4">
        <Activity className="h-5 w-5 text-primary" />
        <h1 className="text-sm font-semibold tracking-tight hidden sm:block">
          Surface Dashboard
        </h1>
        <span className="text-[10px] font-mono bg-muted text-muted-foreground px-2 py-0.5 rounded-sm hidden md:inline">
          MONITORING ONLY
        </span>
      </div>

      <div className="flex-1 max-w-xs">
        {isDashboard && (
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search logs & events..."
              className="h-8 pl-8 text-xs bg-muted border-border"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        )}
      </div>

      <div className="flex items-center gap-3 ml-auto">
        {isDashboard && (
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/ai-evaluation")}
              className="flex items-center gap-2 text-xs h-8"
            >
              <Brain className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">AI Evaluation</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
              className="flex items-center gap-2 text-xs h-8"
            >
              <Download className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Export CSV</span>
            </Button>
          </>
        )}
        {isEvaluation && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate("/")}
            className="flex items-center gap-2 text-xs h-8"
          >
            <Activity className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Dashboard</span>
          </Button>
        )}

        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium ${
            edgeHealth === "Healthy"
              ? "bg-signal-green/15 text-signal-green"
              : "bg-signal-yellow/15 text-signal-yellow"
          }`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              edgeHealth === "Healthy"
                ? "bg-signal-green signal-pulse"
                : "bg-signal-yellow signal-pulse"
            }`}
          />
          Edge: {edgeHealth}
        </div>

        <Select value={role} onValueChange={(v) => setRole(v as UserRole)}>
          <SelectTrigger className="h-8 w-[130px] text-xs bg-muted border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Operator">Operator</SelectItem>
            <SelectItem value="Engineer">Engineer</SelectItem>
            <SelectItem value="Admin">Admin</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </header>
    </>
  );
}
