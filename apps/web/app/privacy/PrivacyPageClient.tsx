'use client'

import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'

const LAST_UPDATED = 'February 22, 2026'

export default function PrivacyPageClient(): React.ReactElement {
  return (
    <div className="min-h-screen flex flex-col">
      <SiteHeader />

      <main className="flex-1 py-16 sm:py-20">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl sm:text-4xl font-semibold text-gray-900 font-serif">
            Privacy Policy
          </h1>
          <p className="mt-2 text-sm text-gray-500">
            Last updated: {LAST_UPDATED}
          </p>

          <div className="mt-10 prose prose-gray max-w-none prose-headings:font-serif prose-headings:font-semibold prose-a:text-amber-600 hover:prose-a:text-amber-700">
            <p>
              Blog AI (&quot;we&quot;, &quot;our&quot;, or &quot;us&quot;) is
              committed to protecting your privacy. This Privacy Policy explains
              how we collect, use, disclose, and safeguard your information when
              you use our AI content generation platform.
            </p>

            <h2>1. Information We Collect</h2>

            <h3>Account Information</h3>
            <p>
              When you create an account through our authentication provider
              (Clerk), we collect your name, email address, and profile
              information. We do not store passwords directly — authentication
              is handled by Clerk&apos;s secure infrastructure.
            </p>

            <h3>Payment Information</h3>
            <p>
              Payment processing is handled by Stripe. We do not store credit
              card numbers or full payment details on our servers. We retain
              your Stripe customer ID and subscription status to manage your
              account.
            </p>

            <h3>Content You Create</h3>
            <p>
              We store the content you generate using our platform, including
              blog posts, articles, and other text. This content is associated
              with your account to provide features like content history and
              analytics.
            </p>

            <h3>Usage Data</h3>
            <p>
              We collect information about how you use the platform, including
              generation counts, feature usage, and interaction patterns. This
              helps us improve the service and enforce usage limits based on
              your subscription tier.
            </p>

            <h3>Technical Data</h3>
            <p>
              We automatically collect certain technical information including
              your IP address, browser type, device information, and error logs
              (via Sentry) to maintain and improve our service.
            </p>

            <h2>2. How We Use Your Information</h2>
            <ul>
              <li>Provide and maintain the Blog AI platform</li>
              <li>Process your content generation requests</li>
              <li>Manage your subscription and billing</li>
              <li>Send service-related communications</li>
              <li>Monitor and improve platform performance</li>
              <li>Detect and prevent fraud or abuse</li>
              <li>Comply with legal obligations</li>
            </ul>

            <h2>3. AI Content Processing</h2>
            <p>
              Your content prompts are sent to third-party AI providers
              (OpenAI, Anthropic, and/or Google) for text generation. These
              providers process your prompts according to their respective
              privacy policies. We do not use your content to train AI models.
            </p>

            <h2>4. Data Sharing</h2>
            <p>We share your information only with:</p>
            <ul>
              <li>
                <strong>Authentication provider (Clerk)</strong> — for account
                management and sign-in
              </li>
              <li>
                <strong>Payment processor (Stripe)</strong> — for subscription
                billing
              </li>
              <li>
                <strong>AI providers (OpenAI, Anthropic, Google)</strong> — for
                content generation
              </li>
              <li>
                <strong>Error tracking (Sentry)</strong> — for monitoring and
                debugging
              </li>
            </ul>
            <p>
              We do not sell your personal information to third parties.
            </p>

            <h2>5. Cookies &amp; Tracking</h2>
            <p>
              We use essential cookies for authentication and session
              management. We do not use third-party advertising cookies. Our
              authentication provider may set additional cookies as part of the
              sign-in process.
            </p>

            <h2>6. Data Security</h2>
            <p>
              We implement industry-standard security measures including
              encrypted connections (HTTPS), parameterized database queries,
              input validation, and secure API key management. However, no
              method of transmission over the Internet is 100% secure.
            </p>

            <h2>7. Data Retention</h2>
            <p>
              We retain your account information and generated content for as
              long as your account is active. You may request deletion of your
              account and associated data at any time by contacting us. Usage
              logs are retained for up to 90 days.
            </p>

            <h2>8. Your Rights</h2>
            <p>Depending on your jurisdiction, you may have the right to:</p>
            <ul>
              <li>Access the personal data we hold about you</li>
              <li>Request correction of inaccurate data</li>
              <li>Request deletion of your data</li>
              <li>Export your data in a portable format</li>
              <li>Opt out of non-essential data processing</li>
            </ul>
            <p>
              To exercise any of these rights, please contact us at the email
              address below.
            </p>

            <h2>9. Children&apos;s Privacy</h2>
            <p>
              Blog AI is not intended for use by individuals under 16 years of
              age. We do not knowingly collect personal information from
              children.
            </p>

            <h2>10. Changes to This Policy</h2>
            <p>
              We may update this Privacy Policy from time to time. We will
              notify you of material changes by posting the updated policy on
              this page and updating the &quot;Last updated&quot; date.
            </p>

            <h2>11. Contact Us</h2>
            <p>
              If you have questions about this Privacy Policy or our data
              practices, please contact us at{' '}
              <a href="mailto:privacy@blogai.com">privacy@blogai.com</a>.
            </p>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  )
}
