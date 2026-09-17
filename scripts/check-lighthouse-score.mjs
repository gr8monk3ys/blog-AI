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

// Mobile floors. Measured the same way as the desktop ones: three runs per
// route of the production build on 2026-09-16, `--form-factor=mobile
// --screenEmulation.mobile --throttling-method=devtools`, colour scheme pinned
// light, no backend on NEXT_PUBLIC_API_URL (exactly what CI does):
//   /         perf 100  a11y 100  bp 96  seo 100   (cls 0.013)
//   /pricing  perf 100  a11y 100  bp 96  seo 100   (cls 0.000)
//   /blog     perf 100  a11y 100  bp 96  seo 100   (cls 0.000)
//   /tools    perf 100  a11y 100  bp 96  seo 100   (cls 0.000)
// Identical on all three runs. Accessibility, best-practices and SEO sit at
// the observed value, same as desktop.
//
// Performance does NOT sit two below the observed 100, and the reason matters.
// The desktop preset simulates a fixed CPU and network, so its numbers travel
// between machines. `--throttling-method=devtools` does not: it applies a 4x
// slowdown to whatever CPU it is running on, and a 2-vCPU GitHub runner is
// several times slower than the machine those 100s came off. A floor of 98
// would fail on hardware alone, and a floor that fails on noise gets bypassed,
// which leaves no check at all.
//
// So the floor comes from modelling the slower host instead of pretending it
// does not exist. Same build, same routes, extra CPU slowdown:
//   cpuSlowdownMultiplier 8   -> /pricing 97, /tools 96
//   cpuSlowdownMultiplier 16  -> /pricing 83, /tools 82
// 16x is the pessimistic end of what a runner looks like. Two below its
// minimum is 80. That is still nowhere near permissive: the defect this
// profile was added to catch — /pricing fetching its plan cards after
// hydration — scored 62-67 on THIS machine at the normal setting, and 62 in
// production. Tighten this to two below the observed CI minimum once real
// runner numbers exist; every run prints its score, so the headroom is visible.
const MOBILE_SCORE_FLOORS = {
  performance: 80,
  accessibility: 100,
  bestPractices: 96,
  seo: 100,
};

// Hardware-independent budgets, mobile only. These are the real gate. The
// regression this profile was added for was a layout shift and a paint that
// waited for hydration, and neither number cares how fast the host is: CLS was
// 0.000 at every CPU multiplier above, and LCP moved only 1.20 s -> 1.40 s
// between 4x and 16x. A composite performance score cannot say that.
// Observed after the fix: CLS 0.000 on every route except / at 0.013, mobile
// LCP 0.84-1.15 s (1.40 s at 16x). Budgets are 0.1 (Core Web Vitals "good")
// and 3 s — loose enough for a slow runner, tight enough that the 0.359 /
// 4.7 s this replaced could not sneak back.
const MOBILE_METRIC_BUDGETS = {
  cumulativeLayoutShift: { limit: 0.1, format: (v) => v.toFixed(3) },
  largestContentfulPaint: { limit: 3000, format: (v) => `${Math.round(v)}ms` },
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
        const budgetFailures = checkMetricBudgets(metrics, profile.metricBudgets);

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
