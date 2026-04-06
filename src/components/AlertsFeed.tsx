import { useDashboard } from '@/lib/dashboard-context';
import { cn } from '@/lib/utils';
import { AlertTriangle, Info, AlertOctagon } from 'lucide-react';
import type { AlertSeverity } from '@/lib/types';

const severityConfig = {
  CRITICAL: { icon: AlertOctagon, color: 'text-signal-red', bg: 'bg-signal-red/10', border: 'border-signal-red/30' },
  WARN: { icon: AlertTriangle, color: 'text-signal-yellow', bg: 'bg-signal-yellow/10', border: 'border-signal-yellow/30' },
  INFO: { icon: Info, color: 'text-signal-blue', bg: 'bg-signal-blue/10', border: 'border-signal-blue/30' },
};

interface AlertsFeedProps {
  filter?: AlertSeverity | 'ALL' | 'UNREAD';
}

export function AlertsFeed({ filter = 'ALL' }: AlertsFeedProps) {
  const { alerts, setSelectedAlert, setDrawerOpen, searchQuery } = useDashboard();

  const filtered = alerts.filter(a => {
    // Apply search filter
    const matchesSearch = !searchQuery || a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (!matchesSearch) return false;

    // Apply severity/read filter
    if (filter === 'UNREAD') return !a.isRead;
    if (filter === 'ALL') return true;
    return a.severity === filter;
  });

  return (
    <div className="space-y-2">
      {filtered.map((alert) => {
        const config = severityConfig[alert.severity];
        const Icon = config.icon;
        return (
          <button
            key={alert.id}
            onClick={() => { setSelectedAlert(alert); setDrawerOpen(true); }}
            className={cn(
              "w-full text-left border rounded-lg p-3 transition-colors hover:bg-muted/30",
              config.border,
              !alert.isRead && "bg-muted/20 border-2"
            )}
          >
            <div className="flex items-start gap-3">
              <div className={cn("p-1.5 rounded-md shrink-0", config.bg)}>
                <Icon className={cn("h-3.5 w-3.5", config.color)} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <p className={cn("text-sm font-medium truncate", !alert.isRead && "font-bold")}>{alert.title}</p>
                  <div className="flex items-center gap-2">
                    {!alert.isRead && <span className="h-2 w-2 rounded-full bg-signal-red"></span>}
                    <span className={cn("text-[10px] font-semibold px-1.5 py-0.5 rounded", config.bg, config.color)}>
                      {alert.severity}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{alert.description}</p>
                <div className="flex items-center gap-2 mt-1.5">
                  <span className="text-[10px] font-mono text-muted-foreground">
                    {new Date(alert.timestamp).toLocaleTimeString('en-US', { hour12: false })}
                  </span>
                  {alert.related_signals.length > 0 && (
                    <div className="flex gap-1">
                      {alert.related_signals.map(s => (
                        <span key={s} className="text-[9px] px-1.5 py-0.5 bg-muted rounded text-muted-foreground">{s}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
