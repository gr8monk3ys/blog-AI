'use client'

import { Fragment, useState } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { XMarkIcon, BookmarkIcon } from '@heroicons/react/24/outline'
import { TemplateCategory, TEMPLATE_CATEGORIES } from '../../types/templates'

interface SaveTemplateModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: SaveTemplateData) => Promise<void>
  toolId: string
  toolName: string
  presetInputs: Record<string, unknown>
}

interface SaveTemplateData {
  name: string
  description: string
  category: TemplateCategory
  tags: string[]
  isPublic: boolean
}

export default function SaveTemplateModal({
  isOpen,
  onClose,
  onSave,
  toolId,
  toolName,
  presetInputs,
}: SaveTemplateModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState<TemplateCategory>('content')
  const [tagsInput, setTagsInput] = useState('')
  const [isPublic, setIsPublic] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError('Template name is required')
      return
    }

    setSaving(true)
    try {
      const tags = tagsInput
        .split(',')
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0)

      await onSave({
        name: name.trim(),
        description: description.trim(),
        category,
        tags,
        isPublic,
      })

      // Reset form and close
      setName('')
      setDescription('')
      setCategory('content')
      setTagsInput('')
      setIsPublic(true)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save template')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-semibold leading-6 text-gray-900 flex items-center gap-2"
                  >
                    <BookmarkIcon className="w-5 h-5 text-amber-600" />
                    Save as Template
                  </Dialog.Title>
                  <button
                    type="button"
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </button>
                </div>

                <p className="text-sm text-gray-500 mb-4">
                  Save your current settings for &quot;{toolName}&quot; as a reusable template.
                </p>

                {error && (
                  <div className="mb-4 p-3 rounded-lg bg-red-50 text-sm text-red-600 border border-red-100">
                    {error}
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label
                      htmlFor="template-name"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Template Name *
                    </label>
                    <input
                      type="text"
                      id="template-name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g., SaaS Product Launch"
                      className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
                      required
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="template-description"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Description
                    </label>
                    <textarea
                      id="template-description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Describe what this template is for..."
                      rows={3}
                      className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="template-category"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Category
                    </label>
                    <select
                      id="template-category"
                      value={category}
                      onChange={(e) => setCategory(e.target.value as TemplateCategory)}
                      className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
                    >
                      {Object.entries(TEMPLATE_CATEGORIES).map(([key, info]) => (
                        <option key={key} value={key}>
                          {info.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label
                      htmlFor="template-tags"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Tags (comma-separated)
                    </label>
                    <input
                      type="text"
                      id="template-tags"
                      value={tagsInput}
                      onChange={(e) => setTagsInput(e.target.value)}
                      placeholder="e.g., landing-page, conversion, copy"
                      className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
                    />
                  </div>

                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="template-public"
                      checked={isPublic}
                      onChange={(e) => setIsPublic(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
                    />
                    <label
                      htmlFor="template-public"
                      className="text-sm text-gray-700"
                    >
                      Make this template public
                    </label>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                    <p className="text-xs text-gray-500 mb-2">
                      Preset inputs to be saved:
                    </p>
                    <pre className="text-xs text-gray-600 overflow-x-auto max-h-24">
                      {JSON.stringify(presetInputs, null, 2)}
                    </pre>
                  </div>

                  <div className="flex justify-end gap-3 pt-4">
                    <button
                      type="button"
                      onClick={onClose}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={saving || !name.trim()}
                      className="px-4 py-2 text-sm font-medium text-white bg-amber-600 rounded-lg hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {saving ? 'Saving...' : 'Save Template'}
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}
