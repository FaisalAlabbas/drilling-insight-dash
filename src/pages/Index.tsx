import { DashboardProvider, useDashboard } from "@/lib/dashboard-context";
import { DashboardHeader } from "@/components/DashboardHeader";
import { DashboardSidebar } from "@/components/DashboardSidebar";
import { LiveMonitoringView } from "@/components/LiveMonitoringView";
import { AlertsView } from "@/components/AlertsView";
import { HistoryView } from "@/components/HistoryView";
import { ReportingView } from "@/components/ReportingView";
import { AdminPanel } from "@/components/AdminPanel";
import { DetailDrawer } from "@/components/DetailDrawer";
import DataQuality from "./DataQuality";

function DashboardContent() {
  const { activeModule, role } = useDashboard();

  const renderModule = () => {
    switch (activeModule) {
      case "live":
        return <LiveMonitoringView />;
      case "alerts":
        return <AlertsView />;
      case "history":
        return <HistoryView />;
      case "data-quality":
        return <DataQuality />;
      case "reporting":
        if (role === "Operator") return null;
        return <ReportingView />;
      case "admin":
        if (role !== "Admin") return null;
        return <AdminPanel />;
      default:
        return <LiveMonitoringView />;
    }
  };

  return (
    <div className="flex flex-col h-screen w-full">
      <DashboardHeader />
      <div className="flex flex-1 overflow-hidden">
        <DashboardSidebar />
        <main className="flex-1 overflow-y-auto p-4">{renderModule()}</main>
      </div>
      <DetailDrawer />
    </div>
  );
}

const Index = () => {
  return (
    <DashboardProvider>
      <DashboardContent />
    </DashboardProvider>
  );
};

export default Index;
