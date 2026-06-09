import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.tsx'],
    testTimeout: 10000,
    include: ['**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    // Keep Playwright E2E tests and any dependency test suites out of Vitest's collection.
    exclude: ['e2e/**', 'node_modules/**'],
    coverage: {
      provider: 'v8',
      // Measure every source file, not just the ones a test happens to import.
      // Previously `all: false` meant untested files were invisible to the gate,
      // so the reported percentages described only the tested slice of the app.
      all: true,
      include: [
        'app/**/*.{ts,tsx}',
        'components/**/*.{ts,tsx}',
        'hooks/**/*.{ts,tsx}',
        'lib/**/*.{ts,tsx}',
        'proxy.ts',
      ],
      reporter: ['text', 'json', 'html', 'text-summary'],
      exclude: [
        'node_modules/',
        '.next/',
        'tests/setup.tsx',
        '**/*.d.ts',
        '**/*.config.*',
        '**/types/**',
        // Next.js framework files with no meaningful logic to unit test.
        'app/**/layout.tsx',
        'app/**/loading.tsx',
        'app/**/not-found.tsx',
        'app/**/error.tsx',
        'app/**/sitemap.ts',
        'app/**/robots.ts',
        'e2e/**',
        '../api/**',
        '../extension/**',
        '../../supabase/**',
      ],
      // Ratchet policy: these reflect the REAL baseline measured with all:true
      // (~10% — the previous all:false gate only saw the ~600 statements tests
      // imported, hiding ~90% of the app) and only ever move UP. Target:
      // branches 70 / functions+lines+statements 85 as tests are backfilled
      // (see docs/REMEDIATION_PLAN.md P1.1/P1.2). Do NOT lower these to make a
      // red build green — add tests instead.
      thresholds: {
        branches: 10,
        functions: 11,
        lines: 11,
        statements: 11,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
})
