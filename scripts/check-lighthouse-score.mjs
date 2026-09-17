import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

// Lighthouse score floors for the public marketing routes, run against a
// production build (`next build && next start`) in CI.
//
// Desktop preset on purpose: mobile devtools throttling on shared GitHub
// runners swings 10+ points between identical runs, which makes any floor
// either flaky or meaningless. Production MOBILE numbers are measured
// separately against https://blog-ai.vivancedata.com (PageSpeed Insights /
// the Lighthouse program notes); this check guards the desktop score of the
// build itself so the 2026-09-13..16 Lighthouse work cannot silently regress.
//
// Per-category floors rather than a blanket 100. Re-measured 2026-09-16 over
// three local runs of the production build (desktop preset), per route:
//   /         perf 100  a11y 100  bp 96  seo 100
//   /pricing  perf  98  a11y 100  bp 96  seo 100
//   /blog     perf 100  a11y 100  bp 96  seo 100
//   /tools    perf 100  a11y 100  bp 96  seo 100
// Performance sits 2 below the observed minimum; the others sit at it.
// Accessibility is a flat 100: the two defects that forced it down to 96 are
// fixed (the /pricing "Save 17%" badge was white on emerald-500, 2.54:1, now
// emerald-700 at 5.48:1; the /tools cards jumped h1 -> h3, and ToolGrid now
// takes a headingLevel). Every route in the list clears 100 on every run, so
// there is no per-route exception left to carve out.
// Best-practices is 96 rather than the 100 production scores because off
// Vercel the @vercel/analytics and @vercel/speed-insights loaders 404 on
// /_vercel/*, which trips errors-in-console. That is an artifact of the CI
// host, not of the code, and it is constant, so 96 still catches a real
// regression. A floor that fails on noise gets bypassed and a bypassed check
// is no check; a genuine regression lands well below the floor. Raise a floor
// whenever the real score improves.
const SCORE_FLOORS = {
  performance: 96,
  accessibility: 100,
  bestPractices: 96,
  seo: 100,
};

// Document byte budget for the home route (gzip-compressed HTML, in bytes).
// `experimental.inlineCss` moved the stylesheet into the document, so the
// response grew from a few KB to tens of KB and it now sits on the critical
// path of every first paint. Measured 2026-09-16: 57,366-57,379 bytes; the
// cap is ~25% above that. The
// measured number is printed on every run so drift is visible before it
// bites. Raise it deliberately, with the reason in the commit message.
const HOME_DOCUMENT_BYTE_CAP = 72_000;

const MAX_ATTEMPTS = 4;
const artifactDir = join(process.cwd(), "artifacts", "lighthouse");
const [baseUrl, ...routes] = process.argv.slice(2);

if (!baseUrl || routes.length === 0) {
  console.error("Usage: node scripts/check-lighthouse-score.mjs <baseUrl> <route...>");
  process.exit(1);
}

const outputDir = mkdtempSync(join(tmpdir(), "blog-ai-lighthouse-"));

try {
  mkdirSync(artifactDir, { recursive: true });

  for (const route of routes) {
    const url = new URL(route, baseUrl).toString();
    warmRoute(url);
    let bestAttempt = null;
    let attemptsRun = 0;

    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
      attemptsRun = attempt;
      const reportPath = join(outputDir, `${artifactSlug(route)}-attempt-${attempt}.json`);
      const scores = runLighthouse(url, reportPath);

      console.log(`[lighthouse] ${route} attempt ${attempt} -> ${JSON.stringify(scores)}`);

      if (!bestAttempt || totalScore(scores) > totalScore(bestAttempt.scores)) {
        bestAttempt = { attempt, scores, reportPath };
      }

      if (Object.entries(scores).every(([k, score]) => score >= (SCORE_FLOORS[k] ?? 100))) {
        break;
      }
    }

    const failures = Object.entries(bestAttempt.scores).filter(([k, score]) => score < (SCORE_FLOORS[k] ?? 100));
    copyFileSync(bestAttempt.reportPath, join(artifactDir, `${artifactSlug(route)}.json`));

    if (failures.length > 0) {
      console.error(
        `[lighthouse] ${route} fell below its score floors after ${attemptsRun} attempt(s): ${failures
          .map(([category, score]) => `${category}=${score}`)
          .join(", ")}`
      );
      logFailureDiagnostics(bestAttempt.reportPath);
      process.exit(1);
    }
  }

  checkDocumentByteBudget(new URL("/", baseUrl).toString());
} finally {
  rmSync(outputDir, { recursive: true, force: true });
}

