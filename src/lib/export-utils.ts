import type { TelemetryPacket, DecisionRecord } from "./api-types";

export const exportToCSV = (
  telemetry: TelemetryPacket[],
  decisions: DecisionRecord[],
  filename?: string
) => {
  // Combine telemetry and decisions by timestamp
  const combinedData = telemetry.map((packet) => {
    const decision = decisions.find(
      (d) =>
        Math.abs(new Date(d.timestamp).getTime() - new Date(packet.timestamp).getTime()) <
        1000
    );

    return {
      timestamp: packet.timestamp,
      // Telemetry data
      depth_ft: packet.depth_ft,
      wob_klbf: packet.wob_klbf,
      torque_kftlb: packet.torque_kftlb,
      rpm: packet.rpm,
      vibration_g: packet.vibration_g,
      inclination_deg: packet.inclination_deg,
      azimuth_deg: packet.azimuth_deg,
      rop_ft_hr: packet.rop_ft_hr,
      dls_deg_100ft: packet.dls_deg_100ft,
      gamma_gapi: packet.gamma_gapi,
      resistivity_ohm_m: packet.resistivity_ohm_m,
      // Formation data
      phif: packet.phif,
      vsh: packet.vsh,
      sw: packet.sw,
      klogh: packet.klogh,
      formation_class: packet.formation_class,
      // Decision data
      steering_command: decision?.steering_command || "",
      confidence_score: decision?.confidence_score || "",
      gate_outcome: decision?.gate_outcome || "",
      rejection_reason: decision?.rejection_reason || "",
      execution_status: decision?.execution_status || "",
      fallback_mode: decision?.fallback_mode || "",
      event_tags: decision?.event_tags?.join("; ") || "",
    };
  });

  // Create CSV headers
  const headers = [
    "timestamp",
    "depth_ft",
    "wob_klbf",
    "torque_kftlb",
    "rpm",
    "vibration_g",
    "inclination_deg",
    "azimuth_deg",
    "rop_ft_hr",
    "dls_deg_100ft",
    "gamma_gapi",
    "resistivity_ohm_m",
    "phif",
    "vsh",
    "sw",
    "klogh",
    "formation_class",
    "steering_command",
    "confidence_score",
    "gate_outcome",
    "rejection_reason",
    "execution_status",
    "fallback_mode",
    "event_tags",
  ];

  // Create CSV rows
  const csvContent = [
    headers.join(","),
    ...combinedData.map((row) =>
      headers
        .map((header) => {
          const value = row[header as keyof typeof row];
          // Escape commas and quotes in values
          const stringValue = String(value || "");
          if (
            stringValue.includes(",") ||
            stringValue.includes('"') ||
            stringValue.includes("\n")
          ) {
            return `"${stringValue.replace(/"/g, '""')}"`;
          }
          return stringValue;
        })
        .join(",")
    ),
  ].join("\n");

  // Create and download file
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute(
    "download",
    filename || `drilling-data-${new Date().toISOString().split("T")[0]}.csv`
  );
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};
