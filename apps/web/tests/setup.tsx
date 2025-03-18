import '@testing-library/jest-dom'
import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import React from 'react'
import type { ReactNode } from 'react'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock fetch globally
global.fetch = vi.fn()

// ---------------------------------------------------------------------------
// Mock next/navigation
// ---------------------------------------------------------------------------
const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  refresh: vi.fn(),
  prefetch: vi.fn(),
}

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => mockRouter),
  usePathname: vi.fn(() => '/'),
  useSearchParams: vi.fn(() => new URLSearchParams()),
  useParams: vi.fn(() => ({})),
  redirect: vi.fn(),
  notFound: vi.fn(),
}))

// ---------------------------------------------------------------------------
// Mock next/image
// ---------------------------------------------------------------------------
vi.mock('next/image', () => ({
  default: (props: Record<string, unknown>) => {
    const { alt, ...rest } = props
    return React.createElement('img', {
      ...rest,
      alt: typeof alt === 'string' ? alt : '',
    })
  },
}))

// ---------------------------------------------------------------------------
// Mock next/link (render as plain <a> to keep assertions simple)
// ---------------------------------------------------------------------------
vi.mock('next/link', () => ({
  default: ({
    children,
    href,
    ...rest
  }: {
    children: ReactNode
    href: string
    [key: string]: unknown
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}))

// ---------------------------------------------------------------------------
// Mock @clerk/nextjs
// ---------------------------------------------------------------------------
vi.mock('@clerk/nextjs', () => ({
  SignedIn: ({ children }: { children: ReactNode }) => <>{children}</>,
  SignedOut: ({ children }: { children: ReactNode }) => <>{children}</>,
  UserButton: () => <div data-testid="clerk-user-button" />,
  SignIn: () => <div data-testid="clerk-sign-in" />,
  SignUp: () => <div data-testid="clerk-sign-up" />,
  useUser: () => ({ isSignedIn: true, user: { id: 'test-user' } }),
  useAuth: () => ({
    isLoaded: true,
    isSignedIn: true,
    userId: 'test-user',
    getToken: vi.fn().mockResolvedValue('mock-token'),
  }),
  ClerkProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
  auth: () => ({ userId: 'test-user' }),
}))

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn()

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState = MockWebSocket.OPEN
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(public url: string) {
    setTimeout(() => {
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 0)
  }

  send(_data: string): void {}

  close(): void {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close'))
    }
  }
}

global.WebSocket = MockWebSocket as unknown as typeof WebSocket

// Mock window.alert
global.alert = vi.fn()

// Mock console methods to reduce noise in tests
vi.spyOn(console, 'log').mockImplementation(() => {})
vi.spyOn(console, 'error').mockImplementation(() => {})
vi.spyOn(console, 'warn').mockImplementation(() => {})
