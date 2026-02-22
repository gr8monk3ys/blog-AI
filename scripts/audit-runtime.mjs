#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";

const ALLOWED_ADVISORY_IDS = new Set(["GHSA-3PPC-4F35-3M26"]);
const BLOCKING_SEVERITIES = new Set(["high", "critical"]);

function extractAdvisoryId(value) {
  if (!value || typeof value !== "string") return null;
  const match = value.match(/GHSA-[\w-]+/i);
  return match ? match[0].toUpperCase() : null;
}

function parseAuditOutput(stdout) {
  const raw = String(stdout || "");
  const jsonStart = raw.indexOf("{");
  if (jsonStart === -1) {
    throw new Error("npm audit did not return JSON output.");
  }

  return JSON.parse(raw.slice(jsonStart));
}

function collectAdvisoryIds(name, vulnerabilities, visited = new Set()) {
  if (visited.has(name)) return new Set();
  visited.add(name);

  const vulnerability = vulnerabilities[name];
  if (!vulnerability || !Array.isArray(vulnerability.via)) return new Set();

  const advisories = new Set();
  for (const via of vulnerability.via) {
    if (typeof via === "string") {
      for (const advisoryId of collectAdvisoryIds(via, vulnerabilities, visited)) {
        advisories.add(advisoryId);
      }
      continue;
    }

    const advisoryId = extractAdvisoryId(via?.url) || extractAdvisoryId(via?.title);
    if (advisoryId) advisories.add(advisoryId);
  }

  return advisories;
}

let report;
try {
  if (process.env.NPM_AUDIT_JSON_PATH) {
    report = JSON.parse(readFileSync(process.env.NPM_AUDIT_JSON_PATH, "utf8"));
  } else {
    const audit = spawnSync("npm", ["audit", "--omit=dev", "--json"], {
      encoding: "utf8",
    });
    report = parseAuditOutput(audit.stdout);
  }
} catch (error) {
  console.error("Unable to parse npm audit output.");
  console.error(error.message);
  process.exit(1);
}

if (report.error) {
  console.error("npm audit returned an error:");
  console.error(report.error.summary || report.error.detail || JSON.stringify(report.error));
  process.exit(1);
}

const vulnerabilities = report.vulnerabilities || {};
const blocking = [];
const tolerated = [];

for (const [name, vulnerability] of Object.entries(vulnerabilities)) {
  const severity = String(vulnerability?.severity || "").toLowerCase();
  if (!BLOCKING_SEVERITIES.has(severity)) continue;

  const advisoryIds = [...collectAdvisoryIds(name, vulnerabilities)];
  if (advisoryIds.length === 0) {
    blocking.push({
      name,
      severity,
      reason: "No advisory ID found for allowlist evaluation.",
    });
    continue;
  }

  const disallowedAdvisories = advisoryIds.filter((id) => !ALLOWED_ADVISORY_IDS.has(id));
  if (disallowedAdvisories.length > 0) {
    blocking.push({
      name,
      severity,
      reason: `Contains non-allowlisted advisories: ${disallowedAdvisories.join(", ")}`,
    });
    continue;
  }

  tolerated.push({
    name,
    severity,
    advisoryIds,
  });
}

if (blocking.length > 0) {
  console.error("Blocking runtime vulnerabilities detected:");
  for (const issue of blocking) {
    console.error(`- ${issue.name} (${issue.severity}): ${issue.reason}`);
  }
  process.exit(1);
}

if (tolerated.length > 0) {
  console.warn("Temporarily tolerated runtime vulnerabilities (upstream fix pending):");
  for (const issue of tolerated) {
    console.warn(`- ${issue.name} (${issue.severity}): ${issue.advisoryIds.join(", ")}`);
  }
}

console.log("Runtime dependency audit passed policy checks.");
