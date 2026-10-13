import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Logo, LogoMark, MARK_PATH } from '../../../components/brand/Logo'
import { Button } from '../../../components/ui/Button'
import { Badge } from '../../../components/ui/Badge'
import { Card, CardTitle } from '../../../components/ui/Card'
import { Input } from '../../../components/ui/Input'
import { Plate } from '../../../components/ui/Plate'
import { Select } from '../../../components/ui/Select'
import { Textarea } from '../../../components/ui/Textarea'

describe('Logo', () => {
  it('the mark is decorative unless titled, and takes the ink from the theme', () => {
    const { container, rerender } = render(<LogoMark />)
    const svg = container.querySelector('svg')!
    expect(svg).toHaveAttribute('aria-hidden', 'true')
    expect(svg.querySelector('path')).toHaveAttribute('d', MARK_PATH)
    expect(svg.querySelector('path')).toHaveAttribute('fill', 'hsl(var(--primary))')
    expect(svg.querySelector('path')).toHaveAttribute('fill-rule', 'evenodd')

    rerender(<LogoMark title="Blog AI" />)
    expect(screen.getByRole('img', { name: 'Blog AI' })).toBeInTheDocument()
  })

  it('the horizontal lockup names itself and sets the wordmark from the cap height', () => {
    render(<Logo size={28} />)
    const logo = screen.getByRole('img', { name: 'Blog AI' })
    const wordmark = logo.querySelector('[data-voice="display"]') as HTMLElement
    expect(wordmark).toHaveClass('font-display')
    expect(wordmark.style.fontSize).toBe(`${28 / 0.7}px`)
    expect(wordmark.textContent).toBe('Blog AI')
    expect(wordmark.querySelector('.text-primary')?.textContent).toBe('AI')
  })

  it('the mark variant is the stamp alone', () => {
    const { container } = render(<Logo variant="mark" />)
    expect(container.querySelectorAll('svg')).toHaveLength(1)
    expect(container.textContent).toBe('Blog AI') // the <title> only
  })
})

describe('Button', () => {
  it('defaults to the one primary button and type=button', () => {
    render(<Button>Save</Button>)
    const button = screen.getByRole('button', { name: 'Save' })
    expect(button).toHaveClass('cta-primary')
    expect(button).toHaveAttribute('type', 'button')
  })

  it('outline and secondary are the paper-card button; link is the ink underline', () => {
    const { rerender } = render(<Button variant="outline">A</Button>)
    expect(screen.getByRole('button')).toHaveClass('cta-secondary')
    rerender(<Button variant="secondary">A</Button>)
    expect(screen.getByRole('button')).toHaveClass('cta-secondary')
    rerender(<Button variant="link">A</Button>)
    expect(screen.getByRole('button')).toHaveClass('ink-underline')
    rerender(<Button variant="destructive">A</Button>)
    expect(screen.getByRole('button')).toHaveClass('cta-secondary', 'text-destructive')
  })

  it('never stacks a ring; focus is the global outline', () => {
    render(<Button variant="ghost">A</Button>)
    expect(screen.getByRole('button').className).not.toMatch(/ring-/)
  })
})

describe('fields', () => {
  it('Input, Textarea and Select share the input-field treatment', () => {
    render(
      <>
        <Input aria-label="title" />
        <Textarea aria-label="body" />
        <Select aria-label="tone">
          <option>Plain</option>
        </Select>
      </>
    )
    expect(screen.getByLabelText('title')).toHaveClass('input-field')
    expect(screen.getByLabelText('body')).toHaveClass('input-field')
    expect(screen.getByLabelText('tone')).toHaveClass('input-field')
  })
})

describe('Card, Badge, Plate', () => {
  it('Card is paper card with a hairline and no shadow; its title is a heading', () => {
    render(
      <Card data-testid="card">
        <CardTitle>Draft</CardTitle>
      </Card>
    )
    const card = screen.getByTestId('card')
    expect(card).toHaveClass('bg-card', 'border-border')
    expect(card.className).not.toMatch(/shadow/)
    expect(screen.getByRole('heading', { name: 'Draft' })).toHaveClass('font-display')
  })

  it('Badge is a round chip; the filled form is the ink', () => {
    const { rerender } = render(<Badge variant="outline">Tag</Badge>)
    expect(screen.getByText('Tag')).toHaveClass('rounded-full', 'bg-card')
    rerender(<Badge>PRO</Badge>)
    expect(screen.getByText('PRO')).toHaveClass('bg-primary')
    rerender(<Badge variant="success">Live</Badge>)
    expect(screen.getByText('Live')).toHaveClass('text-success')
  })

  it('Plate is the square draft sheet, portrait by default', () => {
    const { rerender } = render(<Plate data-testid="plate" />)
    expect(screen.getByTestId('plate')).toHaveClass('plate')
    expect(screen.getByTestId('plate').style.aspectRatio).toBe('3 / 4')
    rerender(<Plate data-testid="plate" aspect="auto" />)
    expect(screen.getByTestId('plate').style.aspectRatio).toBe('')
  })
})
