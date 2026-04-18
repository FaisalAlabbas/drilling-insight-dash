/**
 * Admin API service — types, fetch functions, and React Query hooks
 * for user management, config, alerts, and audit logs.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { API_BASE_URL } from "./config";

// ─── Types ────────────────────────────────────────────────────────

export interface AdminUser {
  id: string;
  username: string;
  email: string | null;
  role: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string | null;
}

export interface UserStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  users_by_role: Record<string, number>;
  recent_logins: number;
}

export interface AdminConfigEntry {
  id: string;
  key: string;
  value: Record<string, unknown>;
  description: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ConfigHistoryEntry {
  id: string;
  timestamp: string | null;
  user_id: string | null;
  action: string;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
}

export interface AdminAlert {
  id: string;
  timestamp: string | null;
  severity: string;
  status: string;
  title: string;
  message: string | null;
  well_id: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
}

export interface AlertsResponse {
  items: AdminAlert[];
  total: number;
  page: number;
  pages: number;
}

export interface AlertStats {
  total_alerts: number;
  by_status: Record<string, number>;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
  acknowledgment_rate: number;
  resolution_rate: number;
  time_range_days?: number;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string | null;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
}

// ─── Helpers ──────────────────────────────────────────────────────

function getAuthHeaders(token: string | null): HeadersInit {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function adminFetch<T>(
  endpoint: string,
  token: string | null,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: getAuthHeaders(token),
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.statusText}`);
  }
  return res.json();
}

// ─── User API ─────────────────────────────────────────────────────

export const fetchAdminUsers = (token: string | null) =>
  adminFetch<AdminUser[]>("/admin/users", token);

export const fetchUserStats = (token: string | null) =>
  adminFetch<UserStats>("/admin/users/stats", token);

export const createUser = (
  token: string | null,
  data: { username: string; email?: string; password: string; role: string }
) =>
  adminFetch<AdminUser>("/admin/users", token, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateUser = (
  token: string | null,
  userId: string,
  data: { email?: string; role?: string; is_active?: boolean; password?: string }
) =>
  adminFetch<AdminUser>(`/admin/users/${userId}`, token, {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const deleteUser = (token: string | null, userId: string) =>
  adminFetch<{ message: string }>(`/admin/users/${userId}`, token, {
    method: "DELETE",
  });

// ─── Config API ───────────────────────────────────────────────────

export const fetchAdminConfig = (token: string | null) =>
  adminFetch<AdminConfigEntry[]>("/admin/config", token);

export const updateConfig = (
  token: string | null,
  key: string,
  data: { value: Record<string, unknown>; description?: string }
) =>
  adminFetch<AdminConfigEntry>(`/admin/config/${key}`, token, {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const fetchConfigHistory = (token: string | null, key: string) =>
  adminFetch<ConfigHistoryEntry[]>(`/admin/config/history/${key}`, token);

// ─── Alert API ────────────────────────────────────────────────────

export const fetchAdminAlerts = (
  token: string | null,
  params?: { severity?: string; status?: string; page?: number }
) => {
  const qs = new URLSearchParams();
  if (params?.severity) qs.set("severity", params.severity);
  if (params?.status) qs.set("alert_status", params.status);
  if (params?.page) qs.set("page", String(params.page));
  const query = qs.toString();
  return adminFetch<AlertsResponse>(`/admin/alerts${query ? `?${query}` : ""}`, token);
};

export const acknowledgeAlert = (token: string | null, alertId: string) =>
  adminFetch<{ message: string }>(`/admin/alerts/${alertId}/acknowledge`, token, {
    method: "PUT",
  });

export const resolveAlert = (token: string | null, alertId: string) =>
  adminFetch<{ message: string }>(`/admin/alerts/${alertId}/resolve`, token, {
    method: "PUT",
  });

export const fetchAlertStats = (token: string | null) =>
  adminFetch<AlertStats>("/admin/alerts/stats", token);

// ─── Audit API ────────────────────────────────────────────────────

export const fetchAuditLogs = (token: string | null, limit = 100) =>
  adminFetch<AuditLogEntry[]>(`/admin/audit-logs?limit=${limit}`, token);

// ─── React Query Hooks ────────────────────────────────────────────

export function useAdminUsers(token: string | null) {
  return useQuery({
    queryKey: ["admin-users"],
    queryFn: () => fetchAdminUsers(token),
    enabled: !!token,
    refetchInterval: 30000,
  });
}

export function useUserStats(token: string | null) {
  return useQuery({
    queryKey: ["admin-user-stats"],
    queryFn: () => fetchUserStats(token),
    enabled: !!token,
    refetchInterval: 30000,
  });
}

export function useAdminConfig(token: string | null) {
  return useQuery({
    queryKey: ["admin-config"],
    queryFn: () => fetchAdminConfig(token),
    enabled: !!token,
    refetchInterval: 60000,
  });
}

export function useAdminAlerts(
  token: string | null,
  params?: { severity?: string; status?: string; page?: number }
) {
  return useQuery({
    queryKey: ["admin-alerts", params],
    queryFn: () => fetchAdminAlerts(token, params),
    enabled: !!token,
    refetchInterval: 15000,
  });
}

export function useAlertStats(token: string | null) {
  return useQuery({
    queryKey: ["admin-alert-stats"],
    queryFn: () => fetchAlertStats(token),
    enabled: !!token,
    refetchInterval: 30000,
  });
}

export function useAuditLogs(token: string | null) {
  return useQuery({
    queryKey: ["admin-audit-logs"],
    queryFn: () => fetchAuditLogs(token),
    enabled: !!token,
    refetchInterval: 30000,
  });
}

// ─── Mutation Hooks ───────────────────────────────────────────────

export function useCreateUser(token: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { username: string; email?: string; password: string; role: string }) =>
      createUser(token, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-users"] });
      qc.invalidateQueries({ queryKey: ["admin-user-stats"] });
    },
  });
}

export function useUpdateUser(token: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: { email?: string; role?: string; is_active?: boolean } }) =>
      updateUser(token, userId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-users"] });
      qc.invalidateQueries({ queryKey: ["admin-user-stats"] });
    },
  });
}

export function useDeleteUser(token: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => deleteUser(token, userId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-users"] });
      qc.invalidateQueries({ queryKey: ["admin-user-stats"] });
    },
  });
}

export function useUpdateConfig(token: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ key, data }: { key: string; data: { value: Record<string, unknown> } }) =>
      updateConfig(token, key, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-config"] });
    },
  });
}

export function useAcknowledgeAlert(token: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (alertId: string) => acknowledgeAlert(token, alertId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-alerts"] });
      qc.invalidateQueries({ queryKey: ["admin-alert-stats"] });
    },
  });
}

export function useResolveAlert(token: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (alertId: string) => resolveAlert(token, alertId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-alerts"] });
      qc.invalidateQueries({ queryKey: ["admin-alert-stats"] });
    },
  });
}
