'use client';

import { ReactNode, createContext } from 'react';

// Create a context for HeadlessUI
export const HeadlessUIContext = createContext({});

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <HeadlessUIContext.Provider value={{}}>
      {children}
    </HeadlessUIContext.Provider>
  );
}
