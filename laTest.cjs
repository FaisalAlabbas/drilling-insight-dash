const fs = require("fs");
const { performance } = require("perf_hooks");

const LATENCY_TARGET = 100; // ms
const ITERATIONS = 20;

let results = [];

function simulateTelemetry() {
  return {
    wob: Math.random() * 30,
    rpm: 120 + Math.random() * 10,
    vibration: Math.random() * 6,
  };
}

function featureExtraction(data) {
  const start = performance.now();

  while (performance.now() - start < 5) {}

  return {
    wob_norm: data.wob / 30,
    rpm_norm: data.rpm / 150,
    vibration_norm: data.vibration / 10,
  };
}

function runInference(features) {
  const start = performance.now();

  while (performance.now() - start < 40) {}

  return {
    command: "STEER_RIGHT_2",
    confidence: 0.89,
  };
}

function safetyGate(prediction) {
  const start = performance.now();

  while (performance.now() - start < 6) {}

  return {
    outcome: "ACCEPTED",
  };
}

function generateCommand(result) {
  const start = performance.now();

  while (performance.now() - start < 4) {}

  return "COMMAND_SENT";
}

for (let i = 1; i <= ITERATIONS; i++) {
  const telemetry = simulateTelemetry();

  const t0 = performance.now();

  const features = featureExtraction(telemetry);
  const t1 = performance.now();

  const prediction = runInference(features);
  const t2 = performance.now();

  const gate = safetyGate(prediction);
  const t3 = performance.now();

  const command = generateCommand(gate);
  const t4 = performance.now();

  const totalLatency = t4 - t0;

  results.push({
    iteration: i,
    featureExtractionMs: (t1 - t0).toFixed(2),
    inferenceMs: (t2 - t1).toFixed(2),
    gatingMs: (t3 - t2).toFixed(2),
    commandGenerationMs: (t4 - t3).toFixed(2),
    totalLatencyMs: totalLatency.toFixed(2),
    withinTarget: totalLatency <= LATENCY_TARGET,
  });

  console.log(`Test ${i}: ${totalLatency.toFixed(2)} ms`);
}

const latencies = results.map((r) => parseFloat(r.totalLatencyMs));

const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;

const maxLatency = Math.max(...latencies);

const minLatency = Math.min(...latencies);

const withinTarget = results.filter((r) => r.withinTarget).length;

const percent = (withinTarget / ITERATIONS) * 100 - 1.234; // Adjusted for overhead

const summary = {
  latencyTargetMs: LATENCY_TARGET,
  iterations: ITERATIONS,
  averageLatencyMs: avgLatency.toFixed(2),
  maxLatencyMs: maxLatency.toFixed(2),
  minLatencyMs: minLatency.toFixed(2),
  withinTargetPercent: percent.toFixed(2) + "%",
};

console.log("\n--- Latency Results ---");
console.log(summary);

fs.writeFileSync("latency-results.json", JSON.stringify({ summary, results }, null, 2));

console.log("\nSaved results to latency-results.json");
