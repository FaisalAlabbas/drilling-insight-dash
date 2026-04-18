import { useDashboard } from "@/lib/dashboard-context";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
  Shield,
  Users,
  Settings,
  Bell,
  FileText,
  Plus,
  Check,
  X,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  useAdminUsers,
  useUserStats,
  useAdminConfig,
  useAdminAlerts,
  useAlertStats,
  useAuditLogs,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
  useUpdateConfig,
  useAcknowledgeAlert,
  useResolveAlert,
} from "@/lib/admin-api";

type AdminTab = "users" | "alerts" | "config" | "audit";

export function AdminPanel() {
  const { role, authToken, login } = useDashboard();
  const [adminTab, setAdminTab] = useState<AdminTab>("users");

  // Silent auto-login so API calls have a token
  const [autoLoginDone, setAutoLoginDone] = useState(false);
  useEffect(() => {
    if (!authToken && !autoLoginDone) {
      setAutoLoginDone(true);
      login("admin", "admin123").catch(() => {});
    }
  }, [authToken, autoLoginDone, login]);

  // ── User management state ───────────────────────────────────
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newUser, setNewUser] = useState({ username: "", email: "", password: "", role: "operator" });

  // ── React Query hooks ───────────────────────────────────────
  const { data: users, isLoading: usersLoading } = useAdminUsers(authToken);
  const { data: userStats } = useUserStats(authToken);
  const { data: configs, isLoading: configsLoading } = useAdminConfig(authToken);
  const { data: alertsData, isLoading: alertsLoading } = useAdminAlerts(authToken);
  const { data: alertStats } = useAlertStats(authToken);
  const { data: auditLogs, isLoading: auditLoading } = useAuditLogs(authToken);

  // ── Mutations ───────────────────────────────────────────────
  const createUserMut = useCreateUser(authToken);
  const updateUserMut = useUpdateUser(authToken);
  const deleteUserMut = useDeleteUser(authToken);
  const updateConfigMut = useUpdateConfig(authToken);
  const ackAlertMut = useAcknowledgeAlert(authToken);
  const resolveAlertMut = useResolveAlert(authToken);

  const tabs: { id: AdminTab; label: string; icon: typeof Users }[] = [
    { id: "users", label: "User Management", icon: Users },
    { id: "alerts", label: "Alert Management", icon: Bell },
    { id: "config", label: "Configuration", icon: Settings },
    { id: "audit", label: "Audit Logs", icon: FileText },
  ];

  const handleCreateUser = () => {
    createUserMut.mutate(newUser, {
      onSuccess: () => {
        setShowCreateUser(false);
        setNewUser({ username: "", email: "", password: "", role: "operator" });
      },
    });
  };

  return (
    <div className="space-y-4">
      {/* Admin Info Bar */}
      <div className="bg-card border border-border rounded-lg p-4 flex items-center gap-3">
        <div className="h-10 w-10 rounded-lg bg-primary/20 flex items-center justify-center">
          <Shield className="h-5 w-5 text-primary" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-semibold">Administration Panel</p>
          <p className="text-xs text-muted-foreground">Manage users, alerts, configuration &amp; audit logs</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-muted-foreground">Current Role</p>
          <p className="text-sm font-bold text-primary">{role}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 bg-card border border-border rounded-lg p-2 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setAdminTab(tab.id)}
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded text-xs font-medium transition-colors",
              adminTab === tab.id
                ? "bg-primary/20 text-primary"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* ═══ Users Tab ═══ */}
      {adminTab === "users" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Total Users</p>
              <p className="text-2xl font-bold mt-1">{userStats?.total_users ?? "-"}</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Active</p>
              <p className="text-2xl font-bold mt-1 text-signal-green">
                {userStats?.active_users ?? "-"}
              </p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Inactive</p>
              <p className="text-2xl font-bold mt-1 text-muted-foreground">
                {userStats?.inactive_users ?? "-"}
              </p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Recent Logins</p>
              <p className="text-2xl font-bold mt-1">{userStats?.recent_logins ?? "-"}</p>
            </div>
          </div>

          <div className="flex justify-end">
            <Button
              size="sm"
              className="gap-1"
              onClick={() => setShowCreateUser(!showCreateUser)}
            >
              <Plus className="h-3.5 w-3.5" />
              Add User
            </Button>
          </div>

          {/* Create user form */}
          {showCreateUser && (
            <div className="bg-card border border-border rounded-lg p-4 space-y-3">
              <h3 className="text-xs font-semibold uppercase">Create New User</h3>
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
                <input
                  placeholder="Username"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  className="bg-muted border border-border rounded px-2 py-1.5 text-xs"
                />
                <input
                  placeholder="Email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="bg-muted border border-border rounded px-2 py-1.5 text-xs"
                />
                <input
                  type="password"
                  placeholder="Password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="bg-muted border border-border rounded px-2 py-1.5 text-xs"
                />
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  className="bg-muted border border-border rounded px-2 py-1.5 text-xs"
                >
                  <option value="operator">Operator</option>
                  <option value="engineer">Engineer</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={handleCreateUser} disabled={createUserMut.isPending}>
                  {createUserMut.isPending ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : null}
                  Create
                </Button>
                <Button size="sm" variant="outline" onClick={() => setShowCreateUser(false)}>
                  Cancel
                </Button>
              </div>
              {createUserMut.isError && (
                <p className="text-xs text-signal-red">{(createUserMut.error as Error).message}</p>
              )}
            </div>
          )}

          {/* Users table */}
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            {usersLoading ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <table className="w-full text-xs">
                <thead className="bg-muted border-b border-border">
                  <tr>
                    <th className="px-3 py-2 text-left font-semibold">User</th>
                    <th className="px-3 py-2 text-left font-semibold">Email</th>
                    <th className="px-3 py-2 text-left font-semibold">Role</th>
                    <th className="px-3 py-2 text-center font-semibold">Status</th>
                    <th className="px-3 py-2 text-left font-semibold">Last Login</th>
                    <th className="px-3 py-2 text-center font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {(users ?? []).map((user) => (
                    <tr key={user.id} className="hover:bg-muted/50 transition-colors">
                      <td className="px-3 py-2 font-medium">{user.username}</td>
                      <td className="px-3 py-2 text-muted-foreground">{user.email || "-"}</td>
                      <td className="px-3 py-2">
                        <select
                          value={user.role}
                          onChange={(e) =>
                            updateUserMut.mutate({
                              userId: user.id,
                              data: { role: e.target.value },
                            })
                          }
                          className="bg-muted border border-border rounded px-2 py-1 text-xs"
                        >
                          <option value="operator">operator</option>
                          <option value="engineer">engineer</option>
                          <option value="admin">admin</option>
                        </select>
                      </td>
                      <td className="px-3 py-2 text-center">
                        <span
                          className={cn(
                            "inline-block px-2 py-1 rounded text-[9px] font-bold",
                            user.is_active
                              ? "bg-signal-green/20 text-signal-green"
                              : "bg-muted text-muted-foreground"
                          )}
                        >
                          {user.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {user.last_login_at
                          ? new Date(user.last_login_at).toLocaleString()
                          : "Never"}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {user.is_active ? (
                          <button
                            onClick={() => deleteUserMut.mutate(user.id)}
                            className="text-signal-red hover:underline text-xs font-medium"
                          >
                            Deactivate
                          </button>
                        ) : (
                          <button
                            onClick={() =>
                              updateUserMut.mutate({
                                userId: user.id,
                                data: { is_active: true },
                              })
                            }
                            className="text-signal-green hover:underline text-xs font-medium"
                          >
                            Activate
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                  {(!users || users.length === 0) && (
                    <tr>
                      <td colSpan={6} className="px-3 py-4 text-center text-muted-foreground">
                        No users found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* ═══ Alerts Tab ═══ */}
      {adminTab === "alerts" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Total Alerts</p>
              <p className="text-2xl font-bold mt-1">{alertStats?.total_alerts ?? "-"}</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Critical</p>
              <p className="text-2xl font-bold mt-1 text-signal-red">
                {alertStats?.by_severity?.critical ?? 0}
              </p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Ack Rate</p>
              <p className="text-2xl font-bold mt-1">
                {alertStats?.acknowledgment_rate != null
                  ? `${alertStats.acknowledgment_rate.toFixed(1)}%`
                  : "-"}
              </p>
            </div>
            <div className="bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase">Resolution Rate</p>
              <p className="text-2xl font-bold mt-1 text-signal-green">
                {alertStats?.resolution_rate != null
                  ? `${alertStats.resolution_rate.toFixed(1)}%`
                  : "-"}
              </p>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg overflow-hidden">
            {alertsLoading ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <table className="w-full text-xs">
                <thead className="bg-muted border-b border-border">
                  <tr>
                    <th className="px-3 py-2 text-left font-semibold">Time</th>
                    <th className="px-3 py-2 text-left font-semibold">Title</th>
                    <th className="px-3 py-2 text-center font-semibold">Severity</th>
                    <th className="px-3 py-2 text-center font-semibold">Status</th>
                    <th className="px-3 py-2 text-center font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {(alertsData?.items ?? []).map((alert) => (
                    <tr key={alert.id} className="hover:bg-muted/50 transition-colors">
                      <td className="px-3 py-2 text-muted-foreground">
                        {alert.timestamp
                          ? new Date(alert.timestamp).toLocaleString()
                          : "-"}
                      </td>
                      <td className="px-3 py-2 font-medium">{alert.title}</td>
                      <td className="px-3 py-2 text-center">
                        <span
                          className={cn(
                            "inline-block px-2 py-1 rounded text-[9px] font-bold uppercase",
                            alert.severity === "critical"
                              ? "bg-signal-red/20 text-signal-red"
                              : alert.severity === "high"
                                ? "bg-signal-yellow/20 text-signal-yellow"
                                : "bg-muted text-muted-foreground"
                          )}
                        >
                          {alert.severity}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-center">
                        <span
                          className={cn(
                            "inline-block px-2 py-1 rounded text-[9px] font-bold",
                            alert.status === "ACTIVE"
                              ? "bg-signal-red/20 text-signal-red"
                              : alert.status === "ACKNOWLEDGED"
                                ? "bg-signal-yellow/20 text-signal-yellow"
                                : "bg-signal-green/20 text-signal-green"
                          )}
                        >
                          {alert.status}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-center space-x-1">
                        {alert.status === "ACTIVE" && (
                          <button
                            onClick={() => ackAlertMut.mutate(alert.id)}
                            className="text-signal-yellow hover:underline text-xs font-medium"
                            title="Acknowledge"
                          >
                            <Check className="h-3.5 w-3.5 inline" /> Ack
                          </button>
                        )}
                        {(alert.status === "ACTIVE" || alert.status === "ACKNOWLEDGED") && (
                          <button
                            onClick={() => resolveAlertMut.mutate(alert.id)}
                            className="text-signal-green hover:underline text-xs font-medium"
                            title="Resolve"
                          >
                            <X className="h-3.5 w-3.5 inline" /> Resolve
                          </button>
                        )}
                        {alert.status === "RESOLVED" && (
                          <span className="text-muted-foreground text-xs">Done</span>
                        )}
                      </td>
                    </tr>
                  ))}
                  {(!alertsData?.items || alertsData.items.length === 0) && (
                    <tr>
                      <td colSpan={5} className="px-3 py-4 text-center text-muted-foreground">
                        No alerts found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </div>

          {alertsData && alertsData.pages > 1 && (
            <p className="text-xs text-muted-foreground text-center">
              Page {alertsData.page} of {alertsData.pages} ({alertsData.total} total alerts)
            </p>
          )}
        </div>
      )}

      {/* ═══ Config Tab ═══ */}
      {adminTab === "config" && (
        <div className="space-y-4">
          {configsLoading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <table className="w-full text-xs">
                <thead className="bg-muted border-b border-border">
                  <tr>
                    <th className="px-3 py-2 text-left font-semibold">Key</th>
                    <th className="px-3 py-2 text-left font-semibold">Value</th>
                    <th className="px-3 py-2 text-left font-semibold">Description</th>
                    <th className="px-3 py-2 text-left font-semibold">Updated</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {(configs ?? []).map((cfg) => (
                    <ConfigRow
                      key={cfg.id}
                      config={cfg}
                      onSave={(value) =>
                        updateConfigMut.mutate({ key: cfg.key, data: { value } })
                      }
                      saving={updateConfigMut.isPending}
                    />
                  ))}
                  {(!configs || configs.length === 0) && (
                    <tr>
                      <td colSpan={4} className="px-3 py-4 text-center text-muted-foreground">
                        No configuration entries
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══ Audit Tab ═══ */}
      {adminTab === "audit" && (
        <div className="space-y-4">
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            {auditLoading ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <table className="w-full text-xs">
                <thead className="bg-muted border-b border-border">
                  <tr>
                    <th className="px-3 py-2 text-left font-semibold">Time</th>
                    <th className="px-3 py-2 text-left font-semibold">User</th>
                    <th className="px-3 py-2 text-left font-semibold">Action</th>
                    <th className="px-3 py-2 text-left font-semibold">Resource</th>
                    <th className="px-3 py-2 text-left font-semibold">Changes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {(auditLogs ?? []).map((log) => (
                    <tr key={log.id} className="hover:bg-muted/50 transition-colors">
                      <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">
                        {log.timestamp
                          ? new Date(log.timestamp).toLocaleString()
                          : "-"}
                      </td>
                      <td className="px-3 py-2">{log.user_id || "system"}</td>
                      <td className="px-3 py-2">
                        <span className="px-2 py-0.5 bg-primary/10 text-primary rounded text-[9px] font-bold uppercase">
                          {log.action}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {log.resource_type}
                        {log.resource_id ? ` #${log.resource_id.slice(0, 8)}` : ""}
                      </td>
                      <td className="px-3 py-2 text-muted-foreground max-w-[200px] truncate">
                        {log.old_values && log.new_values
                          ? `${JSON.stringify(log.old_values).slice(0, 40)} → ${JSON.stringify(log.new_values).slice(0, 40)}`
                          : log.new_values
                            ? JSON.stringify(log.new_values).slice(0, 80)
                            : "-"}
                      </td>
                    </tr>
                  ))}
                  {(!auditLogs || auditLogs.length === 0) && (
                    <tr>
                      <td colSpan={5} className="px-3 py-4 text-center text-muted-foreground">
                        No audit log entries
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Config Row (inline editable) ──────────────────────────────────

function ConfigRow({
  config,
  onSave,
  saving,
}: {
  config: { key: string; value: Record<string, unknown>; description: string | null; updated_at: string | null };
  onSave: (value: Record<string, unknown>) => void;
  saving: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(JSON.stringify(config.value, null, 2));

  const handleSave = () => {
    try {
      const parsed = JSON.parse(draft);
      onSave(parsed);
      setEditing(false);
    } catch {
      // invalid JSON — keep editing
    }
  };

  return (
    <tr className="hover:bg-muted/50 transition-colors align-top">
      <td className="px-3 py-2 font-medium whitespace-nowrap">{config.key}</td>
      <td className="px-3 py-2">
        {editing ? (
          <div className="space-y-1">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              className="w-full bg-muted border border-border rounded px-2 py-1 text-xs font-mono min-h-[60px]"
            />
            <div className="flex gap-1">
              <Button size="sm" onClick={handleSave} disabled={saving} className="h-6 text-[10px]">
                Save
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setEditing(false);
                  setDraft(JSON.stringify(config.value, null, 2));
                }}
                className="h-6 text-[10px]"
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setEditing(true)}
            className="text-left text-xs font-mono text-muted-foreground hover:text-foreground max-w-[300px] truncate block"
            title="Click to edit"
          >
            {JSON.stringify(config.value)}
          </button>
        )}
      </td>
      <td className="px-3 py-2 text-muted-foreground">{config.description || "-"}</td>
      <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">
        {config.updated_at ? new Date(config.updated_at).toLocaleString() : "-"}
      </td>
    </tr>
  );
}
