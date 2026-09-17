import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

// Lighthouse score floors for the public marketing routes, run against a
// production build (`next build && next start`) in CI.
//
// TWO PROFILES. Desktop was the only one for a while, on the theory that
// mobile devtools throttling swings too much on shared runners to floor
// safely. What that actually bought was a blind spot: with the desktop preset
// reporting /pricing at performance 98, production mobile was at 62 with a CLS
// of 0.359 and a 4.7 s LCP, because the plan cards were fetched after
// hydration and shoved the rest of the page down. A desktop-only gate cannot
// see a mobile-only regression, so mobile now runs too, with its own,
// separately measured floors (lower, and with room for runner noise) plus
// explicit metric budgets — a CLS budget is far more stable across hardware
// than a composite performance score, and CLS is the thing that actually broke.
//
// Colour scheme is pinned to light for both profiles. Lighthouse renders in
// whatever the host Chrome prefers, which is light on a GitHub runner and dark
// on a macOS machine set to dark, so identical commits scored differently
// depending on who ran them. Dark mode is covered properly, and separately, by
// scripts/check-dark-mode-a11y.mjs in the same CI job.
//
// Per-category floors rather than a blanket 100. Re-measured 2026-09-16 over
// three local runs of the production build (desktop preset), per route:
//   /         perf 100  a11y 100  bp 96  seo 100
//   /pricing  perf  98  a11y 100  bp 96  seo 100
//   /blog     perf 100  a11y 100  bp 96  seo 100
//   /tools    perf 100  a11y 100  bp 96  seo 100
// Performance sits 2 below the observed minimum; the others sit at it.
// Re-observed on the CI runner itself 2026-09-16 (twice): / 100, /pricing 99,
// /blog 100, /tools 100 — /pricing gained a point from the entrance-motion
// rewrite. The floor stays 96 rather than tracking up to 97 because the
// desktop preset's TBT still moves with the runner; raise it once there is
// more than a two-run history.
// Accessibility is a flat 100: the two defects that forced it down to 96 are
// fixed (the /pricing "Save 17%" badge was white on emerald-500, 2.54:1, now
// emerald-700 at 5.48:1; the /tools cards jumped h1 -> h3, and ToolGrid now
// takes a headingLevel). Every route in the list clears 100 on every run, so
// there is no per-route exception left to carve out. Note that a 100 here only
// means "100 in light mode" — see check-dark-mode-a11y.mjs.
// Best-practices is 96 rather than the 100 production scores because off
// Vercel the @vercel/analytics and @vercel/speed-insights loaders 404 on
// /_vercel/*, which trips errors-in-console. That is an artifact of the CI
// host, not of the code, and it is constant, so 96 still catches a real
// regression. A floor that fails on noise gets bypassed and a bypassed check
// is no check; a genuine regression lands well below the floor. Raise a floor
// whenever the real score improves.
const DESKTOP_SCORE_FLOORS = {
  performance: 96,
  accessibility: 100,
  bestPractices: 96,
  seo: 100,
};

// Mobile floors. Measured twice on the CI runner itself (the numbers printed
// by the "Lighthouse (score floors)" job on this branch, ubuntu-latest, no
// backend on NEXT_PUBLIC_API_URL), per route:
//   /         perf 98, 98   a11y 100  bp 96  seo 100   cls 0.016  lcp ~2.05 s
//   /pricing  perf 99, 99   a11y 100  bp 96  seo 100   cls 0.003  lcp ~1.18 s
//   /blog     perf 99, 99   a11y 100  bp 96  seo 100   cls 0.001  lcp ~0.85 s
//   /tools    perf 99, 97   a11y 100  bp 96  seo 100   cls 0.000  lcp ~0.91 s
// Observed minimum: performance 97. Floor is two below it, same rule as
// desktop; the others sit at the observed value.
//
// The floors deliberately come from the runner, not from a laptop. Unlike the
// desktop preset, `--throttling-method=devtools` applies its 4x slowdown to
// whatever host CPU it has, so local numbers do not transfer: the same build
// scores 100 on every route here and 97-99 on a 2-vCPU runner. Re-measure on
// CI, not locally, before touching these.
//
// 95 is not a soft floor. The defect this profile was added to catch —
// /pricing fetching its plan cards after hydration — scored 62 in production
// and 63-67 locally. And MAX_ATTEMPTS below means a route has to miss the
// floor four times in a row to fail the job, which is what keeps a 2-point
// runner wobble from turning into a red build.
const MOBILE_SCORE_FLOORS = {
  performance: 95,
  accessibility: 100,
  bestPractices: 96,
  seo: 100,
};

// Hardware-independent budgets, mobile only. These are the real gate. The
// regression this profile exists for was a layout shift plus a paint that
// waited for hydration, and neither number drifts with the host the way a
// composite score does: measured locally at cpuSlowdownMultiplier 4, 8 and 16,
// CLS stayed 0.000 throughout and LCP moved only 1.20 s -> 1.40 s.
//
// CLS 0.1 is the Core Web Vitals "good" threshold; the worst route on CI is /
// at 0.016. LCP defaults to 2.5 s, which /pricing (1.18 s on CI) clears with
// room to spare and the 4.7 s this replaced does not.
const MOBILE_METRIC_BUDGETS = {
  cumulativeLayoutShift: { limit: 0.1, format: (v) => v.toFixed(3) },
  largestContentfulPaint: { limit: 2500, format: (v) => `${Math.round(v)}ms` },
};

