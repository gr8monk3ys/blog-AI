import js from '@eslint/js'
import nextPlugin from '@next/eslint-plugin-next'
import reactHooks from 'eslint-plugin-react-hooks'
import tseslint from '@typescript-eslint/eslint-plugin'
import tsParser from '@typescript-eslint/parser'
import globals from 'globals'

const COMMON_IGNORES = [
  '.next/**',
  'node_modules/**',
  'backend/**',
  'chrome-extension/**',
  'supabase/**',
]

export default [
  { ignores: COMMON_IGNORES },

  // Base JS recommendations.
  js.configs.recommended,

  // TypeScript / TSX
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: { jsx: true },
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.es2021,
      },
    },
    plugins: {
      '@typescript-eslint': tseslint,
      '@next/next': nextPlugin,
      'react-hooks': reactHooks,
    },
    rules: {
      ...(tseslint.configs.recommended?.rules ?? {}),
      ...(nextPlugin.configs['core-web-vitals']?.rules ?? {}),
      ...(reactHooks.configs?.recommended?.rules ?? {}),
      // TypeScript already checks undefined symbols; this rule is noisy in TS/Next code.
      'no-undef': 'off',
      // Too strict for the current codebase; keep type-checking as the primary guard.
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],

      // react-hooks v5+ adds compiler-adjacent rules that are noisy (and sometimes
      // false positives) for this codebase. Keep the core hook rules, disable the rest.
      'react-hooks/purity': 'off',
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/static-components': 'off',
    },
  },

  // JS / JSX
  {
    files: ['**/*.{js,jsx,mjs,cjs}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.es2021,
      },
    },
    plugins: {
      '@next/next': nextPlugin,
      'react-hooks': reactHooks,
    },
    rules: {
      ...(nextPlugin.configs['core-web-vitals']?.rules ?? {}),
      ...(reactHooks.configs?.recommended?.rules ?? {}),

      'react-hooks/purity': 'off',
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/static-components': 'off',
    },
  },
]
