'use client';

import { ReactNode, createContext } from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import ConnectionStatus from '../components/ConnectionStatus';

// Create a context for HeadlessUI
export const HeadlessUIContext = createContext({});

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <HeadlessUIContext.Provider value={{}}>
      <ErrorBoundary>
        {children}
        <ConnectionStatus />
      </ErrorBoundary>
    </HeadlessUIContext.Provider>
  );
}
