'use client'

import { EVENT_TYPE_GROUPS, type WebhookEventType } from '../../../../types/webhooks'

interface EventTypeSelectorProps {
  selected: WebhookEventType[]
  onChange: (types: WebhookEventType[]) => void
}

export default function EventTypeSelector({ selected, onChange }: EventTypeSelectorProps) {
  function toggle(type: WebhookEventType) {
    if (selected.includes(type)) {
      onChange(selected.filter((t) => t !== type))
    } else {
      onChange([...selected, type])
    }
  }

  function toggleGroup(types: WebhookEventType[]) {
    const allSelected = types.every((t) => selected.includes(t))
    if (allSelected) {
      onChange(selected.filter((t) => !types.includes(t)))
    } else {
      const merged = new Set([...selected, ...types])
      onChange(Array.from(merged))
    }
  }

  return (
    <div className="space-y-4">
      {Object.entries(EVENT_TYPE_GROUPS).map(([key, group]) => {
        const allSelected = group.types.every((t) => selected.includes(t))
        return (
          <div key={key}>
            <div className="flex items-center gap-2 mb-2">
              <label className="inline-flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={() => toggleGroup(group.types)}
                  className="rounded border-gray-300 text-amber-600 focus:ring-amber-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{group.label}</span>
              </label>
            </div>
            <div className="ml-6 space-y-1.5">
              {group.types.map((type) => (
                <label key={type} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selected.includes(type)}
                    onChange={() => toggle(type)}
                    className="rounded border-gray-300 text-amber-600 focus:ring-amber-500"
                  />
                  <code className="text-xs font-mono text-gray-600 dark:text-gray-400">{type}</code>
                </label>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
