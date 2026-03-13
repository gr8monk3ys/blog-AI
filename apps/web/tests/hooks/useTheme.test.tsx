import { describe, it, expect, beforeEach, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { ThemeProvider, useTheme } from '../../hooks/useTheme'

function Harness(): JSX.Element {
  const { theme, resolvedTheme, setTheme } = useTheme()

  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="resolved-theme">{resolvedTheme}</span>
      <button type="button" onClick={() => setTheme('dark')}>
        Set Dark
      </button>
    </div>
  )
}

describe('useTheme', () => {
  beforeEach(() => {
    try {
      window.localStorage.removeItem('theme')
    } catch {
      // localStorage may be unavailable in some test runtimes
    }
    document.documentElement.classList.remove('dark')

    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    })
  })

  it('throws when used outside ThemeProvider', () => {
    function InvalidConsumer(): JSX.Element {
      useTheme()
      return <div>invalid</div>
    }

    expect(() => render(<InvalidConsumer />)).toThrow(
      'useTheme must be used within a ThemeProvider'
    )
  })

  it('applies and persists selected theme', async () => {
    render(
      <ThemeProvider>
        <Harness />
      </ThemeProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toHaveTextContent('system')
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light')
    })

    fireEvent.click(screen.getByRole('button', { name: 'Set Dark' }))

    await waitFor(() => {
      expect(screen.getByTestId('theme')).toHaveTextContent('dark')
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('dark')
      expect(document.documentElement.classList.contains('dark')).toBe(true)
    })
  })
})
