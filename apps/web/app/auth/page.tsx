import { redirect } from 'next/navigation'

// Back-compat route: older links point at /auth.
export default function AuthPage() {
  redirect('/sign-in')
}
