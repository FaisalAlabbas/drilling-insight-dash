const { chromium } = require("playwright");
const fs = require("fs");

const DASHBOARD_URL = "http://localhost:8080"; // عدله إذا البورت مختلف
const RESPONSE_TARGET_MS = 1000; // 1 second
const ITERATIONS = 20;
const TIMEOUT_MS = 5000;

const results = [];

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function runCheck(checkNumber) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  let status = "FAIL";
  let reason = "";
  let totalResponseTimeMs = null;
  let httpStatus = null;

  try {
    const start = Date.now();

    const response = await page.goto(DASHBOARD_URL, {
      waitUntil: "domcontentloaded",
      timeout: TIMEOUT_MS,
    });

    httpStatus = response ? response.status() : null;

    if (!response || !response.ok()) {
      reason = `HTTP failure: ${httpStatus ?? "no response"}`;
    } else {
      await Promise.all([
        page
          .locator("text=Surface Dashboard")
          .first()
          .waitFor({ state: "visible", timeout: TIMEOUT_MS }),
        page
          .locator("text=Telemetry")
          .first()
          .waitFor({ state: "visible", timeout: TIMEOUT_MS }),
        page
          .locator("text=AI Recommendation")
          .first()
          .waitFor({ state: "visible", timeout: TIMEOUT_MS }),
        page
          .locator("text=Recent Decisions")
          .first()
          .waitFor({ state: "visible", timeout: TIMEOUT_MS }),
      ]);

      totalResponseTimeMs = Date.now() - start;

      if (totalResponseTimeMs <= RESPONSE_TARGET_MS) {
        status = "PASS";
      } else {
        status = "FAIL";
        reason = `Rendered in ${totalResponseTimeMs} ms, above target ${RESPONSE_TARGET_MS} ms`;
      }
    }
  } catch (err) {
    if (totalResponseTimeMs === null) {
      totalResponseTimeMs = null;
    }
    reason = err.message;
  }

  const screenshotPath =
    status === "FAIL" ? `response-failure-check-${checkNumber}.png` : null;

  if (status === "FAIL") {
    try {
      await page.screenshot({ path: screenshotPath, fullPage: true });
    } catch {}
  }

  await browser.close();

  const record = {
    check: checkNumber,
    timestamp: new Date().toISOString(),
    status,
    httpStatus,
    responseTimeMs: totalResponseTimeMs,
    targetMs: RESPONSE_TARGET_MS,
    withinTarget:
      totalResponseTimeMs !== null ? totalResponseTimeMs <= RESPONSE_TARGET_MS : false,
    reason,
    screenshot: screenshotPath,
  };

  results.push(record);

  console.log(
    `[Check ${checkNumber}] ${record.timestamp} | ${status} | ` +
      `${record.responseTimeMs ?? "-"} ms | HTTP ${record.httpStatus ?? "-"}${reason ? ` | ${reason}` : ""}`
  );
}

async function main() {
  console.log(`Testing dashboard response time for ${DASHBOARD_URL}`);
  console.log(`Target: <= ${RESPONSE_TARGET_MS} ms`);
  console.log(`Iterations: ${ITERATIONS}\n`);

  for (let i = 1; i <= ITERATIONS; i++) {
    await runCheck(i);
    if (i < ITERATIONS) {
      await sleep(2000);
    }
  }

  const measured = results.filter((r) => typeof r.responseTimeMs === "number");
  const passed = results.filter((r) => r.withinTarget).length;
  const failed = results.length - passed;

  const times = measured.map((r) => r.responseTimeMs);
  const avg = times.length ? times.reduce((a, b) => a + b, 0) / times.length : 0;
  const min = times.length ? Math.min(...times) : 0;
  const max = times.length ? Math.max(...times) : 0;

  const sorted = [...times].sort((a, b) => a - b);
  const p95 = sorted.length ? sorted[Math.ceil(0.95 * sorted.length) - 1] : 0;

  const summary = {
    dashboardUrl: DASHBOARD_URL,
    responseTargetMs: RESPONSE_TARGET_MS,
    iterations: ITERATIONS,
    passedChecks: passed,
    failedChecks: failed,
    passRatePercent: Number(((passed / ITERATIONS) * 100).toFixed(2)),
    averageResponseTimeMs: Number(avg.toFixed(2)),
    minResponseTimeMs: Number(min.toFixed(2)),
    maxResponseTimeMs: Number(max.toFixed(2)),
    p95ResponseTimeMs: Number(p95.toFixed(2)),
    requirementMet: failed === 0,
  };

  fs.writeFileSync(
    "dashboard-response-results.json",
    JSON.stringify({ summary, results }, null, 2)
  );

  const csv = [
    "check,timestamp,status,httpStatus,responseTimeMs,targetMs,withinTarget,reason,screenshot",
    ...results.map(
      (r) =>
        `${r.check},${r.timestamp},${r.status},${r.httpStatus ?? ""},${r.responseTimeMs ?? ""},${r.targetMs},${r.withinTarget},"${(r.reason || "").replace(/"/g, '""')}","${r.screenshot || ""}"`
    ),
  ].join("\n");

  fs.writeFileSync("dashboard-response-results.csv", csv);

  console.log("\n=== SUMMARY ===");
  console.log(summary);
  console.log("\nSaved: dashboard-response-results.json, dashboard-response-results.csv");
}

main();
