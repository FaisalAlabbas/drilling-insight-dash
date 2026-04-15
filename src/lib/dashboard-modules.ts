/**
 * Dashboard Modules Configuration
 * Central configuration for all dashboard modules, permissions, and routing
 */

export type UserRole = "operator" | "engineer" | "admin";

export type ModuleId =
  | "live-monitoring"
  | "alerts"
  | "history"
  | "data-quality"
  | "reporting"
  | "ai-evaluation"
  | "admin-panel"
  | "telemetry-chart"
  | "ai-recommendation";

export interface ModuleConfig {
  id: ModuleId;
  name: string;
  description: string;
  icon: string;
  path: string;
  requiredRole: UserRole;
  category: "monitoring" | "analysis" | "management" | "ai";
  enabled: boolean;
  order: number;
}

export interface RouteConfig {
  path: string;
  moduleId: ModuleId;
  component: string;
  exact?: boolean;
  requiresAuth: boolean;
  requiredRole: UserRole;
}

// Module configurations with permissions
export const DASHBOARD_MODULES: Record<ModuleId, ModuleConfig> = {
  "live-monitoring": {
    id: "live-monitoring",
    name: "Live Monitoring",
    description: "Real-time telemetry monitoring and AI recommendations",
    icon: "Activity",
    path: "/",
    requiredRole: "operator",
    category: "monitoring",
    enabled: true,
    order: 1,
  },
  "telemetry-chart": {
    id: "telemetry-chart",
    name: "Telemetry Chart",
    description: "Advanced telemetry visualization with multi-signal overlay",
    icon: "BarChart3",
    path: "/chart",
    requiredRole: "operator",
    category: "monitoring",
    enabled: true,
    order: 2,
  },
  "ai-recommendation": {
    id: "ai-recommendation",
    name: "AI Recommendations",
    description: "AI-powered steering recommendations and decision support",
    icon: "Brain",
    path: "/ai",
    requiredRole: "operator",
    category: "ai",
    enabled: true,
    order: 3,
  },
  alerts: {
    id: "alerts",
    name: "Alerts",
    description: "Alert management and incident tracking",
    icon: "AlertTriangle",
    path: "/alerts",
    requiredRole: "operator",
    category: "monitoring",
    enabled: true,
    order: 4,
  },
  history: {
    id: "history",
    name: "History",
    description: "Historical data search and export",
    icon: "History",
    path: "/history",
    requiredRole: "engineer",
    category: "analysis",
    enabled: true,
    order: 5,
  },
  "data-quality": {
    id: "data-quality",
    name: "Data Quality",
    description: "Data quality monitoring and validation",
    icon: "CheckCircle",
    path: "/data-quality",
    requiredRole: "engineer",
    category: "analysis",
    enabled: true,
    order: 6,
  },
  reporting: {
    id: "reporting",
    name: "Reporting",
    description: "Automated reports and analytics",
    icon: "FileText",
    path: "/reporting",
    requiredRole: "engineer",
    category: "analysis",
    enabled: true,
    order: 7,
  },
  "ai-evaluation": {
    id: "ai-evaluation",
    name: "AI Evaluation",
    description: "AI model performance evaluation and metrics",
    icon: "TrendingUp",
    path: "/ai-evaluation",
    requiredRole: "engineer",
    category: "ai",
    enabled: true,
    order: 8,
  },
  "admin-panel": {
    id: "admin-panel",
    name: "Admin Panel",
    description: "System administration and configuration",
    icon: "Settings",
    path: "/admin",
    requiredRole: "admin",
    category: "management",
    enabled: true,
    order: 9,
  },
};

// Route configurations
export const DASHBOARD_ROUTES: RouteConfig[] = [
  {
    path: "/",
    moduleId: "live-monitoring",
    component: "Index",
    exact: true,
    requiresAuth: true,
    requiredRole: "operator",
  },
  {
    path: "/chart",
    moduleId: "telemetry-chart",
    component: "TelemetryChart",
    requiresAuth: true,
    requiredRole: "operator",
  },
  {
    path: "/ai",
    moduleId: "ai-recommendation",
    component: "AIRecommendation",
    requiresAuth: true,
    requiredRole: "operator",
  },
  {
    path: "/alerts",
    moduleId: "alerts",
    component: "AlertsView",
    requiresAuth: true,
    requiredRole: "operator",
  },
  {
    path: "/history",
    moduleId: "history",
    component: "History",
    requiresAuth: true,
    requiredRole: "engineer",
  },
  {
    path: "/data-quality",
    moduleId: "data-quality",
    component: "DataQuality",
    requiresAuth: true,
    requiredRole: "engineer",
  },
  {
    path: "/reporting",
    moduleId: "reporting",
    component: "Reporting",
    requiresAuth: true,
    requiredRole: "engineer",
  },
  {
    path: "/ai-evaluation",
    moduleId: "ai-evaluation",
    component: "AIEvaluation",
    requiresAuth: true,
    requiredRole: "engineer",
  },
  {
    path: "/admin",
    moduleId: "admin-panel",
    component: "AdminPanel",
    requiresAuth: true,
    requiredRole: "admin",
  },
];

// Permission utilities
export function hasAccess(userRole: UserRole, requiredRole: UserRole): boolean {
  const roleHierarchy: Record<UserRole, number> = {
    operator: 1,
    engineer: 2,
    admin: 3,
  };

  return roleHierarchy[userRole] >= roleHierarchy[requiredRole];
}

export function getAccessibleModules(userRole: UserRole): ModuleConfig[] {
  return Object.values(DASHBOARD_MODULES)
    .filter((module) => module.enabled && hasAccess(userRole, module.requiredRole))
    .sort((a, b) => a.order - b.order);
}

export function getModuleById(id: ModuleId): ModuleConfig | undefined {
  return DASHBOARD_MODULES[id];
}

export function getRouteByPath(path: string): RouteConfig | undefined {
  return DASHBOARD_ROUTES.find((route) => route.path === path);
}

// Navigation helpers
export function getNavigationItems(userRole: UserRole) {
  const accessibleModules = getAccessibleModules(userRole);

  // Group by category
  const categories = {
    monitoring: accessibleModules.filter((m) => m.category === "monitoring"),
    analysis: accessibleModules.filter((m) => m.category === "analysis"),
    ai: accessibleModules.filter((m) => m.category === "ai"),
    management: accessibleModules.filter((m) => m.category === "management"),
  };

  return categories;
}
