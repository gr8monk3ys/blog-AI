/**
 * Types for webhook management.
 *
 * Mirrors backend responses from:
 * - GET/POST /api/v1/webhooks
 * - PATCH/DELETE /api/v1/webhooks/:id
 * - POST /api/v1/webhooks/test
 * - GET /api/v1/webhooks/events/types
 */

export type WebhookEventType =
  | 'content.generated'
  | 'content.published'
  | 'batch.started'
  | 'batch.progress'
  | 'batch.completed'
  | 'batch.failed'
  | 'quota.warning'
  | 'quota.exceeded'
  | 'test'

export const EVENT_TYPE_GROUPS: Record<string, { label: string; types: WebhookEventType[] }> = {
  content: {
    label: 'Content',
    types: ['content.generated', 'content.published'],
  },
  batch: {
    label: 'Batch',
    types: ['batch.started', 'batch.progress', 'batch.completed', 'batch.failed'],
  },
  quota: {
    label: 'Quota',
    types: ['quota.warning', 'quota.exceeded'],
  },
  other: {
    label: 'Other',
    types: ['test'],
  },
}

export const EVENT_TYPE_DESCRIPTIONS: Record<WebhookEventType, string> = {
  'content.generated': 'Fires when content generation completes',
  'content.published': 'Fires when content is published',
  'batch.started': 'Fires when a batch job starts processing',
  'batch.progress': 'Fires periodically with batch progress updates',
  'batch.completed': 'Fires when a batch job completes successfully',
  'batch.failed': 'Fires when a batch job fails',
  'quota.warning': 'Fires when usage reaches 80% of quota limit',
  'quota.exceeded': 'Fires when quota is exceeded',
  'test': 'Test event for verifying webhook delivery',
}

export interface WebhookSubscription {
  id: string
  user_id: string
  target_url: string
  event_types: WebhookEventType[]
  secret?: string | null
  is_active: boolean
  description?: string | null
  metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
  total_deliveries: number
  successful_deliveries: number
  failed_deliveries: number
  last_delivery_at?: string | null
  last_error?: string | null
}

export interface WebhookSubscriptionCreate {
  target_url: string
  event_types: WebhookEventType[]
  secret?: string
  description?: string
}

export interface WebhookSubscriptionUpdate {
  target_url?: string
  event_types?: WebhookEventType[]
  secret?: string
  is_active?: boolean
  description?: string
}

export interface WebhookTestRequest {
  subscription_id?: string
  target_url?: string
  event_type?: WebhookEventType
}

export interface WebhookTestResponse {
  success: boolean
  status_code?: number
  response_time_ms?: number
  error?: string
}

export interface WebhookEventTypeInfo {
  event_type: WebhookEventType
  description: string
  data_fields: string[]
}
