---
description: Create custom React hooks with TypeScript and best practices
model: claude-opus-4-5
---

Generate a custom React hook following modern best practices.

## Hook Specification

$ARGUMENTS

## Custom Hook Patterns

### Data Fetching Hook

```typescript
import { useState, useEffect } from 'react'

interface UseQueryOptions<T> {
  enabled?: boolean
  refetchInterval?: number
  onSuccess?: (data: T) => void
  onError?: (error: Error) => void
}

interface UseQueryResult<T> {
  data: T | null
  error: Error | null
  isLoading: boolean
  isError: boolean
  refetch: () => Promise<void>
}

export function useQuery<T>(
  queryFn: () => Promise<T>,
  options: UseQueryOptions<T> = {}
): UseQueryResult<T> {
  const { enabled = true, refetchInterval, onSuccess, onError } = options
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [isLoading, setIsLoading] = useState(enabled)

  const fetchData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const result = await queryFn()
      setData(result)
      onSuccess?.(result)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error')
      setError(error)
      onError?.(error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (!enabled) return

    fetchData()

    if (refetchInterval) {
      const interval = setInterval(fetchData, refetchInterval)
      return () => clearInterval(interval)
    }
  }, [enabled, refetchInterval])

  return {
    data,
    error,
    isLoading,
    isError: error !== null,
    refetch: fetchData
  }
}
```

### Form State Hook

```typescript
import { useState, useCallback, ChangeEvent, FormEvent } from 'react'

interface UseFormOptions<T> {
  initialValues: T
  validate?: (values: T) => Partial<Record<keyof T, string>>
  onSubmit: (values: T) => void | Promise<void>
}

interface UseFormResult<T> {
  values: T
  errors: Partial<Record<keyof T, string>>
  touched: Partial<Record<keyof T, boolean>>
  isSubmitting: boolean
  handleChange: (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void
  handleBlur: (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void
  handleSubmit: (e: FormEvent<HTMLFormElement>) => Promise<void>
  setFieldValue: (field: keyof T, value: T[keyof T]) => void
  resetForm: () => void
}

export function useForm<T extends Record<string, any>>({
  initialValues,
  validate,
  onSubmit
}: UseFormOptions<T>): UseFormResult<T> {
  const [values, setValues] = useState<T>(initialValues)
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({})
  const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleChange = useCallback((e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setValues(prev => ({ ...prev, [name]: value }))
  }, [])

  const handleBlur = useCallback((e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name } = e.target
    setTouched(prev => ({ ...prev, [name]: true }))

    if (validate) {
      const validationErrors = validate(values)
      setErrors(validationErrors)
    }
  }, [values, validate])

  const handleSubmit = useCallback(async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (validate) {
      const validationErrors = validate(values)
      setErrors(validationErrors)

      if (Object.keys(validationErrors).length > 0) {
        return
      }
    }

    setIsSubmitting(true)
    try {
      await onSubmit(values)
    } finally {
      setIsSubmitting(false)
    }
  }, [values, validate, onSubmit])

  const setFieldValue = useCallback((field: keyof T, value: T[keyof T]) => {
    setValues(prev => ({ ...prev, [field]: value }))
  }, [])

  const resetForm = useCallback(() => {
    setValues(initialValues)
    setErrors({})
    setTouched({})
    setIsSubmitting(false)
  }, [initialValues])

  return {
    values,
    errors,
    touched,
    isSubmitting,
    handleChange,
    handleBlur,
    handleSubmit,
    setFieldValue,
    resetForm
  }
}
```

### Local Storage Hook

```typescript
import { useState, useEffect } from 'react'

export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  // Get from local storage then parse stored json or return initialValue
  const readValue = (): T => {
    if (typeof window === 'undefined') {
      return initialValue
    }

    try {
      const item = window.localStorage.getItem(key)
      return item ? (JSON.parse(item) as T) : initialValue
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error)
      return initialValue
    }
  }

  const [storedValue, setStoredValue] = useState<T>(readValue)

  const setValue = (value: T | ((prev: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value
      setStoredValue(valueToStore)

      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore))
      }
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error)
    }
  }

  const removeValue = () => {
    try {
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(key)
      }
      setStoredValue(initialValue)
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error)
    }
  }

  useEffect(() => {
    setStoredValue(readValue())
  }, [])

  return [storedValue, setValue, removeValue]
}
```

