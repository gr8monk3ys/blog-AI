import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Loading from '../../app/loading'

describe('Loading', () => {
  it('should render an element with role="status"', () => {
    render(<Loading />)

    const statusElement = screen.getByRole('status')
    expect(statusElement).toBeInTheDocument()
  })

  it('should have an aria-label on the status element', () => {
    render(<Loading />)

    const statusElement = screen.getByRole('status')
    expect(statusElement).toHaveAttribute('aria-label', 'Loading')
  })

  it('should contain screen-reader-only text', () => {
    render(<Loading />)

    const srText = screen.getByText('Loading')
    expect(srText).toBeInTheDocument()
    expect(srText).toHaveClass('sr-only')
  })

  it('should render the spinner animation element', () => {
    const { container } = render(<Loading />)

    const spinner = container.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })

  it('should be wrapped in a centered container', () => {
    const { container } = render(<Loading />)

    const wrapper = container.firstElementChild
    expect(wrapper).toHaveClass('min-h-screen')
    expect(wrapper).toHaveClass('flex')
    expect(wrapper).toHaveClass('items-center')
    expect(wrapper).toHaveClass('justify-center')
  })
})
