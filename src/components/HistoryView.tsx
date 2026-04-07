import { useDashboard } from "@/lib/dashboard-context";
import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { Search, Download, Filter, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { DecisionRecord } from "@/lib/types";

export function HistoryView() {
  const {
    decisions,
    telemetry,
    setSelectedDecision,
    setDrawerOpen,
    searchQuery,
    setSearchQuery,
  } = useDashboard();
  const [sortBy, setSortBy] = useState<"newest" | "oldest" | "confidence">("newest");
  const [filterCommand, setFilterCommand] = useState<string>("ALL");
  const [filterOutcome, setFilterOutcome] = useState<string>("ALL");

  const filteredDecisions = useMemo(() => {
    let filtered = [...decisions];

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (d) =>
          d.steering_command.toLowerCase().includes(searchQuery.toLowerCase()) ||
          new Date(d.timestamp).toLocaleString().includes(searchQuery)
      );
    }

    // Command filter
    if (filterCommand !== "ALL") {
      filtered = filtered.filter((d) => d.steering_command === filterCommand);
    }

    // Outcome filter
    if (filterOutcome !== "ALL") {
      filtered = filtered.filter((d) => d.gate_outcome === filterOutcome);
    }

    // Sort
    filtered.sort((a, b) => {
      const timeA = new Date(a.timestamp).getTime();
      const timeB = new Date(b.timestamp).getTime();
      if (sortBy === "newest") return timeB - timeA;
      if (sortBy === "oldest") return timeA - timeB;
      return b.confidence_score - a.confidence_score;
    });

    return filtered;
  }, [decisions, searchQuery, filterCommand, filterOutcome, sortBy]);

  const commands = Array.from(new Set(decisions.map((d) => d.steering_command)));
  const avgConfidence =
    decisions.length > 0
      ? (
          (decisions.reduce((sum, d) => sum + d.confidence_score, 0) / decisions.length) *
          100
        ).toFixed(1)
      : "0";
  const acceptRate =
    decisions.length > 0
      ? (
          (decisions.filter((d) => d.gate_outcome === "ACCEPTED").length /
            decisions.length) *
          100
        ).toFixed(1)
      : "0";

  const exportCSV = () => {
    const headers = [
      "Timestamp",
      "Steering Command",
      "Confidence",
      "Gate Outcome",
      "Execution Status",
      "Rejection Reason",
    ];
    const rows = filteredDecisions.map((d) => [
      new Date(d.timestamp).toLocaleString(),
      d.steering_command,
      (d.confidence_score * 100).toFixed(1) + "%",
      d.gate_outcome,
      d.execution_status,
      d.rejection_reason || "N/A",
    ]);

    const csv = [headers, ...rows]
      .map((row) => row.map((cell) => `"${cell}"`).join(","))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `drilling-decisions-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
  };

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-card border border-border rounded-lg p-3">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
            Total Decisions
          </p>
          <p className="text-2xl font-bold mt-1">{decisions.length}</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-3">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
            Avg Confidence
          </p>
          <p className="text-2xl font-bold mt-1">{avgConfidence}%</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-3">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
            Accept Rate
          </p>
          <p className="text-2xl font-bold mt-1">{acceptRate}%</p>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-card border border-border rounded-lg p-3 space-y-3">
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex-1 min-w-[200px] relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search decisions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-muted border border-border rounded px-3 py-2 pl-8 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <select
            value={filterCommand}
            onChange={(e) => setFilterCommand(e.target.value)}
            className="bg-muted border border-border rounded px-2 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
          >
            <option value="ALL">All Commands</option>
            {commands.map((cmd) => (
              <option key={cmd} value={cmd}>
                {cmd}
              </option>
            ))}
          </select>

          <select
            value={filterOutcome}
            onChange={(e) => setFilterOutcome(e.target.value)}
            className="bg-muted border border-border rounded px-2 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
          >
            <option value="ALL">All Outcomes</option>
            <option value="ACCEPTED">Accepted</option>
            <option value="REJECTED">Rejected</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as "newest" | "oldest" | "confidence")}
            className="bg-muted border border-border rounded px-2 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="confidence">Highest Confidence</option>
          </select>

          <Button onClick={exportCSV} size="sm" variant="outline" className="gap-2">
            <Download className="h-3.5 w-3.5" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-muted border-b border-border">
              <tr>
                <th className="px-3 py-2 text-left font-semibold">Timestamp</th>
                <th className="px-3 py-2 text-left font-semibold">Command</th>
                <th className="px-3 py-2 text-center font-semibold">Confidence</th>
                <th className="px-3 py-2 text-center font-semibold">Gate</th>
                <th className="px-3 py-2 text-center font-semibold">Status</th>
                <th className="px-3 py-2 text-left font-semibold">Rejection</th>
                <th className="px-3 py-2 text-center font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredDecisions.slice(0, 50).map((decision) => (
                <tr
                  key={decision.timestamp}
                  className="hover:bg-muted/50 transition-colors"
                >
                  <td className="px-3 py-2 font-mono text-muted-foreground">
                    {new Date(decision.timestamp).toLocaleTimeString("en-US", {
                      hour12: false,
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    })}
                  </td>
                  <td className="px-3 py-2 font-medium">{decision.steering_command}</td>
                  <td className="px-3 py-2 text-center">
                    <span
                      className={cn(
                        "inline-block px-2 py-1 rounded text-[9px] font-bold",
                        decision.confidence_score >= 0.7
                          ? "bg-signal-green/20 text-signal-green"
                          : decision.confidence_score >= 0.5
                            ? "bg-signal-yellow/20 text-signal-yellow"
                            : "bg-signal-red/20 text-signal-red"
                      )}
                    >
                      {(decision.confidence_score * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-3 py-2 text-center">
                    <span
                      className={cn(
                        "inline-block px-2 py-1 rounded text-[9px] font-bold",
                        decision.gate_outcome === "ACCEPTED"
                          ? "bg-signal-green/20 text-signal-green"
                          : "bg-signal-red/20 text-signal-red"
                      )}
                    >
                      {decision.gate_outcome}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-center">
                    <span
                      className={cn(
                        "inline-block px-2 py-1 rounded text-[9px] font-bold",
                        decision.execution_status === "SENT"
                          ? "bg-signal-green/20 text-signal-green"
                          : "bg-signal-red/20 text-signal-red"
                      )}
                    >
                      {decision.execution_status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">
                    {decision.rejection_reason || "-"}
                  </td>
                  <td className="px-3 py-2 text-center">
                    <button
                      onClick={() => {
                        setSelectedDecision(decision);
                        setDrawerOpen(true);
                      }}
                      className="text-primary hover:underline text-xs font-medium"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredDecisions.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">No decisions found matching your filters</p>
          </div>
        )}
        {filteredDecisions.length > 50 && (
          <div className="bg-muted border-t border-border px-3 py-2 text-center text-xs text-muted-foreground">
            Showing 50 of {filteredDecisions.length} records
          </div>
        )}
      </div>
    </div>
  );
}
