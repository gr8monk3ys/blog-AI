import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { chromium } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Dark-mode accessibility gate for the public marketing routes.
//
// Why this exists, separately from check-lighthouse-score.mjs:
//
// Lighthouse renders whatever colour scheme the host Chrome happens to prefer.
// On a GitHub runner that is always light, so the desktop score-floor check
// reported accessibility 100 for /pricing while production, rendered dark,
// scored 94: the comparison-table headers carried `text-gray-700` /
// `text-amber-700` / `text-indigo-700` with no dark: variant and sat on
// gray-900 at 1.72:1, 3.53:1 and 2.24:1. The "Free" column header was
// invisible. CI could not have caught it, because CI never saw dark mode.
//
// Lighthouse has no prefers-color-scheme switch, and `--force-dark-mode` does
// not move `prefers-color-scheme` at all (verified: it still reports light) —
// it is Chrome's auto-darkening of light pages, which is a different feature.
// Playwright emulates the media feature properly, so the dark pass is a
// Playwright + axe-core run over the same routes, in the same CI job, against
// the same server.
//
// Mobile viewport on purpose: it is the other half of the same blind spot.
const VIEWPORT = { width: 412, height: 823 };

// Everything axe can decide on its own at WCAG 2.1 AA, plus its best-practice
// rules — that is where heading-order lives, the other defect /pricing shipped,
// and all four routes pass them today (37-43 rules per route), so including
// them costs nothing and catches more.
//
// No per-route exceptions: every route is clean, and a violation here is a real
// one. If a route ever needs an exception, add it with the ratio and the
// reason, not as a blanket rule disable.
const AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"];

const artifactDir = join(process.cwd(), "artifacts", "lighthouse");
const [baseUrl, ...routes] = process.argv.slice(2);

if (!baseUrl || routes.length === 0) {
  console.error("Usage: node scripts/check-dark-mode-a11y.mjs <baseUrl> <route...>");
  process.exit(1);
}

mkdirSync(artifactDir, { recursive: true });

const browser = await chromium.launch({ args: ["--no-sandbox"] });
let failed = false;

try {
  const context = await browser.newContext({ colorScheme: "dark", viewport: VIEWPORT });
  const page = await context.newPage();

  for (const route of routes) {
    const url = new URL(route, baseUrl).toString();
    await page.goto(url, { waitUntil: "load", timeout: 60_000 });

    // The theme provider resolves `system` to `dark` in an effect, so dark mode
    // only exists after hydration. Waiting for the class is also the assertion
    // that this run is genuinely testing dark mode.
    await page.waitForFunction(() => document.documentElement.classList.contains("dark"), null, {
      timeout: 15_000,
    });

    // Sections below the fold start at opacity 0 until an IntersectionObserver
    // flips data-inview (app/_home/Reveal.tsx). Walk the page so everything is
    // in its final painted state before axe looks at it.
    await page.evaluate(async () => {
      const step = window.innerHeight * 0.8;
      for (let y = 0; y < document.body.scrollHeight; y += step) {
        window.scrollTo(0, y);
        await new Promise((resolve) => setTimeout(resolve, 60));
      }
      window.scrollTo(0, 0);
    });
    await page.waitForTimeout(600);

    const results = await new AxeBuilder({ page }).withTags(AXE_TAGS).analyze();
    writeFileSync(
      join(artifactDir, `${artifactSlug(route)}-dark-axe.json`),
      JSON.stringify({ url, violations: results.violations }, null, 2)
    );

    const violations = results.violations;
    console.log(
      `[a11y:dark] ${route} -> ${violations.length} violation(s) across ${results.passes.length} passing rule(s)`
    );

    for (const violation of violations) {
      failed = true;
      console.error(`[a11y:dark] ${route} ${violation.id} (${violation.impact}): ${violation.help}`);
      for (const node of violation.nodes.slice(0, 8)) {
        const detail = [...node.any, ...node.all, ...node.none]
          .map((check) => check.message)
          .join("; ");
        console.error(`    ${node.target.join(" ")} -> ${detail}`);
        console.error(`      ${node.html.slice(0, 160)}`);
      }
    }
  }
} finally {
  await browser.close();
}

if (failed) {
  console.error(
    "[a11y:dark] dark-mode accessibility violations. These do not show up in the " +
      "Lighthouse pass above: it renders in the host's colour scheme, which on CI is light."
  );
  process.exit(1);
}

console.log("[a11y:dark] all routes clean in dark mode");

function artifactSlug(route) {
  return route === "/" ? "root" : route.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "");
}
