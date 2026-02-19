import { DashboardProvider, useDashboard } from '@/lib/dashboard-context';
import { DashboardHeader } from '@/components/DashboardHeader';
import { DashboardSidebar } from '@/components/DashboardSidebar';
import { LiveMonitoringView } from '@/components/LiveMonitoringView';
import { AlertsView } from '@/components/AlertsView';
import { DetailDrawer } from '@/components/DetailDrawer';

function DashboardContent() {
  const { activeModule, role } = useDashboard();

  const renderModule = () => {
    switch (activeModule) {
      case 'live':
        return <LiveMonitoringView />;
      case 'alerts':
        return <AlertsView />;
      case 'history':
        return (
          <div className="bg-card border border-border rounded-lg p-8 text-center">
            <p className="text-muted-foreground text-sm">Run History & Audit Logs</p>
            <p className="text-xs text-muted-foreground mt-1">Coming in Phase 2</p>
          </div>
        );
      case 'reporting':
        if (role === 'Operator') return null;
        return (
          <div className="bg-card border border-border rounded-lg p-8 text-center">
            <p className="text-muted-foreground text-sm">Reporting & Export</p>
            <p className="text-xs text-muted-foreground mt-1">Coming in Phase 2</p>
          </div>
        );
      case 'admin':
        if (role !== 'Admin') return null;
        return (
          <div className="bg-card border border-border rounded-lg p-8 text-center">
            <p className="text-muted-foreground text-sm">Admin Panel</p>
            <p className="text-xs text-muted-foreground mt-1">Coming in Phase 2</p>
          </div>
        );
      default:
        return <LiveMonitoringView />;
    }
  };

  return (
    <div className="flex flex-col h-screen w-full">
      <DashboardHeader />
      <div className="flex flex-1 overflow-hidden">
        <DashboardSidebar />
        <main className="flex-1 overflow-y-auto p-4">
          {renderModule()}
        </main>
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
