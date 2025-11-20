import { describe, it, expect, vi, afterEach } from 'vitest'
import { act, render, screen } from '@testing-library/react'
import Loading from '../../app/loading'

afterEach(() => {
  vi.useRealTimers()
})

describe('Loading', () => {
  it('renders the loading message', () => {
    render(<Loading />)
    expect(screen.getByText('Loading your workspace...')).toBeInTheDocument()
  })

  it('renders a spinner animation element', () => {
    const { container } = render(<Loading />)
    const spinner = container.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })

  it('is wrapped in a centered container', () => {
    const { container } = render(<Loading />)
    const wrapper = container.firstElementChild
    expect(wrapper).toHaveClass('min-h-screen')
    expect(wrapper).toHaveClass('flex')
    expect(wrapper).toHaveClass('items-center')
    expect(wrapper).toHaveClass('justify-center')
  })

  it('shows a timeout help panel after 8 seconds', () => {
    vi.useFakeTimers()
    render(<Loading />)

    expect(screen.queryByText('Still loading?')).not.toBeInTheDocument()
    act(() => {
      vi.advanceTimersByTime(8000)
    })
    expect(screen.getByText('Still loading?')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: 'Open Tool Directory' })
    ).toBeInTheDocument()
  })
})
