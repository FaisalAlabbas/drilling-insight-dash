import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AIRecommendationCard } from "./AIRecommendationCard";
import * as DashboardContext from "@/lib/dashboard-context";
import { DecisionRecord } from "@/lib/types";
import type { DashboardContextType } from "@/lib/dashboard-context";

const mockDecision: DecisionRecord = {
  timestamp: "2024-04-07T12:00:00Z",
  model_version: "rf-cal-v1",
  feature_summary: {
    mean_wob: 50,
    std_wob: 5,
    mean_torque: 100,
    std_torque: 10,
    mean_rpm: 150,
    std_rpm: 15,
    mean_vibration: 0.5,
    std_vibration: 0.1,
    trend_inclination: 0.1,
    trend_azimuth: 0.2,
    instability_proxy: 0.3,
  },
  steering_command: "Build" as const,
  confidence_score: 0.85,
  gate_outcome: "ACCEPTED" as const,
  rejection_reason: null,
  execution_status: "SENT",
  fallback_mode: null,
  event_tags: [],
};

describe("AIRecommendationCard", () => {
  beforeEach(() => {
    const mockContext: Partial<DashboardContextType> = {
      decisions: [mockDecision],
      edgeHealth: "Healthy",
      addAlert: vi.fn(),
      telemetry: [],
      alerts: [],
    };
    vi.spyOn(DashboardContext, "useDashboard").mockReturnValue(
      mockContext as DashboardContextType
    );
  });

  it("renders correct styling for ACCEPTED outcome", () => {
    render(<AIRecommendationCard />);
    const gateStatus = screen.getByText("ACCEPTED");
    expect(gateStatus).toBeInTheDocument();
    expect(gateStatus).toHaveClass("text-signal-green");
  });

  it("renders correct styling for REDUCED outcome", () => {
    const mockContext: Partial<DashboardContextType> = {
      decisions: [
        {
          ...mockDecision,
          gate_outcome: "REDUCED" as const,
        },
      ],
      edgeHealth: "Healthy",
      addAlert: vi.fn(),
      telemetry: [],
      alerts: [],
    };
    vi.spyOn(DashboardContext, "useDashboard").mockReturnValue(
      mockContext as DashboardContextType
    );

    render(<AIRecommendationCard />);
    const gateStatus = screen.getByText("REDUCED");
    expect(gateStatus).toBeInTheDocument();
    expect(gateStatus).toHaveClass("text-signal-yellow");
  });

  it("renders correct styling for REJECTED outcome", () => {
    const mockContext: Partial<DashboardContextType> = {
      decisions: [
        {
          ...mockDecision,
          gate_outcome: "REJECTED" as const,
          rejection_reason: "LOW_CONFIDENCE" as const,
        },
      ],
      edgeHealth: "Healthy",
      addAlert: vi.fn(),
      telemetry: [],
      alerts: [],
    };
    vi.spyOn(DashboardContext, "useDashboard").mockReturnValue(
      mockContext as DashboardContextType
    );

    render(<AIRecommendationCard />);
    const gateStatus = screen.getByText("REJECTED");
    expect(gateStatus).toBeInTheDocument();
    expect(gateStatus).toHaveClass("text-signal-red");
  });

  it("displays confidence score with correct formatting", () => {
    render(<AIRecommendationCard />);
    expect(screen.getByText("85% confidence")).toBeInTheDocument();
  });

  it("shows rejection reason when present", () => {
    const mockContext: Partial<DashboardContextType> = {
      decisions: [
        {
          ...mockDecision,
          gate_outcome: "REJECTED" as const,
          rejection_reason: "LOW_CONFIDENCE" as const,
        },
      ],
      edgeHealth: "Healthy",
      addAlert: vi.fn(),
      telemetry: [],
      alerts: [],
    };
    vi.spyOn(DashboardContext, "useDashboard").mockReturnValue(
      mockContext as DashboardContextType
    );

    render(<AIRecommendationCard />);
    expect(screen.getByText("LOW_CONFIDENCE")).toBeInTheDocument();
  });

  it("renders steering command", () => {
    render(<AIRecommendationCard />);
    expect(screen.getByText("Build")).toBeInTheDocument();
  });

  it("returns null when no decisions exist", () => {
    const mockContext: Partial<DashboardContextType> = {
      decisions: [],
      edgeHealth: "Healthy",
      addAlert: vi.fn(),
      telemetry: [],
      alerts: [],
    };
    vi.spyOn(DashboardContext, "useDashboard").mockReturnValue(
      mockContext as DashboardContextType
    );

    const { container } = render(<AIRecommendationCard />);
    expect(container.firstChild).toBeNull();
  });
});
