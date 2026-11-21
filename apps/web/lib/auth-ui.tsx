'use client'

import type { ReactNode } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react'
import { UserCircleIcon } from '@heroicons/react/24/outline'
import { authClient } from './auth-client'

type UseAuthResult = {
  isLoaded: boolean
  isSignedIn: boolean
  userId: string | null
}

/**
 * Session state for client components. A session request that fails (network,
 * server error) settles as signed out, so signed-out UI is never left blank.
 */
export function useAuth(): UseAuthResult {
  const { data, isPending } = authClient.useSession()
  return {
    isLoaded: !isPending,
    isSignedIn: !!data,
    userId: data?.user.id ?? null,
  }
}

export function SignedIn({ children }: { children: ReactNode }): ReactNode {
  const { isLoaded, isSignedIn } = useAuth()
  return isLoaded && isSignedIn ? children : null
}

/** Renders while the session loads too, so CTAs never blink out on first paint. */
export function SignedOut({ children }: { children: ReactNode }): ReactNode {
  const { isSignedIn } = useAuth()
  return isSignedIn ? null : children
}

const menuItemClassName =
  'block w-full px-4 py-2 text-left text-sm text-foreground data-focus:bg-muted data-focus:text-primary'

export function AccountMenu(): ReactNode {
  const { data } = authClient.useSession()
  const router = useRouter()
  if (!data) return null

  const signOut = async (): Promise<void> => {
    await authClient.signOut()
    router.push('/')
    router.refresh()
  }

  return (
    <Menu>
      <MenuButton
        className="inline-flex size-9 items-center justify-center rounded-full text-foreground transition-colors hover:bg-muted hover:text-primary"
        aria-label="Account menu"
      >
        <UserCircleIcon className="size-6" aria-hidden="true" />
      </MenuButton>
      <MenuItems
        anchor="bottom end"
        className="z-30 mt-2 min-w-56 rounded-lg border border-border bg-card py-1 focus:outline-hidden"
      >
        <p className="truncate px-4 py-2 text-xs text-muted-foreground">{data.user.email}</p>
        <MenuItem>
          <Link href="/settings/webhooks" className={menuItemClassName}>
            Settings
          </Link>
        </MenuItem>
        <MenuItem>
          <button type="button" onClick={signOut} className={menuItemClassName}>
            Sign out
          </button>
        </MenuItem>
      </MenuItems>
    </Menu>
  )
}