// Per-route budget exceptions. Keep this list short and always say why.
//
//   /  — the home hero renders at 2.04-2.06 s on the runner (0.78 s desktop);
//        it is a much heavier above-the-fold section than /pricing's, and it
//        is already at 98 performance. 3.5 s keeps ~1.4 s of headroom over the
//        measured value instead of failing the build on runner variance, and
//        still sits a second under the 4.7 s regression this profile guards.
//        Lower it if the home hero ever gets lighter.
const ROUTE_METRIC_BUDGETS = {
  mobile: {
    "/": { largestContentfulPaint: { limit: 3500, format: (v) => `${Math.round(v)}ms` } },
  },
};

const PROFILES = [
  {
    id: "desktop",
    lighthouseArgs: ["--preset=desktop"],
    floors: DESKTOP_SCORE_FLOORS,
    metricBudgets: {},
  },
  {
    id: "mobile",
    lighthouseArgs: [
      "--form-factor=mobile",
      "--screenEmulation.mobile",
      "--throttling-method=devtools",
    ],
    floors: MOBILE_SCORE_FLOORS,
    metricBudgets: MOBILE_METRIC_BUDGETS,
  },
];

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

  for (const profile of PROFILES) {
    for (const route of routes) {
      const url = new URL(route, baseUrl).toString();
      warmRoute(url);
      let bestAttempt = null;
      let attemptsRun = 0;

      for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
        attemptsRun = attempt;
        const reportPath = join(
          outputDir,
          `${artifactSlug(route)}-${profile.id}-attempt-${attempt}.json`
        );
        const { scores, metrics } = runLighthouse(url, reportPath, profile);
        const budgets = { ...profile.metricBudgets, ...(ROUTE_METRIC_BUDGETS[profile.id]?.[route] ?? {}) };
        const budgetFailures = checkMetricBudgets(metrics, budgets);

        console.log(
          `[lighthouse] ${profile.id} ${route} attempt ${attempt} -> ${JSON.stringify(scores)}` +
            ` cls=${metrics.cumulativeLayoutShift.toFixed(3)} lcp=${Math.round(metrics.largestContentfulPaint)}ms`
        );

        if (!bestAttempt || totalScore(scores) > totalScore(bestAttempt.scores)) {
          bestAttempt = { attempt, scores, reportPath, budgetFailures };
        }

        const scoresPass = Object.entries(scores).every(
          ([k, score]) => score >= (profile.floors[k] ?? 100)
        );
        if (scoresPass && budgetFailures.length === 0) break;
      }

      const failures = Object.entries(bestAttempt.scores).filter(
        ([k, score]) => score < (profile.floors[k] ?? 100)
      );
      copyFileSync(
        bestAttempt.reportPath,
        join(artifactDir, `${artifactSlug(route)}-${profile.id}.json`)
      );

      if (failures.length > 0 || bestAttempt.budgetFailures.length > 0) {
        console.error(
          `[lighthouse] ${profile.id} ${route} fell below its budget after ${attemptsRun} attempt(s): ` +
            [
              ...failures.map(([category, score]) => `${category}=${score}`),
              ...bestAttempt.budgetFailures,
            ].join(", ")
        );
        logFailureDiagnostics(bestAttempt.reportPath);
        process.exit(1);
      }
    }
  }

  checkDocumentByteBudget(new URL("/", baseUrl).toString());
} finally {
  rmSync(outputDir, { recursive: true, force: true });
}

function artifactSlug(route) {
  return route === "/" ? "root" : route.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "");
}

function runLighthouse(url, reportPath, profile) {
  const result = spawnSync(
    "npx",
    [
      "-y",
      "lighthouse",
      url,
      ...profile.lighthouseArgs,
      "--quiet",
      // preferredColorScheme=1 is light. Without it the run inherits the host
      // OS appearance, so the same commit scores differently on a dark-mode
      // laptop than on a CI runner. Dark mode has its own check.
      "--chrome-flags=--headless=new --no-sandbox --blink-settings=preferredColorScheme=1",
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
  const metrics = report.audits.metrics?.details?.items?.[0] ?? {};

  return {
    scores: {
      performance: Math.round(report.categories.performance.score * 100),
      accessibility: Math.round(report.categories.accessibility.score * 100),
      bestPractices: Math.round(report.categories["best-practices"].score * 100),
      seo: Math.round(report.categories.seo.score * 100),
    },
    metrics: {
      cumulativeLayoutShift: metrics.cumulativeLayoutShift ?? 0,
      largestContentfulPaint: metrics.largestContentfulPaint ?? 0,
      firstContentfulPaint: metrics.firstContentfulPaint ?? 0,
      totalBlockingTime: metrics.totalBlockingTime ?? 0,
    },
  };
}

function checkMetricBudgets(metrics, budgets) {
  return Object.entries(budgets)
    .filter(([metric, budget]) => metrics[metric] > budget.limit)
    .map(([metric, budget]) => `${metric}=${budget.format(metrics[metric])} (budget ${budget.limit})`);
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