### Debounced Value Hook

```typescript
import { useState, useEffect } from 'react'

export function useDebounce<T>(value: T, delay: number = 500): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}
```

### Media Query Hook

```typescript
import { useState, useEffect } from 'react'

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false)

  useEffect(() => {
    const media = window.matchMedia(query)

    if (media.matches !== matches) {
      setMatches(media.matches)
    }

    const listener = (event: MediaQueryListEvent) => {
      setMatches(event.matches)
    }

    media.addEventListener('change', listener)
    return () => media.removeEventListener('change', listener)
  }, [matches, query])

  return matches
}

// Usage
// const isMobile = useMediaQuery('(max-width: 768px)')
```

### Async State Hook

```typescript
import { useState, useCallback } from 'react'

type AsyncState<T> =
  | { status: 'idle'; data: null; error: null }
  | { status: 'loading'; data: null; error: null }
  | { status: 'success'; data: T; error: null }
  | { status: 'error'; data: null; error: Error }

export function useAsync<T>() {
  const [state, setState] = useState<AsyncState<T>>({
    status: 'idle',
    data: null,
    error: null
  })

  const execute = useCallback(async (promise: Promise<T>) => {
    setState({ status: 'loading', data: null, error: null })

    try {
      const data = await promise
      setState({ status: 'success', data, error: null })
      return data
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Unknown error')
      setState({ status: 'error', data: null, error: err })
      throw err
    }
  }, [])

  const reset = useCallback(() => {
    setState({ status: 'idle', data: null, error: null })
  }, [])

  return { ...state, execute, reset }
}
```

## Hook Best Practices

### Naming Convention
- Always prefix with `use` (e.g., `useCustomHook`)
- Use descriptive names that explain what the hook does
- Follow React naming conventions

### TypeScript
- Use generic types for reusability
- Provide clear type definitions
- Never use `any` - use `unknown` if type is truly unknown

### Dependencies
- List all dependencies in useEffect/useCallback
- Use ESLint rule `react-hooks/exhaustive-deps`
- Be careful with object/array dependencies (use refs if needed)

### Performance
- Use `useCallback` for functions passed to children
- Use `useMemo` for expensive calculations
- Avoid unnecessary re-renders

### Error Handling
- Always handle errors in async hooks
- Provide meaningful error messages
- Allow consumers to handle errors

### Side Effects
- Clean up side effects in useEffect return
- Handle component unmounting
- Cancel pending requests when component unmounts

## Common Hook Patterns

### Cleanup Pattern
```typescript
useEffect(() => {
  const controller = new AbortController()

  fetchData(controller.signal)

  return () => {
    controller.abort()
  }
}, [])
```

### Ref Pattern (Avoid Stale Closures)
```typescript
const latestCallback = useRef(callback)

useEffect(() => {
  latestCallback.current = callback
}, [callback])

useEffect(() => {
  const handler = () => latestCallback.current()
  // Use handler
}, [])
```

### Reducer Pattern (Complex State)
```typescript
type State = { /* ... */ }
type Action = { type: 'ACTION'; payload: any }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'ACTION':
      return { ...state, /* ... */ }
    default:
      return state
  }
}

export function useComplexState(initialState: State) {
  const [state, dispatch] = useReducer(reducer, initialState)
  return { state, dispatch }
}
```

## File Structure

```
hooks/
  ├── useQuery.ts
  ├── useForm.ts
  ├── useLocalStorage.ts
  ├── useDebounce.ts
  └── index.ts (barrel export)
```

## Output Format

Generate:
1. **Hook Implementation** - Complete TypeScript hook
2. **Type Definitions** - Full type safety
3. **Usage Example** - How to use the hook
4. **JSDoc Comments** - Document parameters and return
5. **Tests** - Basic test cases (optional)

## Code Quality Standards

- ✅ TypeScript strict mode
- ✅ Proper dependency arrays
- ✅ Error handling
- ✅ Memory leak prevention
- ✅ SSR compatibility (check `typeof window`)
- ✅ Performance optimizations
- ✅ Clear documentation

Generate production-ready, reusable custom hooks that follow React best practices and provide type safety.
