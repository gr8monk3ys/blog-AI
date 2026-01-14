---
description: Create a new Vue 3 component with TypeScript and Composition API
model: claude-opus-4-5
---

Generate a new Vue 3 component following 2025 best practices.

## Component Specification

$ARGUMENTS

## Modern Vue 3 + TypeScript Standards

### 1. **Composition API Only**
- Use `<script setup>` syntax (recommended)
- Composition API over Options API
- Vue 3.4+ features

### 2. **TypeScript Best Practices**
- Strict typing (`strict: true`)
- Define props with `defineProps<T>()`
- Define emits with `defineEmits<T>()`
- NO `any` types
- Use `PropType` for complex types

### 3. **Component Patterns**

**Single File Component (SFC)**
```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  title: string
  count?: number
}

const props = withDefaults(defineProps<Props>(), {
  count: 0
})

const emit = defineEmits<{
  (e: 'update', value: number): void
  (e: 'close'): void
}>()

const localCount = ref(props.count)

const doubled = computed(() => localCount.value * 2)

function increment() {
  localCount.value++
  emit('update', localCount.value)
}
</script>

<template>
  <div class="component">
    <h2>{{ title }}</h2>
    <p>Count: {{ localCount }} (doubled: {{ doubled }})</p>
    <button @click="increment">Increment</button>
  </div>
</template>

<style scoped>
.component {
  /* scoped styles */
}
</style>
```

### 4. **State Management**
- `ref()` for primitive values
- `reactive()` for objects
- `computed()` for derived state
- Pinia for global state
- Composables for shared logic

### 5. **Performance**
- `defineAsyncComponent()` for lazy loading
- `v-memo` for expensive list rendering
- `shallowRef()` for large objects
- `v-once` for static content

### 6. **Styling Approach** (choose based on project)
- **Scoped CSS** - Default Vue scoping
- **Tailwind CSS** - Utility-first
- **CSS Modules** - `<style module>`
- **UnoCSS** - Atomic CSS engine

## What to Generate

1. **Component File** - `.vue` SFC with TypeScript
2. **Props Interface** - Typed with `defineProps`
3. **Emits Definition** - Typed with `defineEmits`
4. **Composable** (if needed) - Reusable logic
5. **Example Usage** - How to import and use

## Code Quality Standards

**Structure**
- Feature-based folder organization
- Co-locate related files
- Barrel exports (index.ts)
- PascalCase component names

**TypeScript**
- Generic props with `defineProps<T>()`
- Typed emits with `defineEmits<T>()`
- Use `PropType` for complex types
- Template refs with proper typing

**Props**
- Required vs optional with `withDefaults()`
- Prop validation where needed
- Use readonly for immutable props

**Accessibility**
- Semantic HTML
- ARIA labels where needed
- Keyboard navigation
- Focus management

**Best Practices**
- Single Responsibility Principle
- Extract logic to composables
- Keep templates simple
- Use `v-bind` shorthand

## Composables Pattern

**Creating Composables**
```typescript
// composables/useCounter.ts
import { ref, computed } from 'vue'

export function useCounter(initial = 0) {
  const count = ref(initial)
  const doubled = computed(() => count.value * 2)

  function increment() {
    count.value++
  }

  function decrement() {
    count.value--
  }

  return {
    count,
    doubled,
    increment,
    decrement
  }
}
```

## Vue 3.4+ Features to Use

- **defineModel()** for v-model binding
- **Generics in SFC** with `<script setup lang="ts" generic="T">`
- **toValue()** for unwrapping refs/getters
- **Suspense** for async components
- **Teleport** for portal rendering

## Nuxt 3 Considerations (if applicable)

- Auto-imports for Vue APIs
- `useFetch()` for data fetching
- `useState()` for SSR-safe state
- `useAsyncData()` for async operations
- Server components with `.server.vue`

Generate production-ready, accessible, and performant Vue 3 components following modern patterns.