function artifactSlug(route) {
  return route === "/" ? "root" : route.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "");
}

function runLighthouse(url, reportPath) {
  const result = spawnSync(
    "npx",
    [
      "-y",
      "lighthouse",
      url,
      "--preset=desktop",
      "--quiet",
      "--chrome-flags=--headless=new --no-sandbox",
      "--only-categories=performance,accessibility,best-practices,seo",
      "--output=json",
      `--output-path=${reportPath}`,
    ],
    { encoding: "utf-8" }
  );

  if (result.error) {
    console.error(`Failed to run Lighthouse for ${url}:`, result.error.message);
    process.exit(1);
  }

  if (result.status !== 0) {
    if (result.stdout) process.stdout.write(result.stdout);
    if (result.stderr) process.stderr.write(result.stderr);
    process.exit(result.status ?? 1);
  }

  const report = JSON.parse(readFileSync(reportPath, "utf-8"));
  return {
    performance: Math.round(report.categories.performance.score * 100),
    accessibility: Math.round(report.categories.accessibility.score * 100),
    bestPractices: Math.round(report.categories["best-practices"].score * 100),
    seo: Math.round(report.categories.seo.score * 100),
  };
}

function warmRoute(url) {
  spawnSync("curl", ["-fsSLo", "/dev/null", url], { stdio: "ignore" });
}

function checkDocumentByteBudget(url) {
  const result = spawnSync(
    "curl",
    ["--compressed", "-fsSo", "/dev/null", "-w", "%{size_download}", url],
    { encoding: "utf-8" }
  );
  const bytes = Number.parseInt(result.stdout, 10);

  if (result.status !== 0 || !Number.isFinite(bytes)) {
    console.error(`[document-budget] failed to fetch ${url}: ${result.stderr || `exit ${result.status}`}`);
    process.exit(1);
  }

  console.log(
    `[document-budget] ${url} -> ${bytes} bytes compressed (cap ${HOME_DOCUMENT_BYTE_CAP}, ${Math.round(
      (bytes / HOME_DOCUMENT_BYTE_CAP) * 100
    )}% of budget)`
  );

  if (bytes > HOME_DOCUMENT_BYTE_CAP) {
    console.error(
      `[document-budget] home document is ${bytes} bytes compressed, over the ${HOME_DOCUMENT_BYTE_CAP} byte cap. ` +
        "With inlineCss on, every byte here delays first paint on every page view. " +
        "Find what grew (inlined CSS, serialized props, a new provider) before raising the cap."
    );
    process.exit(1);
  }
}

function totalScore(scores) {
  return Object.values(scores).reduce((sum, score) => sum + score, 0);
}

function logFailureDiagnostics(reportPath) {
  const report = JSON.parse(readFileSync(reportPath, "utf-8"));
  const metrics = report.audits.metrics?.details?.items?.[0];

  if (metrics) {
    const formatMetric = (value) => `${Math.round(value)}ms`;
    console.error(
      `[lighthouse] metrics: fcp=${formatMetric(metrics.firstContentfulPaint)} lcp=${formatMetric(metrics.largestContentfulPaint)} tbt=${formatMetric(metrics.totalBlockingTime)} si=${formatMetric(metrics.speedIndex)} cls=${metrics.cumulativeLayoutShift}`
    );
  }

  const opportunities = Object.values(report.audits)
    .filter((audit) => audit.details?.type === "opportunity" && typeof audit.numericValue === "number")
    .sort((left, right) => right.numericValue - left.numericValue)
    .slice(0, 5)
    .map((audit) => `${audit.id}:${Math.round(audit.numericValue)}ms`);

  if (opportunities.length > 0) {
    console.error(`[lighthouse] top opportunities: ${opportunities.join(", ")}`);
  }

  const failedAudits = Object.values(report.audits)
    .filter((audit) => audit.score !== null && audit.score < 1 && audit.scoreDisplayMode === "binary")
    .slice(0, 10)
    .map((audit) => audit.id);

  if (failedAudits.length > 0) {
    console.error(`[lighthouse] failed audits: ${failedAudits.join(", ")}`);
  }

  const layoutShiftItems = report.audits["layout-shift-elements"]?.details?.items
    ?.slice(0, 5)
    .map((item) => {
      const node = item.node ?? {};
      const snippet = node.snippet ?? node.nodeLabel ?? node.path ?? "unknown";
      return `${snippet} (${Math.round((item.score ?? 0) * 1000) / 1000})`;
    });

  if (layoutShiftItems?.length) {
    console.error(`[lighthouse] layout-shift-elements: ${layoutShiftItems.join(" | ")}`);
  }
}
