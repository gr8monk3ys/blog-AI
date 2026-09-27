'use client';

import { ReactNode, createContext } from 'react';
import { LazyMotion, MotionConfig } from 'framer-motion';
import ErrorBoundary from '../components/ErrorBoundary';
import ConnectionStatus from '../components/ConnectionStatus';
import { ThemeProvider } from '../hooks/useTheme';

// Create a context for HeadlessUI
export const HeadlessUIContext = createContext({});

const loadMotionFeatures = () => import('../lib/motion-features').then((mod) => mod.default);

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider>
      {/* The app renders `m.*` components, which only animate inside
          LazyMotion; features load asynchronously after hydration.
          reducedMotion="user" honors prefers-reduced-motion everywhere. */}
      <LazyMotion features={loadMotionFeatures}>
        <MotionConfig reducedMotion="user">
          <HeadlessUIContext.Provider value={{}}>
            <ErrorBoundary>
              {children}
              <ConnectionStatus />
            </ErrorBoundary>
          </HeadlessUIContext.Provider>
        </MotionConfig>
      </LazyMotion>
    </ThemeProvider>
  );
}
