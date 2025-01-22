import { PencilIcon } from '@heroicons/react/24/outline'

interface TopicInputProps {
  value: string
  onChange: (value: string) => void
}

export default function TopicInput({ value, onChange }: TopicInputProps) {
  return (
    <div className="bg-amber-50/50 dark:bg-amber-950/20 rounded-2xl p-5 border border-amber-200/40 dark:border-amber-700/30 backdrop-blur-sm">
      <div className="flex items-center mb-2">
        <PencilIcon className="h-4 w-4 text-amber-600 mr-2" />
        <label htmlFor="topic" className="block text-sm font-medium text-amber-700">
          What would you like to write about?
        </label>
      </div>
      <input
        type="text"
        id="topic"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 block w-full rounded-xl border-black/[0.08] dark:border-white/[0.08] shadow-sm focus:border-amber-500 focus:ring-amber-500 bg-white/70 dark:bg-gray-800/70 dark:text-gray-100 dark:placeholder-gray-500 backdrop-blur-sm"
        placeholder="Enter your topic..."
        required
      />
    </div>
  )
}
