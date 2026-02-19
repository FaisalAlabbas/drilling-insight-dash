import { Activity, Bell, History, FileBarChart, Shield, Menu, X } from 'lucide-react';
import { useDashboard } from '@/lib/dashboard-context';
import { useState } from 'react';
import { cn } from '@/lib/utils';

const modules = [
  { id: 'live' as const, label: 'Live Monitoring', icon: Activity },
  { id: 'alerts' as const, label: 'Alerts', icon: Bell },
  { id: 'history' as const, label: 'Run History', icon: History },
  { id: 'reporting' as const, label: 'Reporting', icon: FileBarChart, roles: ['Engineer', 'Admin'] as const },
  { id: 'admin' as const, label: 'Admin', icon: Shield, roles: ['Admin'] as const },
];

export function DashboardSidebar() {
  const { activeModule, setActiveModule, role, alerts } = useDashboard();
  const [collapsed, setCollapsed] = useState(false);

  const criticalCount = alerts.filter(a => a.severity === 'CRITICAL').length;

  return (
    <>
      {/* Mobile toggle */}
      <button
        className="fixed top-3.5 right-4 z-50 md:hidden p-1.5 rounded bg-muted"
        onClick={() => setCollapsed(!collapsed)}
      >
        {collapsed ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
      </button>

      <aside className={cn(
        "bg-sidebar border-r border-sidebar-border flex flex-col shrink-0 transition-all duration-200",
        "fixed md:relative z-40 h-full md:h-auto",
        collapsed ? "w-56 translate-x-0" : "w-0 -translate-x-full md:w-56 md:translate-x-0"
      )}>
        <div className="p-4 border-b border-sidebar-border">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary/20 flex items-center justify-center">
              <Activity className="h-4 w-4 text-primary" />
            </div>
            <div>
              <p className="text-xs font-semibold text-sidebar-accent-foreground">RSS Monitor</p>
              <p className="text-[10px] text-sidebar-foreground">v1.3.2</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-2 space-y-0.5">
          {modules.map((mod) => {
            if (mod.roles && !mod.roles.includes(role as any)) return null;
            const isActive = activeModule === mod.id;
            return (
              <button
                key={mod.id}
                onClick={() => {
                  setActiveModule(mod.id);
                  setCollapsed(false);
                }}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
                )}
              >
                <mod.icon className={cn("h-4 w-4", isActive && "text-primary")} />
                <span className="truncate">{mod.label}</span>
                {mod.id === 'alerts' && criticalCount > 0 && (
                  <span className="ml-auto text-[10px] font-bold bg-signal-red/20 text-signal-red px-1.5 py-0.5 rounded-full">
                    {criticalCount}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="p-3 border-t border-sidebar-border">
          <div className="text-[10px] text-sidebar-foreground space-y-1">
            <p>Well: <span className="text-sidebar-accent-foreground font-medium">Permian-H7</span></p>
            <p>Depth: <span className="text-sidebar-accent-foreground font-mono">12,847 ft MD</span></p>
          </div>
        </div>
      </aside>
    </>
  );
}
