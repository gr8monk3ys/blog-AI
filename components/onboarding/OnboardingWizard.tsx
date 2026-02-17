'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  SparklesIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  CheckIcon,
} from '@heroicons/react/24/outline'

import {
  WRITING_STYLES,
  TONE_KEYWORDS,
  type WritingStyle,
  type ToneKeyword,
} from '../../types/brand'
import {
  ONBOARDING_STEPS,
  FIRST_CONTENT_OPTIONS,
  TOPIC_SUGGESTIONS,
  type OnboardingFormData,
  type FirstContentType,
} from '../../types/onboarding'
import { markOnboardingComplete } from '../../lib/onboarding'

/* -------------------------------------------------------------------------- */
/*  Constants                                                                  */
/* -------------------------------------------------------------------------- */

const MAX_TONE_KEYWORDS = 5

const INITIAL_FORM_DATA: OnboardingFormData = {
  name: '',
  company: '',
  writingStyle: 'balanced',
  toneKeywords: [],
  sampleWriting: '',
  firstContentType: 'blog-post',
  topicSuggestion: TOPIC_SUGGESTIONS['blog-post'],
}

/* -------------------------------------------------------------------------- */
/*  Animation variants                                                         */
/* -------------------------------------------------------------------------- */

const slideVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 300 : -300,
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
  exit: (direction: number) => ({
    x: direction < 0 ? 300 : -300,
    opacity: 0,
  }),
}

/* -------------------------------------------------------------------------- */
/*  Props                                                                      */
/* -------------------------------------------------------------------------- */

interface OnboardingWizardProps {
  /** Pre-fill the name field (e.g. from Clerk user profile). */
  initialName?: string
}

/* -------------------------------------------------------------------------- */
/*  Component                                                                  */
/* -------------------------------------------------------------------------- */

