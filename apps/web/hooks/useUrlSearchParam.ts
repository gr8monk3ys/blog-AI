'use client'

import { useCallback, useSyncExternalStore } from 'react'

const URL_CHANGE_EVENT = 'app:urlchange'

function subscribe(onChange: () => void): () => void {
  window.addEventListener('popstate', onChange)
  window.addEventListener(URL_CHANGE_EVENT, onChange)
  return () => {
    window.removeEventListener('popstate', onChange)
    window.removeEventListener(URL_CHANGE_EVENT, onChange)
  }
}

/**
 * Keep a piece of UI state (tab, filter, search) in a URL search param so it
 * can be deep-linked and restored with Back/Forward. Server render and
 * hydration use `fallback` (no mismatch); the URL value takes over right
 * after. Updates use history.replaceState (no navigation, no history spam).
 */
export function useUrlSearchParam<T extends string>(
  name: string,
  fallback: T,
  isValid: (value: string) => value is T = (value): value is T => value.length > 0
): [T, (next: T) => void] {
  const getSnapshot = useCallback((): T => {
    const raw = new URLSearchParams(window.location.search).get(name)
    return raw !== null && isValid(raw) ? raw : fallback
  }, [name, fallback, isValid])
  const getServerSnapshot = useCallback((): T => fallback, [fallback])
  const value = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)

  const setValue = useCallback(
    (next: T) => {
      const url = new URL(window.location.href)
      if (next === fallback) url.searchParams.delete(name)
      else url.searchParams.set(name, next)
      window.history.replaceState(window.history.state, '', url)
      window.dispatchEvent(new Event(URL_CHANGE_EVENT))
    },
    [name, fallback]
  )

  return [value, setValue]
}
