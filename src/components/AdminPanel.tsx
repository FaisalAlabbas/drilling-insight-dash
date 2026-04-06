import { useDashboard } from '@/lib/dashboard-context';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Shield, Users, Settings, Database, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { UserRole, EdgeHealth } from '@/lib/types';

interface User {
  id: string;
  name: string;
  role: UserRole;
  status: 'active' | 'inactive';
  lastLogin: string;
}

export function AdminPanel() {
  const { role, setRole, edgeHealth, setEdgeHealth, telemetry, decisions, alerts } = useDashboard();
  const [adminTab, setAdminTab] = useState<'users' | 'health' | 'config'>('users');

  const [users] = useState<User[]>([
    { id: '1', name: 'John Operator', role: 'Operator', status: 'active', lastLogin: '2 min ago' },
    { id: '2', name: 'Jane Engineer', role: 'Engineer', status: 'active', lastLogin: '15 min ago' },
    { id: '3', name: 'Admin User', role: 'Admin', status: 'active', lastLogin: 'Now' },
    { id: '4', name: 'Bob Operator', role: 'Operator', status: 'inactive', lastLogin: '2 days ago' },
  ]);

  const systemStats = {
    uptimePercent: 99.8,
    avgLatency: 24,
    totalRequests: decisions.length,
    errorRate: 0.2,
    dataPoints: telemetry.length,
    activeAlerts: alerts.filter(a => !a.isRead).length,
  };

  const tabs = [
    { id: 'users' as const, label: 'User Management', icon: Users },
    { id: 'health' as const, label: 'System Health', icon: AlertCircle },
    { id: 'config' as const, label: 'Configuration', icon: Settings },
  ];

  return (
    <div className="space-y-4">
      {/* Admin Info Bar */}
      <div className="bg-card border border-border rounded-lg p-4 flex items-center gap-3">
        <div className="h-10 w-10 rounded-lg bg-primary/20 flex items-center justify-center">
          <Shield className="h-5 w-5 text-primary" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-semibold">Administration Panel</p>
          <p className="text-xs text-muted-foreground">System configuration and user management</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-muted-foreground">Current Role</p>
          <p className="text-sm font-bold text-primary">{role}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 bg-card border border-border rounded-lg p-2 w-fit">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setAdminTab(tab.id)}
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded text-xs font-medium transition-colors',
              adminTab === tab.id
                ? 'bg-primary/20 text-primary'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* User Management Tab */}
      {adminTab === 'users' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Total Users</p>
              <p className="text-2xl font-bold mt-1">{users.length}</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Active Now</p>
              <p className="text-2xl font-bold mt-1 text-signal-green">{users.filter(u => u.status === 'active').length}</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Roles</p>
              <p className="text-2xl font-bold mt-1">3</p>
              <p className="text-[10px] text-muted-foreground mt-1">Operator, Engineer, Admin</p>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <table className="w-full text-xs">
              <thead className="bg-muted border-b border-border">
                <tr>
                  <th className="px-3 py-2 text-left font-semibold">User</th>
                  <th className="px-3 py-2 text-left font-semibold">Role</th>
                  <th className="px-3 py-2 text-center font-semibold">Status</th>
                  <th className="px-3 py-2 text-left font-semibold">Last Login</th>
                  <th className="px-3 py-2 text-center font-semibold">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {users.map(user => (
                  <tr key={user.id} className="hover:bg-muted/50 transition-colors">
                    <td className="px-3 py-2 font-medium">{user.name}</td>
                    <td className="px-3 py-2">
                      <select
                        value={user.role}
                        disabled
                        className="bg-muted border border-border rounded px-2 py-1 text-xs"
                      >
                        <option>Operator</option>
                        <option>Engineer</option>
                        <option>Admin</option>
                      </select>
                    </td>
                    <td className="px-3 py-2 text-center">
                      <span className={cn(
                        'inline-block px-2 py-1 rounded text-[9px] font-bold',
                        user.status === 'active'
                          ? 'bg-signal-green/20 text-signal-green'
                          : 'bg-muted text-muted-foreground'
                      )}>
                        {user.status === 'active' ? '● Active' : '○ Inactive'}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">{user.lastLogin}</td>
                    <td className="px-3 py-2 text-center">
                      <button className="text-primary hover:underline text-xs font-medium">
                        {user.status === 'active' ? 'Deactivate' : 'Reactivate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* System Health Tab */}
      {adminTab === 'health' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            <div className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-semibold uppercase">System Status</h3>
                <CheckCircle2 className="h-5 w-5 text-signal-green" />
              </div>
              <div className="space-y-3">
                <div>
                  <p className="text-[10px] text-muted-foreground uppercase mb-1">Uptime</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-muted rounded h-2 overflow-hidden">
                      <div
                        className="bg-signal-green h-full"
                        style={{ width: `${systemStats.uptimePercent}%` }}
                      />
                    </div>
                    <span className="text-sm font-bold">{systemStats.uptimePercent}%</span>
                  </div>
                </div>
                <div>
                  <p className="text-[10px] text-muted-foreground uppercase mb-1">API Response Time</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xl font-bold">{systemStats.avgLatency}ms</span>
                    <span className="text-xs text-muted-foreground">average</span>
                  </div>
                </div>
                <div>
                  <p className="text-[10px] text-muted-foreground uppercase mb-1">Error Rate</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xl font-bold text-signal-green">{systemStats.errorRate}%</span>
                    <span className="text-xs text-muted-foreground">last 24h</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-card border border-border rounded-lg p-4">
              <h3 className="text-xs font-semibold uppercase mb-4">Data Processing</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-muted-foreground">Telemetry Points</span>
                  <span className="text-sm font-bold">{systemStats.dataPoints}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-muted-foreground">Model Decisions</span>
                  <span className="text-sm font-bold">{systemStats.totalRequests}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-muted-foreground">Active Alerts</span>
                  <span className={cn(
                    'text-sm font-bold',
                    systemStats.activeAlerts > 5 ? 'text-signal-red' : 'text-signal-green'
                  )}>
                    {systemStats.activeAlerts}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="text-xs font-semibold uppercase mb-3">System Health Indicators</h3>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
              <div className="bg-muted rounded p-3">
                <p className="text-[10px] text-muted-foreground mb-1">Edge Computing Node</p>
                <p className={cn(
                  'text-sm font-bold',
                  edgeHealth === 'Healthy' ? 'text-signal-green' : 'text-signal-yellow'
                )}>
                  {edgeHealth}
                </p>
              </div>
              <div className="bg-muted rounded p-3">
                <p className="text-[10px] text-muted-foreground mb-1">Database</p>
                <p className="text-sm font-bold text-signal-green">Connected</p>
              </div>
              <div className="bg-muted rounded p-3">
                <p className="text-[10px] text-muted-foreground mb-1">Model Service</p>
                <p className="text-sm font-bold text-signal-green">Running</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Configuration Tab */}
      {adminTab === 'config' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-card border border-border rounded-lg p-4 space-y-3">
              <h3 className="text-xs font-semibold uppercase">System Settings</h3>
              
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-medium">Model Version</label>
                  <span className="text-xs text-muted-foreground">v2.1.4</span>
                </div>
                <select disabled className="w-full bg-muted border border-border rounded px-2 py-1.5 text-xs cursor-not-allowed">
                  <option>v2.1.4 (Current)</option>
                  <option>v2.1.3</option>
                  <option>v2.1.2</option>
                </select>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-medium">Confidence Threshold</label>
                  <span className="text-xs text-muted-foreground">0.50</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  defaultValue="0.5"
                  disabled
                  className="w-full cursor-not-allowed opacity-50"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-medium">Data Retention (days)</label>
                  <span className="text-xs text-muted-foreground">90</span>
                </div>
                <input
                  type="number"
                  disabled
                  defaultValue="90"
                  className="w-full bg-muted border border-border rounded px-2 py-1.5 text-xs cursor-not-allowed"
                />
              </div>
            </div>

            <div className="bg-card border border-border rounded-lg p-4 space-y-3">
              <h3 className="text-xs font-semibold uppercase">Alert Configuration</h3>

              <div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" defaultChecked disabled className="rounded" />
                  <span className="text-xs">Email Alerts on Critical</span>
                </label>
              </div>

              <div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" defaultChecked disabled className="rounded" />
                  <span className="text-xs">SMS Notifications</span>
                </label>
              </div>

              <div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" defaultChecked disabled className="rounded" />
                  <span className="text-xs">Auto-escalation</span>
                </label>
              </div>

              <div>
                <label className="text-xs font-medium block mb-1">Escalation Contacts</label>
                <input
                  type="text"
                  placeholder="ops@company.com"
                  disabled
                  className="w-full bg-muted border border-border rounded px-2 py-1.5 text-xs"
                  value="ops@company.com"
                />
              </div>
            </div>
          </div>

          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
            <p className="text-xs font-semibold mb-2 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-yellow-600" />
              Configuration Note
            </p>
            <p className="text-xs text-muted-foreground">
              Most settings are read-only in this demo. In production, admins can adjust model parameters, thresholds, retention policies, and notification settings.
            </p>
          </div>

          <div className="flex gap-2 justify-between">
            <Button variant="outline" disabled>
              Reset to Defaults
            </Button>
            <Button disabled>
              Apply Changes
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