export default function OnboardingWizard({
  initialName = '',
}: OnboardingWizardProps) {
  /* ---- state ---- */
  const [step, setStep] = useState(0)
  const [direction, setDirection] = useState(0)
  const [formData, setFormData] = useState<OnboardingFormData>({
    ...INITIAL_FORM_DATA,
    name: initialName,
  })
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  /* Focus the first interactive element on each step change. */
  const stepContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const timer = setTimeout(() => {
      const container = stepContainerRef.current
      if (!container) return
      const firstInput = container.querySelector<HTMLElement>(
        'input, select, textarea, button[data-autofocus]'
      )
      firstInput?.focus()
    }, 350) // Wait for framer-motion entry animation
    return () => clearTimeout(timer)
  }, [step])

  /* ---- navigation helpers ---- */

  const totalSteps = ONBOARDING_STEPS.length

  const goTo = useCallback(
    (target: number) => {
      if (target < 0 || target >= totalSteps) return
      setDirection(target > step ? 1 : -1)
      setStep(target)
    },
    [step, totalSteps]
  )

  const next = useCallback(() => goTo(step + 1), [goTo, step])
  const prev = useCallback(() => goTo(step - 1), [goTo, step])

  /* ---- field updaters ---- */

  const updateField = useCallback(
    <K extends keyof OnboardingFormData>(
      key: K,
      value: OnboardingFormData[K]
    ) => {
      setFormData((prev) => ({ ...prev, [key]: value }))
    },
    []
  )

  const toggleTone = useCallback(
    (keyword: ToneKeyword) => {
      setFormData((prev) => {
        const exists = prev.toneKeywords.includes(keyword)
        if (exists) {
          return {
            ...prev,
            toneKeywords: prev.toneKeywords.filter((k) => k !== keyword),
          }
        }
        if (prev.toneKeywords.length >= MAX_TONE_KEYWORDS) return prev
        return {
          ...prev,
          toneKeywords: [...prev.toneKeywords, keyword],
        }
      })
    },
    []
  )

  const selectContentType = useCallback(
    (type: FirstContentType) => {
      updateField('firstContentType', type)
      updateField('topicSuggestion', TOPIC_SUGGESTIONS[type])
    },
    [updateField]
  )

  /* ---- save brand profile on final step ---- */

  const saveBrandProfile = useCallback(async () => {
    // Only attempt save if user provided meaningful brand voice data.
    const hasBrandData =
      formData.toneKeywords.length > 0 || formData.sampleWriting.trim() !== ''

    if (!hasBrandData) return

    setSaving(true)
    setSaveError(null)

    try {
      const response = await fetch('/api/brand-profiles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.company
            ? `${formData.company} Voice`
            : `${formData.name || 'My'} Voice`,
          toneKeywords:
            formData.toneKeywords.length > 0
              ? formData.toneKeywords
              : ['professional'],
          writingStyle: formData.writingStyle,
          exampleContent: formData.sampleWriting || undefined,
        }),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(
          (data as Record<string, string>).error || 'Failed to save brand profile'
        )
      }
    } catch (err) {
      setSaveError(
        err instanceof Error ? err.message : 'Could not save brand profile.'
      )
    } finally {
      setSaving(false)
    }
  }, [formData])

  const handleFinish = useCallback(async () => {
    await saveBrandProfile()
    markOnboardingComplete()
  }, [saveBrandProfile])

  /* ---- keyboard navigation ---- */

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Do not intercept when an input/textarea is focused.
      const tag = (e.target as HTMLElement)?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

      if (e.key === 'ArrowRight') {
        e.preventDefault()
        next()
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault()
        prev()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [next, prev])

  /* -------------------------------------------------------------------------- */
  /*  Step renderers                                                             */
  /* -------------------------------------------------------------------------- */

  const renderWelcome = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-amber-100">
          <SparklesIcon className="h-7 w-7 text-amber-600" aria-hidden="true" />
        </div>
        <h2 className="mt-4 text-2xl font-semibold text-gray-900 font-serif sm:text-3xl">
          Welcome to Blog AI
        </h2>
        <p className="mt-2 text-sm text-gray-600 max-w-md mx-auto">
          Let us set up your workspace so every piece of content sounds like
          you. This takes about two minutes.
        </p>
      </div>

      <div className="max-w-sm mx-auto space-y-4">
        <div>
          <label
            htmlFor="onboarding-name"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Your name
          </label>
          <input
            id="onboarding-name"
            type="text"
            value={formData.name}
            onChange={(e) => updateField('name', e.target.value)}
            placeholder="Jane Smith"
            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
            autoComplete="name"
          />
        </div>

        <div>
          <label
            htmlFor="onboarding-company"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Company or brand
            <span className="text-gray-400 font-normal"> (optional)</span>
          </label>
          <input
            id="onboarding-company"
            type="text"
            value={formData.company}
            onChange={(e) => updateField('company', e.target.value)}
            placeholder="Acme Inc."
            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
            autoComplete="organization"
          />
        </div>
      </div>
    </div>
  )

  const renderBrandVoice = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-semibold text-gray-900 font-serif sm:text-3xl">
          Define your brand voice
        </h2>
        <p className="mt-2 text-sm text-gray-600 max-w-md mx-auto">
          Help us understand how you write so generated content matches your
          style from the start.
        </p>
      </div>

      {/* Writing style dropdown */}
      <div className="max-w-sm mx-auto">
        <label
          htmlFor="onboarding-writing-style"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Writing style
        </label>
        <select
          id="onboarding-writing-style"
          value={formData.writingStyle}
          onChange={(e) =>
            updateField('writingStyle', e.target.value as WritingStyle)
          }
          className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
        >
          {WRITING_STYLES.map((style) => (
            <option key={style.value} value={style.value}>
              {style.label} -- {style.description}
            </option>
          ))}
        </select>
      </div>

      {/* Tone keywords */}
      <div>
        <p className="text-sm font-medium text-gray-700 mb-2 text-center">
          Pick up to {MAX_TONE_KEYWORDS} tone keywords
        </p>
        <div
          className="flex flex-wrap justify-center gap-2"
          role="group"
          aria-label="Tone keywords"
        >
          {TONE_KEYWORDS.map((keyword) => {
            const selected = formData.toneKeywords.includes(keyword.value)
            const disabled =
              !selected && formData.toneKeywords.length >= MAX_TONE_KEYWORDS

            return (
              <button
                key={keyword.value}
                type="button"
                onClick={() => toggleTone(keyword.value)}
                disabled={disabled}
                aria-pressed={selected}
                className={`
                  inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-sm font-medium
                  transition-all focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2
                  ${
                    selected
                      ? 'bg-amber-600 text-white shadow-sm'
                      : disabled
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-gray-100 text-gray-700 hover:bg-amber-50 hover:text-amber-800'
                  }
                `}
              >
                {selected && (
                  <CheckIcon className="h-3.5 w-3.5" aria-hidden="true" />
                )}
                {keyword.label}
              </button>
            )
          })}
        </div>
        {formData.toneKeywords.length > 0 && (
          <p className="mt-2 text-xs text-center text-gray-500">
            {formData.toneKeywords.length}/{MAX_TONE_KEYWORDS} selected
          </p>
        )}
      </div>

      {/* Sample writing */}
      <div className="max-w-lg mx-auto">
        <label
          htmlFor="onboarding-sample"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Paste a sample of your writing
          <span className="text-gray-400 font-normal"> (optional)</span>
        </label>
        <p className="text-xs text-gray-500 mb-2">
          A paragraph or two is enough. We use this to calibrate tone and
          vocabulary.
        </p>
        <textarea
          id="onboarding-sample"
          value={formData.sampleWriting}
          onChange={(e) => updateField('sampleWriting', e.target.value)}
          rows={4}
          placeholder="Paste a paragraph that represents how you write..."
          className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
        />
      </div>
    </div>
  )

  const renderFirstGeneration = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-semibold text-gray-900 font-serif sm:text-3xl">
          What would you like to create first?
        </h2>
        <p className="mt-2 text-sm text-gray-600 max-w-md mx-auto">
          Choose a content type and we will pre-fill a topic to get you
          started.
        </p>
      </div>

      {/* Content type cards */}
      <div
        className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto"
        role="radiogroup"
        aria-label="Content type"
      >
        {FIRST_CONTENT_OPTIONS.map((option) => {
          const selected = formData.firstContentType === option.value
          return (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => selectContentType(option.value)}
              className={`
                relative rounded-xl p-5 text-left transition-all
                focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2
                ${
                  selected
                    ? 'glass-card ring-2 ring-amber-500 shadow-lg'
                    : 'glass-card hover:shadow-md'
                }
              `}
            >
              {selected && (
                <span className="absolute top-3 right-3 flex h-5 w-5 items-center justify-center rounded-full bg-amber-600">
                  <CheckIcon
                    className="h-3 w-3 text-white"
                    aria-hidden="true"
                  />
                </span>
              )}
              <p className="text-sm font-semibold text-gray-900">
                {option.label}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                {option.description}
              </p>
            </button>
          )
        })}
      </div>

      {/* Topic suggestion */}
      <div className="max-w-lg mx-auto">
        <label
          htmlFor="onboarding-topic"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Suggested topic
        </label>
        <p className="text-xs text-gray-500 mb-2">
          You can change this later or start from scratch on the dashboard.
        </p>
        <input
          id="onboarding-topic"
          type="text"
          value={formData.topicSuggestion}
          onChange={(e) => updateField('topicSuggestion', e.target.value)}
          className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
        />
      </div>
    </div>
  )

  const renderDone = () => (
    <div className="space-y-8 text-center">
      <div>
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
          <CheckIcon className="h-8 w-8 text-green-600" aria-hidden="true" />
        </div>
        <h2 className="mt-4 text-2xl font-semibold text-gray-900 font-serif sm:text-3xl">
          You are all set{formData.name ? `, ${formData.name}` : ''}!
        </h2>
        <p className="mt-2 text-sm text-gray-600 max-w-md mx-auto">
          Your workspace is ready. Start creating content that sounds like
          you.
        </p>

        {saveError && (
          <div className="mt-4 mx-auto max-w-sm p-3 rounded-lg bg-red-50 border border-red-100 text-sm text-red-700">
            {saveError}
            <button
              type="button"
              className="ml-2 text-xs underline hover:text-red-900"
              onClick={() => {
                setSaveError(null)
                saveBrandProfile()
              }}
            >
              Retry
            </button>
          </div>
        )}
      </div>

      <div className="max-w-sm mx-auto grid gap-3">
        <a
          href="/"
          className="flex items-center justify-center gap-2 rounded-lg bg-amber-600 px-5 py-3 text-sm font-medium text-white hover:bg-amber-700 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
          data-autofocus="true"
        >
          <SparklesIcon className="h-4 w-4" aria-hidden="true" />
          Go to Dashboard
        </a>
        <a
          href="/templates"
          className="flex items-center justify-center rounded-lg border border-amber-200 bg-amber-50/70 px-5 py-3 text-sm font-medium text-amber-800 hover:bg-amber-100 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
        >
          Browse Templates
        </a>
        <a
          href="/brand"
          className="flex items-center justify-center rounded-lg border border-gray-200 bg-white px-5 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
        >
          Refine Brand Settings
        </a>
      </div>
    </div>
  )

  const STEP_RENDERERS = [
    renderWelcome,
    renderBrandVoice,
    renderFirstGeneration,
    renderDone,
  ]

  /* -------------------------------------------------------------------------- */
  /*  Progress indicator                                                         */
  /* -------------------------------------------------------------------------- */

  const renderProgress = () => (
    <nav aria-label="Onboarding progress" className="mb-8">
      {/* Desktop: horizontal stepper */}
      <ol className="hidden sm:flex items-center justify-center gap-2">
        {ONBOARDING_STEPS.map((s, i) => {
          const isComplete = i < step
          const isCurrent = i === step
          return (
            <li key={s.id} className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => goTo(i)}
                aria-current={isCurrent ? 'step' : undefined}
                aria-label={`${s.title}${isComplete ? ' (completed)' : ''}${isCurrent ? ' (current)' : ''}`}
                className={`
                  flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium transition-all
                  focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2
                  ${
                    isCurrent
                      ? 'bg-amber-600 text-white shadow-sm'
                      : isComplete
                        ? 'bg-amber-100 text-amber-800 hover:bg-amber-200'
                        : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                  }
                `}
              >
                {isComplete ? (
                  <CheckIcon className="h-3.5 w-3.5" aria-hidden="true" />
                ) : (
                  <span
                    className={`flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold
                    ${isCurrent ? 'bg-white/20 text-white' : 'bg-white text-gray-500'}
                  `}
                  >
                    {i + 1}
                  </span>
                )}
                {s.title}
              </button>
              {i < ONBOARDING_STEPS.length - 1 && (
                <div
                  className={`h-px w-8 ${isComplete ? 'bg-amber-300' : 'bg-gray-200'}`}
                  aria-hidden="true"
                />
              )}
            </li>
          )
        })}
      </ol>

      {/* Mobile: dots + label */}
      <div className="sm:hidden text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          {ONBOARDING_STEPS.map((s, i) => (
            <button
              key={s.id}
              type="button"
              onClick={() => goTo(i)}
              aria-label={`Go to step ${i + 1}: ${s.title}`}
              aria-current={i === step ? 'step' : undefined}
              className={`
                h-2.5 rounded-full transition-all focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2
                ${
                  i === step
                    ? 'w-8 bg-amber-600'
                    : i < step
                      ? 'w-2.5 bg-amber-300'
                      : 'w-2.5 bg-gray-200'
                }
              `}
            />
          ))}
        </div>
        <p className="text-xs text-gray-500">
          Step {step + 1} of {totalSteps}:{' '}
          <span className="font-medium text-gray-700">
            {ONBOARDING_STEPS[step]?.title}
          </span>
        </p>
      </div>
    </nav>
  )

  /* -------------------------------------------------------------------------- */
  /*  Navigation bar                                                             */
  /* -------------------------------------------------------------------------- */

  const isFirstStep = step === 0
  const isLastStep = step === totalSteps - 1

  const renderNavigation = () => {
    if (isLastStep) return null

    return (
      <div className="mt-8 flex items-center justify-between">
        <button
          type="button"
          onClick={prev}
          disabled={isFirstStep}
          className={`
            inline-flex items-center gap-1.5 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors
            focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2
            ${
              isFirstStep
                ? 'text-gray-300 cursor-not-allowed'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }
          `}
          aria-label="Previous step"
        >
          <ArrowLeftIcon className="h-4 w-4" aria-hidden="true" />
          Back
        </button>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={next}
            className="text-sm text-gray-400 hover:text-gray-600 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 rounded px-2 py-1"
          >
            Skip
          </button>

          <button
            type="button"
            onClick={async () => {
              if (step === totalSteps - 2) {
                // Moving to final step -- save and mark complete.
                await handleFinish()
              }
              next()
            }}
            disabled={saving}
            className="inline-flex items-center gap-1.5 rounded-lg bg-amber-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-amber-700 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            aria-label={step === totalSteps - 2 ? 'Finish setup' : 'Next step'}
          >
            {saving ? (
              'Saving...'
            ) : step === totalSteps - 2 ? (
              <>
                Finish
                <CheckIcon className="h-4 w-4" aria-hidden="true" />
              </>
            ) : (
              <>
                Next
                <ArrowRightIcon className="h-4 w-4" aria-hidden="true" />
              </>
            )}
          </button>
        </div>
      </div>
    )
  }

  /* -------------------------------------------------------------------------- */
  /*  Render                                                                     */
  /* -------------------------------------------------------------------------- */

  return (
    <div className="w-full max-w-2xl mx-auto">
      {renderProgress()}

      <div
        ref={stepContainerRef}
        className="relative overflow-hidden rounded-2xl glass-card p-6 sm:p-10"
        role="region"
        aria-live="polite"
        aria-label={`Step ${step + 1}: ${ONBOARDING_STEPS[step]?.title}`}
      >
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={step}
            custom={direction}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ type: 'tween', ease: 'easeInOut', duration: 0.3 }}
          >
            {STEP_RENDERERS[step]?.()}
          </motion.div>
        </AnimatePresence>
      </div>

      {renderNavigation()}
    </div>
  )
}
