const axios = require("axios");
const fs = require("fs");

const url = "http://localhost:8080";
const checks = 20;
const interval = 5000;

let success = 0;
let fail = 0;
let results = [];

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function checkAvailability(i) {
  const start = Date.now();

  try {
    const response = await axios.get(url, { timeout: 4000 });
    const responseTime = Date.now() - start;

    if (response.status === 200) {
      console.log(`Check ${i}: UP (${responseTime} ms)`);
      success++;
      results.push({
        check: i,
        status: "UP",
        responseTime: responseTime,
        timestamp: new Date().toISOString(),
      });
    } else {
      console.log(`Check ${i}: DOWN`);
      fail++;
      results.push({
        check: i,
        status: "DOWN",
        responseTime: responseTime,
        timestamp: new Date().toISOString(),
      });
    }
  } catch (error) {
    const responseTime = Date.now() - start;
    console.log(`Check ${i}: DOWN`);
    fail++;
    results.push({
      check: i,
      status: "DOWN",
      responseTime: responseTime,
      timestamp: new Date().toISOString(),
      error: error.message,
    });
  }
}

async function runTest() {
  console.log("Starting availability test...\n");

  for (let i = 1; i <= checks; i++) {
    await checkAvailability(i);

    if (i < checks) {
      await sleep(interval);
    }
  }

  const availability = (success / checks) * 100;
  const avgResponseTime =
    results.filter((r) => r.status === "UP").reduce((sum, r) => sum + r.responseTime, 0) /
    (success || 1);

  console.log("\n--- Results ---");
  console.log(`Successful checks: ${success}`);
  console.log(`Failed checks: ${fail}`);
  console.log(`Availability: ${availability.toFixed(2)}%`);
  console.log(`Average response time: ${avgResponseTime.toFixed(2)} ms`);

  const summary = {
    totalChecks: checks,
    successfulChecks: success,
    failedChecks: fail,
    availability: `${availability.toFixed(2)}%`,
    averageResponseTime: `${avgResponseTime.toFixed(2)} ms`,
  };

  fs.writeFileSync(
    "availability-results.json",
    JSON.stringify({ summary, results }, null, 2)
  );

  console.log("\nSaved results to availability-results.json");
}

runTest();
