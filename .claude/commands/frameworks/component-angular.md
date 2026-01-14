---
description: Create a new Angular component with TypeScript and standalone components
model: claude-opus-4-5
---

Generate a new Angular component following 2025 best practices.

## Component Specification

$ARGUMENTS

## Modern Angular + TypeScript Standards

### 1. **Standalone Components**
- Use standalone components (default in Angular 17+)
- No NgModules for components
- Direct imports in component decorator

### 2. **TypeScript Best Practices**
- Strict typing (`strict: true`)
- Interface for inputs/outputs
- Proper Angular decorators typing
- NO `any` types
- Explicit return types

### 3. **Component Patterns**

**Standalone Component**
```typescript
import { Component, input, output, computed, signal } from '@angular/core'
import { CommonModule } from '@angular/common'

interface Props {
  title: string
  count?: number
}

@Component({
  selector: 'app-counter',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="component">
      <h2>{{ title() }}</h2>
      <p>Count: {{ count() }} (doubled: {{ doubled() }})</p>
      <button (click)="increment()">Increment</button>
    </div>
  `,
  styles: [`
    .component {
      /* component styles */
    }
  `]
})
export class CounterComponent {
  // Signal inputs (Angular 17+)
  title = input.required<string>()
  count = input<number>(0)

  // Signal outputs
  countChange = output<number>()

  // Internal signal state
  private internalCount = signal(0)

  // Computed values
  doubled = computed(() => this.internalCount() * 2)

  increment() {
    this.internalCount.update(c => c + 1)
    this.countChange.emit(this.internalCount())
  }
}
```

### 4. **State Management**
- Signals for local state (`signal()`)
- `computed()` for derived state
- NgRx SignalStore for global state
- Services for shared state

### 5. **Performance**
- `@defer` for lazy loading
- `OnPush` change detection
- `trackBy` for ngFor
- Signal-based reactivity

### 6. **Styling Approach** (choose based on project)
- **Component Styles** - Encapsulated CSS
- **Tailwind CSS** - Utility-first
- **SCSS** - Preprocessor features
- **Angular Material** - Component library

## What to Generate

1. **Component File** - Standalone TypeScript component
2. **Inputs/Outputs** - Signal-based I/O
3. **Template** - Inline or separate file
4. **Styles** - Scoped component styles
5. **Example Usage** - How to import and use

## Code Quality Standards

**Structure**
- Feature-based folder organization
- Standalone components
- Barrel exports (index.ts)
- Consistent naming (`.component.ts`)

**TypeScript**
- Signal inputs with `input()`
- Signal outputs with `output()`
- Typed services with interfaces
- Proper DI with `inject()`

**Inputs/Outputs**
- Required inputs with `input.required()`
- Default values with `input(defaultValue)`
- Aliased inputs where needed
- Transform functions for inputs

**Accessibility**
- Semantic HTML
- ARIA attributes
- Keyboard navigation
- Angular CDK a11y module

**Best Practices**
- Single Responsibility Principle
- Inject services with `inject()`
- Prefer signals over RxJS for UI state
- Keep templates readable

## Angular 17+ Features to Use

**Signal Inputs**
```typescript
// Required input
title = input.required<string>()

// Optional with default
count = input<number>(0)

// With transform
disabled = input(false, { transform: booleanAttribute })

// With alias
name = input<string>('', { alias: 'userName' })
```

**Signal Outputs**
```typescript
// Basic output
close = output<void>()

// Typed output
select = output<Item>()

// With alias
change = output<string>({ alias: 'valueChange' })
```

**Control Flow**
```html
@if (isLoggedIn()) {
  <app-dashboard />
} @else {
  <app-login />
}

@for (item of items(); track item.id) {
  <app-item [data]="item" />
} @empty {
  <p>No items found</p>
}

@switch (status()) {
  @case ('loading') { <app-spinner /> }
  @case ('error') { <app-error /> }
  @default { <app-content /> }
}
```

**Defer Blocks**
```html
@defer (on viewport) {
  <app-heavy-component />
} @placeholder {
  <div>Loading...</div>
} @loading (minimum 500ms) {
  <app-spinner />
} @error {
  <p>Failed to load</p>
}
```

## Service Pattern

**Injectable Service**
```typescript
import { Injectable, signal, computed } from '@angular/core'

@Injectable({ providedIn: 'root' })
export class CounterService {
  private count = signal(0)

  readonly currentCount = this.count.asReadonly()
  readonly doubled = computed(() => this.count() * 2)

  increment() {
    this.count.update(c => c + 1)
  }

  reset() {
    this.count.set(0)
  }
}
```

Generate production-ready, accessible, and performant Angular components following modern patterns.
