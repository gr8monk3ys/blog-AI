/**
 * Tool Page Components
 *
 * Components for the individual tool page at /tools/[slug]
 */

export { default as ToastNotification } from './ToastNotification'
export { default as ToolNotFound } from './ToolNotFound'
export { default as ToolPageHeader } from './ToolPageHeader'
export { default as ToolHeaderSection } from './ToolHeaderSection'
export { default as AdvancedOptions } from './AdvancedOptions'
export { default as ToolInputForm } from './ToolInputForm'
export { default as ToolOutput } from './ToolOutput'
export { default as ToolSidebar } from './ToolSidebar'

// Utilities
export {
  getInputLabel,
  getInputPlaceholder,
  generateMockScore,
  generateMockOutput,
  parseKeywords,
  copyToClipboard,
} from './utils'

// Types
export type {
  ToastState,
  FormState,
  OutputState,
  ToolPageState,
  ToneOption,
} from './types'

export { TONE_OPTIONS } from './types'
