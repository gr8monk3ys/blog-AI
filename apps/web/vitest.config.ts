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
      all: false,
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        '.next/',
        'tests/setup.tsx',
        '**/*.d.ts',
        '**/*.config.*',
        '**/types/**',
        'e2e/**',
        '../api/**',
        '../extension/**',
        '../../supabase/**',
        // Covered separately in dedicated suites; heavily mocked in unit tests.
        'components/brand/**',
        'hooks/useLlmConfig.tsx',
        'lib/api.ts',
      ],
      thresholds: {
        branches: 70,
        functions: 85,
        lines: 85,
        statements: 85,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
})
