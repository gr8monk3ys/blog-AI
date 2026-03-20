import type { BlogGenerationOptions } from '../../types/blog'
import type { LlmProviderType } from '../../types/llm'

interface FormFieldsProps {
  keywords: string
  onKeywordsChange: (value: string) => void
  tone: BlogGenerationOptions['tone']
  onToneChange: (value: BlogGenerationOptions['tone']) => void
  providerType: LlmProviderType
  onProviderChange: (value: LlmProviderType) => void
  availableProviders: LlmProviderType[]
}

export default function FormFields({
  keywords,
  onKeywordsChange,
  tone,
  onToneChange,
  providerType,
  onProviderChange,
  availableProviders,
}: FormFieldsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div>
        <label htmlFor="keywords" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Keywords (comma separated)
        </label>
        <input
          type="text"
          id="keywords"
          value={keywords}
          onChange={(e) => onKeywordsChange(e.target.value)}
          className="mt-1 block w-full rounded-xl border-black/[0.08] dark:border-white/[0.08] shadow-sm focus:border-amber-500 focus:ring-amber-500 bg-white/70 dark:bg-gray-800/70 dark:text-gray-100 dark:placeholder-gray-500 backdrop-blur-sm"
          placeholder="SEO, marketing, content..."
        />
      </div>

      <div>
        <label htmlFor="tone" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Tone
        </label>
        <select
          id="tone"
          value={tone}
          onChange={(e) => onToneChange(e.target.value as BlogGenerationOptions['tone'])}
          className="mt-1 block w-full rounded-xl border-black/[0.08] dark:border-white/[0.08] shadow-sm focus:border-amber-500 focus:ring-amber-500 bg-white/70 dark:bg-gray-800/70 dark:text-gray-100 backdrop-blur-sm"
        >
          <option value="informative">Informative</option>
          <option value="conversational">Conversational</option>
          <option value="professional">Professional</option>
          <option value="friendly">Friendly</option>
          <option value="authoritative">Authoritative</option>
          <option value="technical">Technical</option>
        </select>
      </div>

      <div>
        <label htmlFor="provider" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Model Provider
        </label>
        <select
          id="provider"
          value={providerType}
          onChange={(e) => onProviderChange(e.target.value as LlmProviderType)}
          className="mt-1 block w-full rounded-xl border-black/[0.08] dark:border-white/[0.08] shadow-sm focus:border-amber-500 focus:ring-amber-500 bg-white/70 dark:bg-gray-800/70 dark:text-gray-100 backdrop-blur-sm"
          disabled={availableProviders.length <= 1}
        >
          {availableProviders.map((p) => (
            <option key={p} value={p}>
              {p === 'openai' ? 'OpenAI' : p === 'anthropic' ? 'Anthropic' : 'Gemini'}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
