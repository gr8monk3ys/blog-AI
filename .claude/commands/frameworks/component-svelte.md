---
description: Create a new Svelte 5 component with TypeScript and runes
model: claude-opus-4-5
---

Generate a new Svelte 5 component following 2025 best practices.

## Component Specification

$ARGUMENTS

## Modern Svelte 5 + TypeScript Standards

### 1. **Svelte 5 Runes**
- Use runes (`$state`, `$derived`, `$effect`)
- TypeScript with `<script lang="ts">`
- Svelte 5 patterns

### 2. **TypeScript Best Practices**
- Strict typing
- Props with `$props()` rune
- NO `any` types
- Explicit types where needed

### 3. **Component Patterns**

**Svelte 5 Component**
```svelte
<script lang="ts">
  interface Props {
    title: string
    count?: number
    onUpdate?: (value: number) => void
  }

  let { title, count = 0, onUpdate }: Props = $props()

  let localCount = $state(count)
  let doubled = $derived(localCount * 2)

  function increment() {
    localCount++
    onUpdate?.(localCount)
  }
</script>

<div class="component">
  <h2>{title}</h2>
  <p>Count: {localCount} (doubled: {doubled})</p>
  <button onclick={increment}>Increment</button>
</div>

<style>
  .component {
    /* scoped styles */
  }
</style>
```

### 4. **State Management**
- `$state()` for reactive state
- `$derived()` for computed values
- `$effect()` for side effects
- Svelte stores for global state

### 5. **Performance**
- Automatic fine-grained reactivity
- No virtual DOM overhead
- Compile-time optimizations
- Lazy loading with dynamic imports

### 6. **Styling Approach** (choose based on project)
- **Scoped CSS** - Default Svelte scoping
- **Tailwind CSS** - Utility-first
- **Global styles** - `:global()` selector
- **CSS variables** - Theming support

## What to Generate

1. **Component File** - `.svelte` with TypeScript
2. **Props Interface** - Typed with `$props()`
3. **Event Callbacks** - Function props for events
4. **Stores** (if needed) - Shared state
5. **Example Usage** - How to import and use

## Code Quality Standards

**Structure**
- Feature-based folder organization
- Co-locate related files
- Barrel exports (index.ts)
- PascalCase component names

**TypeScript**
- Interface for props
- Type callback functions
- Generic components where needed
- Use `$$Props` for full prop typing

**Props**
- Required vs optional with defaults
- Destructure in `$props()`
- Callback props for events
- Spread props with `{...rest}`

**Accessibility**
- Semantic HTML
- ARIA labels where needed
- Keyboard navigation
- Focus management

**Best Practices**
- Single Responsibility Principle
- Extract logic to separate files
- Keep components focused
- Use snippets for reusable markup

## Svelte 5 Runes

**$state - Reactive State**
```svelte
<script lang="ts">
  let count = $state(0)
  let user = $state<User | null>(null)

  // Deep reactivity for objects
  let todos = $state<Todo[]>([])
</script>
```

**$derived - Computed Values**
```svelte
<script lang="ts">
  let count = $state(0)
  let doubled = $derived(count * 2)

  // Complex derivations
  let filtered = $derived(
    todos.filter(t => !t.completed)
  )
</script>
```

**$effect - Side Effects**
```svelte
<script lang="ts">
  let count = $state(0)

  $effect(() => {
    console.log('Count changed:', count)
    // Cleanup function (optional)
    return () => {
      console.log('Cleanup')
    }
  })
</script>
```

**$props - Component Props**
```svelte
<script lang="ts">
  interface Props {
    required: string
    optional?: number
    withDefault?: boolean
  }

  let {
    required,
    optional,
    withDefault = true
  }: Props = $props()
</script>
```

**$bindable - Two-way Binding**
```svelte
<script lang="ts">
  interface Props {
    value: string
  }

  let { value = $bindable() }: Props = $props()
</script>

<!-- Usage -->
<Input bind:value={name} />
```

## Snippets Pattern

**Defining Snippets**
```svelte
<script lang="ts">
  interface Props {
    header?: Snippet
    children: Snippet
  }

  let { header, children }: Props = $props()
</script>

{#if header}
  <header>{@render header()}</header>
{/if}

<main>{@render children()}</main>
```

**Using Snippets**
```svelte
<Card>
  {#snippet header()}
    <h2>Title</h2>
  {/snippet}

  <p>Card content goes here</p>
</Card>
```

## SvelteKit Considerations (if applicable)

- `+page.svelte` for routes
- `+layout.svelte` for layouts
- `+page.server.ts` for server load
- `$app/stores` for page/navigation stores
- Form actions for mutations

Generate production-ready, accessible, and performant Svelte 5 components following modern patterns.
