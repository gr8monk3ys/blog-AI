'use client'

import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'

const LAST_UPDATED = 'February 22, 2026'

export default function TermsPageClient(): React.ReactElement {
  return (
    <div className="min-h-screen flex flex-col">
      <SiteHeader />

      <main className="flex-1 py-16 sm:py-20">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl sm:text-4xl font-semibold text-gray-900 font-serif">
            Terms of Service
          </h1>
          <p className="mt-2 text-sm text-gray-500">
            Last updated: {LAST_UPDATED}
          </p>

          <div className="mt-10 prose prose-gray max-w-none prose-headings:font-serif prose-headings:font-semibold prose-a:text-amber-600 hover:prose-a:text-amber-700">
            <p>
              These Terms of Service (&quot;Terms&quot;) govern your access to
              and use of Blog AI (&quot;we&quot;, &quot;our&quot;, or
              &quot;us&quot;), including our website, APIs, and AI content
              generation services (collectively, the &quot;Service&quot;).
              By accessing or using the Service, you agree to be bound by
              these Terms.
            </p>

            <h2>1. Acceptance of Terms</h2>
            <p>
              By creating an account or using the Service, you confirm that
              you are at least 16 years of age and agree to comply with these
              Terms. If you are using the Service on behalf of an organization,
              you represent that you have authority to bind that organization
              to these Terms.
            </p>

            <h2>2. Description of Service</h2>
            <p>
              Blog AI is an AI-powered content generation platform that helps
              users create blog posts, articles, marketing copy, and other
              written content. The Service uses third-party AI providers
              (including OpenAI, Anthropic, and Google) to generate content
              based on your prompts and instructions.
            </p>

            <h2>3. Accounts</h2>
            <p>
              You are responsible for maintaining the confidentiality of your
              account credentials and for all activity that occurs under your
              account. You must provide accurate and complete information when
              creating your account and keep it up to date.
            </p>
            <p>
              We reserve the right to suspend or terminate accounts that
              violate these Terms, engage in fraudulent activity, or remain
              inactive for an extended period.
            </p>

            <h2>4. Subscription &amp; Billing</h2>
            <p>
              Blog AI offers free and paid subscription tiers. Paid
              subscriptions are billed on a monthly or annual basis through
              Stripe. By subscribing to a paid plan, you authorize us to
              charge your payment method on a recurring basis.
            </p>
            <ul>
              <li>
                You may cancel your subscription at any time through the
                customer portal. Cancellation takes effect at the end of the
                current billing period.
              </li>
              <li>
                We do not offer refunds for partial billing periods unless
                required by applicable law.
              </li>
              <li>
                We reserve the right to change pricing with 30 days&apos;
                notice. Existing subscribers will be notified before price
                changes take effect.
              </li>
            </ul>

            <h2>5. Acceptable Use</h2>
            <p>You agree not to use the Service to:</p>
            <ul>
              <li>Generate content that is illegal, harmful, or violates the rights of others</li>
              <li>Produce spam, misleading content, or impersonate others</li>
              <li>Attempt to circumvent usage limits or rate limiting</li>
              <li>Reverse-engineer, decompile, or extract source code from the Service</li>
              <li>Use automated tools to scrape or overload the Service</li>
              <li>Generate content intended to harass, defame, or threaten</li>
            </ul>

            <h2>6. Content Ownership &amp; License</h2>
            <h3>Your Content</h3>
            <p>
              You retain ownership of the prompts and instructions you provide
              to the Service. You also own the AI-generated output created
              through your use of the Service, subject to the terms of the
              underlying AI providers.
            </p>

            <h3>Our License</h3>
            <p>
              By using the Service, you grant us a limited license to process
              your prompts and store your generated content as necessary to
              provide the Service. We do not claim ownership of your content
              and will not use it for purposes other than providing the
              Service.
            </p>

            <h3>AI-Generated Content Disclaimer</h3>
            <p>
              Content generated by AI may contain inaccuracies, biases, or
              errors. You are solely responsible for reviewing, editing, and
              verifying all AI-generated content before publication or use.
              We do not guarantee the accuracy, originality, or fitness for
              purpose of generated content.
            </p>

            <h2>7. Intellectual Property</h2>
            <p>
              The Service, including its design, features, code, and branding,
              is owned by Blog AI and protected by intellectual property laws.
              You may not copy, modify, or distribute any part of the Service
              without our written permission.
            </p>

            <h2>8. Third-Party Services</h2>
            <p>
              The Service integrates with third-party providers including
              OpenAI, Anthropic, Google, Clerk, and Stripe. Your use of the
              Service may be subject to the terms and policies of these
              providers. We are not responsible for the practices or
              availability of third-party services.
            </p>

            <h2>9. Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by law, Blog AI shall not be
              liable for any indirect, incidental, special, consequential, or
              punitive damages arising from your use of the Service, including
              but not limited to loss of profits, data, or business
              opportunities.
            </p>
            <p>
              Our total liability for any claims arising from your use of the
              Service is limited to the amount you paid us in the 12 months
              preceding the claim.
            </p>

            <h2>10. Disclaimer of Warranties</h2>
            <p>
              The Service is provided &quot;as is&quot; and &quot;as
              available&quot; without warranties of any kind, either express
              or implied. We do not warrant that the Service will be
              uninterrupted, error-free, or free of harmful components.
            </p>

            <h2>11. Termination</h2>
            <p>
              Either party may terminate this agreement at any time. You may
              stop using the Service and delete your account. We may suspend
              or terminate your access if you violate these Terms or if we
              discontinue the Service.
            </p>
            <p>
              Upon termination, your right to use the Service ceases
              immediately. We may retain certain data as required by law or
              for legitimate business purposes.
            </p>

            <h2>12. Changes to Terms</h2>
            <p>
              We may update these Terms from time to time. Material changes
              will be communicated via email or a prominent notice on the
              Service. Continued use after changes take effect constitutes
              acceptance of the updated Terms.
            </p>

            <h2>13. Governing Law</h2>
            <p>
              These Terms are governed by and construed in accordance with the
              laws of the State of California, United States, without regard
              to conflict of law principles.
            </p>

            <h2>14. Contact Us</h2>
            <p>
              If you have questions about these Terms, please contact us at{' '}
              <a href="mailto:legal@blogai.com">legal@blogai.com</a>.
            </p>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  )
}
