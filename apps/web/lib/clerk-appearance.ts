/**
 * Clerk's `appearance` mapped onto the notebook's tokens, shared by the
 * sign-in, sign-up and /auth pages.
 *
 * The colours are the CSS custom properties from app/globals.css rather than
 * hex values, so the same object renders Iron Gall on paper by day and the
 * lifted Iron Gall on night under `.dark` with no second theme object. The
 * radius is the field radius (8px) and the type is the body voice; Clerk's
 * card chrome (shadow, border) is flattened through `elements` so the form
 * sits on the paper like every other surface (DESIGN.md → Elevation → The
 * Flat Paper Rule).
 */
export const clerkAppearance = {
  variables: {
    colorPrimary: 'hsl(var(--primary))',
    colorBackground: 'hsl(var(--background))',
    colorForeground: 'hsl(var(--foreground))',
    colorMutedForeground: 'hsl(var(--muted-foreground))',
    colorMuted: 'hsl(var(--muted))',
    colorInput: 'hsl(var(--card))',
    colorInputForeground: 'hsl(var(--foreground))',
    colorBorder: 'hsl(var(--border))',
    colorRing: 'hsl(var(--ring))',
    colorDanger: 'hsl(var(--destructive))',
    colorSuccess: 'hsl(var(--success))',
    colorWarning: 'hsl(var(--warning))',
    colorNeutral: 'hsl(var(--foreground))',
    borderRadius: '8px',
    fontFamily: 'var(--font-body), ui-sans-serif, system-ui, sans-serif',
    fontFamilyButtons: 'var(--font-body), ui-sans-serif, system-ui, sans-serif',
  },
  elements: {
    rootBox: 'w-full',
    cardBox: 'w-full shadow-none',
    card: 'bg-transparent shadow-none px-0 py-0',
    footer: 'bg-transparent',
    headerTitle: 'font-display',
  },
} as const
