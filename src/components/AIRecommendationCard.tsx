import { useDashboard } from '@/lib/dashboard-context';
import { cn } from '@/lib/utils';
import { Shield, AlertTriangle, CheckCircle2, XCircle, ArrowRight } from 'lucide-react';

export function AIRecommendationCard() {
  const { decisions, edgeHealth } = useDashboard();
  const latest = decisions[decisions.length - 1];
  if (!latest) return null;

  const conf = latest.confidence_score;
  const confColor = conf >= 0.75 ? 'text-signal-green' : conf >= 0.5 ? 'text-signal-yellow' : 'text-signal-red';
  const confBg = conf >= 0.75 ? 'bg-signal-green/15' : conf >= 0.5 ? 'bg-signal-yellow/15' : 'bg-signal-red/15';

  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">AI Recommendation</h3>
        <span className="text-[10px] font-mono text-muted-foreground">{latest.model_version}</span>
      </div>

      <div className="text-center py-2">
        <p className="text-3xl font-bold tracking-tight">{latest.steering_command}</p>
        <div className={cn("inline-flex items-center gap-1.5 mt-2 px-3 py-1 rounded-full text-xs font-semibold", confBg, confColor)}>
          <span>{(conf * 100).toFixed(0)}% confidence</span>
        </div>
      </div>

      <div className="space-y-2 border-t border-border pt-3">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Gate Outcome</span>
          <span className={cn(
            "flex items-center gap-1 font-semibold",
            latest.gate_outcome === 'ACCEPTED' ? 'text-signal-green' : 'text-signal-red'
          )}>
            {latest.gate_outcome === 'ACCEPTED' ? <CheckCircle2 className="h-3.5 w-3.5" /> : <XCircle className="h-3.5 w-3.5" />}
            {latest.gate_outcome}
          </span>
        </div>

        {latest.rejection_reason && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Reason</span>
            <span className="text-signal-red font-mono text-[11px]">{latest.rejection_reason}</span>
          </div>
        )}

        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Execution</span>
          <span className={cn(
            "font-semibold",
            latest.execution_status === 'SENT' ? 'text-signal-green' : 'text-signal-amber'
          )}>
            {latest.execution_status}
          </span>
        </div>

        {latest.fallback_mode && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Fallback</span>
            <span className="text-signal-amber font-mono text-[11px]">{latest.fallback_mode}</span>
          </div>
        )}
      </div>

      <div className="border-t border-border pt-3">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Edge Health</span>
          <span className={cn(
            "flex items-center gap-1 font-semibold",
            edgeHealth === 'Healthy' ? 'text-signal-green' : 'text-signal-yellow'
          )}>
            <span className={cn("h-1.5 w-1.5 rounded-full signal-pulse",
              edgeHealth === 'Healthy' ? 'bg-signal-green' : 'bg-signal-yellow'
            )} />
            {edgeHealth}
          </span>
        </div>
      </div>
    </div>
  );
}
