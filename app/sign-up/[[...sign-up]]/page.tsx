import SiteFooter from '../../../components/SiteFooter'
import SiteHeader from '../../../components/SiteHeader'
import { SignUp } from '@clerk/nextjs'

export default function SignUpPage() {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <SiteHeader />
      <section className="py-14 sm:py-20">
        <div className="max-w-lg mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-6 sm:p-8">
            {publishableKey ? (
              <SignUp routing="path" path="/sign-up" signInUrl="/sign-in" />
            ) : (
              <p className="text-sm text-gray-600">
                Clerk is not configured. Set `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and
                `CLERK_SECRET_KEY` to enable sign-up.
              </p>
            )}
          </div>
        </div>
      </section>
      <SiteFooter />
    </main>
  )
}
