# Technical Architecture: Tier 4 & Tier 5 Features

This document provides detailed technical architecture for Blog AI's Tier 4 (Competitive Parity) and Tier 5 (Wild Card) features.

---

## Table of Contents

1. [F11: Browser Extension](#f11-browser-extension)
2. [F12: Team Collaboration](#f12-team-collaboration)
3. [F13: Additional Publishing Integrations](#f13-additional-publishing-integrations)
4. [F14: Content Marketplace](#f14-content-marketplace)
5. [F15: Humanizer Pro](#f15-humanizer-pro-ai-detection-bypass)

---

## F11: Browser Extension

### Overview

A Chrome/Firefox browser extension enabling content generation directly within social platforms and content management systems.

### Architecture Diagram

```
+------------------------------------------------------------------+
|                     Browser Extension                              |
+------------------------------------------------------------------+
|  +------------------+  +------------------+  +------------------+  |
|  |   Popup UI       |  |  Content Script  |  | Background Worker|  |
|  |   (React)        |  |  (Site-specific) |  | (Service Worker) |  |
|  +--------+---------+  +--------+---------+  +--------+---------+  |
|           |                     |                     |            |
|           +----------+----------+----------+----------+            |
|                      |                     |                       |
+----------------------|---------------------|------------------------+
                       |                     |
                       v                     v
              +------------------+  +------------------+
              |   Blog AI API    |  |  OAuth Providers |
              |   (FastAPI)      |  |  (Google, etc.)  |
              +------------------+  +------------------+
```

### Extension Components (Manifest V3)

```json
{
  "manifest_version": 3,
  "name": "Blog AI Content Generator",
  "version": "1.0.0",
  "permissions": [
    "storage",
    "activeTab",
    "contextMenus",
    "identity"
  ],
  "host_permissions": [
    "https://www.linkedin.com/*",
    "https://medium.com/*",
    "https://twitter.com/*",
    "https://x.com/*",
    "https://api.blogai.com/*"
  ],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "content_scripts": [
    {
      "matches": ["https://www.linkedin.com/*"],
      "js": ["content-scripts/linkedin.js"],
      "css": ["content-scripts/inject.css"]
    },
    {
      "matches": ["https://medium.com/*"],
      "js": ["content-scripts/medium.js"],
      "css": ["content-scripts/inject.css"]
    },
    {
      "matches": ["https://twitter.com/*", "https://x.com/*"],
      "js": ["content-scripts/twitter.js"],
      "css": ["content-scripts/inject.css"]
    }
  ],
  "action": {
    "default_popup": "popup/index.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  }
}
```

### Data Models

```typescript
// extension/types/extension.ts

interface ExtensionUser {
  id: string
  email: string
  apiKey: string
  subscription: 'free' | 'pro' | 'team'
  tokenBalance: number
}

interface ContentInjectionRequest {
  platform: 'linkedin' | 'medium' | 'twitter' | 'generic'
  contentType: 'post' | 'article' | 'thread' | 'comment'
  context: {
    pageUrl: string
    selectedText?: string
    targetElement?: string
  }
  generationParams: {
    topic?: string
    tone?: string
    length?: 'short' | 'medium' | 'long'
  }
}

interface ContentInjectionResponse {
  success: boolean
  content: string
  metadata: {
    tokensUsed: number
    generationTimeMs: number
  }
}

interface ExtensionSettings {
  defaultTone: string
  defaultLength: string
  autoSuggest: boolean
  keyboardShortcuts: Record<string, string>
  enabledPlatforms: string[]
}
```

### API Endpoints

```yaml
# Extension-specific endpoints added to FastAPI

POST /api/v1/extension/generate:
  description: Generate content for browser extension
  authentication: API Key (X-API-Key header)
  request:
    platform: string
    contentType: string
    context: object
    generationParams: object
  response:
    content: string
    metadata: object

POST /api/v1/extension/auth/link:
  description: Link extension to user account
  request:
    linkCode: string (6-digit code from web app)
  response:
    apiKey: string
    user: ExtensionUser

GET /api/v1/extension/user:
  description: Get current user info and token balance
  authentication: API Key
  response:
    user: ExtensionUser

POST /api/v1/extension/context-menu:
  description: Handle context menu actions
  request:
    action: string
    selectionText: string
    pageUrl: string
  response:
    content: string
```

### Database Schema

```sql
-- Migration: 010_create_extension_sessions.sql

CREATE TABLE extension_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    api_key_hash TEXT NOT NULL UNIQUE,
    device_info JSONB,
    last_active_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ
);

CREATE TABLE extension_link_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_extension_sessions_user ON extension_sessions(user_id);
CREATE INDEX idx_extension_sessions_api_key ON extension_sessions(api_key_hash);
CREATE INDEX idx_extension_link_codes_code ON extension_link_codes(code);
```

### Authentication Flow

```
1. User clicks "Link Extension" in Blog AI web app
2. Web app generates 6-digit link code (valid 5 minutes)
3. User enters code in extension popup
4. Extension calls /api/v1/extension/auth/link
5. Backend validates code, creates extension_session
6. Returns API key to extension (stored in chrome.storage.local)
7. All subsequent requests use API key in X-API-Key header
```

### Site-Specific Content Injection

```typescript
// content-scripts/linkedin.ts

class LinkedInInjector {
  private buttonContainerSelector = '.share-box-feed-entry__trigger'
  private editorSelector = '.ql-editor'

  inject(): void {
    this.observeDOM()
    this.addGenerateButton()
  }

  private addGenerateButton(): void {
    const container = document.querySelector(this.buttonContainerSelector)
    if (!container) return

    const button = this.createButton()
    container.appendChild(button)
  }

  private async handleGenerate(): Promise<void> {
    const editor = document.querySelector(this.editorSelector) as HTMLElement
    const existingText = editor?.textContent || ''

    const response = await chrome.runtime.sendMessage({
      type: 'GENERATE_CONTENT',
      payload: {
        platform: 'linkedin',
        contentType: 'post',
        context: { selectedText: existingText }
      }
    })

    if (response.success && editor) {
      // Use textContent for safe text insertion
      editor.textContent = response.content
      // Trigger platform's input detection
      editor.dispatchEvent(new Event('input', { bubbles: true }))
    }
  }
}
```

### Cross-Browser Compatibility

```typescript
// lib/browser-api.ts

const browserAPI = typeof browser !== 'undefined' ? browser : chrome

export const storage = {
  get: (keys: string[]) => browserAPI.storage.local.get(keys),
  set: (items: Record<string, unknown>) => browserAPI.storage.local.set(items),
}

export const runtime = {
  sendMessage: (message: unknown) => browserAPI.runtime.sendMessage(message),
  onMessage: browserAPI.runtime.onMessage,
}

export const contextMenus = browserAPI.contextMenus
```

### Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| React | 18.x | Popup UI framework |
| Vite | 5.x | Build tool with HMR |
| webextension-polyfill | 0.10.x | Cross-browser API |

### Security Considerations

1. **API Key Storage**: Keys stored in `chrome.storage.local` (encrypted by browser)
2. **CSP Compliance**: Extension uses strict CSP; no inline scripts
3. **Permission Minimization**: Only request necessary host permissions
4. **Token Validation**: All API calls validate token server-side
5. **Link Code Expiry**: 5-minute expiry prevents replay attacks
6. **Rate Limiting**: Extension requests subject to same rate limits
7. **Content Injection**: Use textContent instead of innerHTML to prevent XSS

### Complexity Assessment

| Aspect | Complexity | Rationale |
|--------|------------|-----------|
| Core Extension | Medium | Standard Manifest V3 patterns |
| Site Injection | High | Platform-specific DOM manipulation |
| Auth Flow | Medium | Standard OAuth-like linking |
| Cross-Browser | Medium | API differences manageable |
| **Overall** | **High** | Multiple moving parts |

**Estimated Development Time**: 4-6 weeks

---

## F12: Team Collaboration

### Overview

Multi-tenant team workspace with role-based access control, content approval workflows, and real-time collaboration capabilities.

### Architecture Diagram

```
+------------------------------------------------------------------+
|                        Frontend (Next.js)                          |
+------------------------------------------------------------------+
|  Auth Provider  |  Team Context  |  RBAC Guards  |  Real-time UI  |
+--------+--------+--------+-------+-------+-------+--------+--------+
         |                 |               |                |
         v                 v               v                v
+------------------------------------------------------------------+
|                        API Layer (FastAPI)                         |
+------------------------------------------------------------------+
|  Auth Routes  |  Team Routes  |  RBAC Middleware  |  WebSocket    |
+-------+-------+-------+-------+--------+---------+--------+-------+
        |               |                |                  |
        v               v                v                  v
+---------------+  +---------------+  +---------------+  +----------+
| Supabase Auth |  | PostgreSQL    |  | Redis         |  | Y.js     |
| (OAuth 2.0)   |  | (Multi-tenant)|  | (Sessions)    |  | (CRDT)   |
+---------------+  +---------------+  +---------------+  +----------+
```

### User Authentication System

```typescript
// Supabase Auth Configuration

// lib/auth/supabase-auth.ts
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// OAuth providers configuration
const authConfig = {
  providers: ['google', 'github', 'azure'],
  redirectTo: `${process.env.NEXT_PUBLIC_APP_URL}/auth/callback`,
  scopes: {
    google: 'email profile',
    github: 'read:user user:email',
    azure: 'openid profile email'
  }
}

// Sign in with OAuth
export async function signInWithProvider(provider: 'google' | 'github' | 'azure') {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo: authConfig.redirectTo,
      scopes: authConfig.scopes[provider]
    }
  })
  return { data, error }
}
```

### Multi-Tenancy Architecture

```
Strategy: Schema-based isolation with shared tables

+------------------+     +------------------+     +------------------+
|   Organization   |---->|      Team        |---->|      User        |
|   (Tenant)       |     |   (Workspace)    |     |   (Member)       |
+------------------+     +------------------+     +------------------+
        |                        |                        |
        v                        v                        v
+------------------+     +------------------+     +------------------+
|  org_settings    |     |  team_content    |     |  user_prefs      |
|  org_billing     |     |  team_templates  |     |  user_activity   |
|  org_limits      |     |  team_workflows  |     |  user_roles      |
+------------------+     +------------------+     +------------------+
```

### Data Models

```typescript
// types/team.ts

interface Organization {
  id: string
  name: string
  slug: string
  plan: 'starter' | 'professional' | 'enterprise'
  settings: OrganizationSettings
  createdAt: Date
  ownerId: string
}

interface Team {
  id: string
  organizationId: string
  name: string
  slug: string
  settings: TeamSettings
  createdAt: Date
}

interface TeamMember {
  id: string
  userId: string
  teamId: string
  role: TeamRole
  permissions: Permission[]
  joinedAt: Date
  invitedBy: string
}

type TeamRole = 'owner' | 'admin' | 'editor' | 'reviewer' | 'viewer'

interface Permission {
  resource: 'content' | 'templates' | 'settings' | 'members' | 'billing'
  actions: ('create' | 'read' | 'update' | 'delete' | 'approve')[]
}

interface ContentItem {
  id: string
  teamId: string
  createdBy: string
  title: string
  content: string
  status: ContentStatus
  workflowState: WorkflowState
  version: number
  createdAt: Date
  updatedAt: Date
}

type ContentStatus = 'draft' | 'pending_review' | 'approved' | 'published' | 'archived'

interface WorkflowState {
  currentStep: string
  assignedTo: string[]
  dueDate?: Date
  comments: WorkflowComment[]
}
```

### Role-Based Access Control (RBAC)

```typescript
// lib/rbac/permissions.ts

const ROLE_PERMISSIONS: Record<TeamRole, Permission[]> = {
  owner: [
    { resource: 'content', actions: ['create', 'read', 'update', 'delete', 'approve'] },
    { resource: 'templates', actions: ['create', 'read', 'update', 'delete'] },
    { resource: 'settings', actions: ['create', 'read', 'update', 'delete'] },
    { resource: 'members', actions: ['create', 'read', 'update', 'delete'] },
    { resource: 'billing', actions: ['read', 'update'] },
  ],
  admin: [
    { resource: 'content', actions: ['create', 'read', 'update', 'delete', 'approve'] },
    { resource: 'templates', actions: ['create', 'read', 'update', 'delete'] },
    { resource: 'settings', actions: ['read', 'update'] },
    { resource: 'members', actions: ['create', 'read', 'update'] },
    { resource: 'billing', actions: ['read'] },
  ],
  editor: [
    { resource: 'content', actions: ['create', 'read', 'update'] },
    { resource: 'templates', actions: ['read'] },
    { resource: 'settings', actions: ['read'] },
    { resource: 'members', actions: ['read'] },
  ],
  reviewer: [
    { resource: 'content', actions: ['read', 'approve'] },
    { resource: 'templates', actions: ['read'] },
    { resource: 'members', actions: ['read'] },
  ],
  viewer: [
    { resource: 'content', actions: ['read'] },
    { resource: 'templates', actions: ['read'] },
  ],
}

// RBAC Middleware
export function requirePermission(resource: string, action: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user
    const teamId = req.params.teamId || req.body.teamId

    const member = await getTeamMember(user.id, teamId)
    if (!member) {
      return res.status(403).json({ error: 'Not a team member' })
    }

    const hasPermission = checkPermission(member.role, resource, action)
    if (!hasPermission) {
      return res.status(403).json({ error: 'Insufficient permissions' })
    }

    next()
  }
}
```

### Content Approval Workflow Engine

```typescript
// lib/workflow/engine.ts

interface WorkflowDefinition {
  id: string
  name: string
  steps: WorkflowStep[]
  triggers: WorkflowTrigger[]
}

interface WorkflowStep {
  id: string
  name: string
  type: 'approval' | 'review' | 'notification' | 'automation'
  config: {
    requiredApprovers?: number
    approverRoles?: TeamRole[]
    timeoutHours?: number
    autoApprove?: boolean
  }
  transitions: {
    onApprove: string  // next step ID
    onReject: string   // step ID on rejection
  }
}

class WorkflowEngine {
  async executeStep(content: ContentItem, step: WorkflowStep): Promise<void> {
    switch (step.type) {
      case 'approval':
        await this.handleApprovalStep(content, step)
        break
      case 'review':
        await this.handleReviewStep(content, step)
        break
      case 'notification':
        await this.sendNotifications(content, step)
        break
      case 'automation':
        await this.runAutomation(content, step)
        break
    }
  }

  async submitForApproval(contentId: string, submitterId: string): Promise<void> {
    const content = await this.getContent(contentId)
    const workflow = await this.getWorkflow(content.teamId)

    await this.updateContentStatus(contentId, 'pending_review')
    await this.createApprovalRequest({
      contentId,
      workflowId: workflow.id,
      currentStep: workflow.steps[0].id,
      submittedBy: submitterId,
    })

    await this.notifyApprovers(content, workflow.steps[0])
  }

  async approveContent(
    contentId: string,
    approverId: string,
    comment?: string
  ): Promise<void> {
    const approval = await this.getApprovalRequest(contentId)
    const step = await this.getWorkflowStep(approval.currentStep)

    await this.recordApproval(contentId, approverId, comment)

    const approvalCount = await this.getApprovalCount(contentId, step.id)
    if (approvalCount >= (step.config.requiredApprovers || 1)) {
      await this.transitionToNextStep(contentId, step.transitions.onApprove)
    }
  }
}
```

### Real-Time Collaboration (CRDT via Y.js)

```
Decision: CRDT (Conflict-free Replicated Data Types) via Y.js

Rationale:
- No central server required for conflict resolution
- Better offline support
- Simpler implementation for text editing
- Y.js has proven React bindings

Trade-offs:
- Larger document size (operation history)
- Less precise conflict resolution than OT
- Acceptable for content generation use case
```

```typescript
// lib/collaboration/yjs-provider.ts

import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'

export function createCollaborativeDocument(
  documentId: string,
  teamId: string
): { doc: Y.Doc; provider: WebsocketProvider } {
  const doc = new Y.Doc()

  const provider = new WebsocketProvider(
    process.env.NEXT_PUBLIC_WS_URL!,
    `team/${teamId}/doc/${documentId}`,
    doc,
    {
      params: {
        auth: getAuthToken(),
      },
    }
  )

  provider.on('status', (event: { status: string }) => {
    console.log('Connection status:', event.status)
  })

  return { doc, provider }
}

// React hook for collaborative editing
export function useCollaborativeEditor(documentId: string, teamId: string) {
  const [doc, setDoc] = useState<Y.Doc | null>(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const { doc, provider } = createCollaborativeDocument(documentId, teamId)

    provider.on('sync', (isSynced: boolean) => {
      setConnected(isSynced)
    })

    setDoc(doc)

    return () => {
      provider.destroy()
      doc.destroy()
    }
  }, [documentId, teamId])

  return { doc, connected }
}
```

### Database Schema

```sql
-- Migration: 011_create_team_tables.sql

-- Organizations (tenants)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    plan TEXT NOT NULL DEFAULT 'starter',
    settings JSONB NOT NULL DEFAULT '{}',
    owner_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Teams (workspaces within organizations)
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    settings JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(organization_id, slug)
);

-- Team members with roles
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'viewer',
    permissions JSONB,
    invited_by UUID,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, team_id)
);

-- Team content with workflow state
CREATE TABLE team_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    created_by UUID NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    workflow_state JSONB,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Content versions for history
CREATE TABLE content_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID NOT NULL REFERENCES team_content(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    changed_by UUID NOT NULL,
    change_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(content_id, version)
);

-- Workflow definitions
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    steps JSONB NOT NULL,
    triggers JSONB NOT NULL DEFAULT '[]',
    is_default BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Approval requests
CREATE TABLE approval_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID NOT NULL REFERENCES team_content(id) ON DELETE CASCADE,
    workflow_id UUID NOT NULL REFERENCES workflows(id),
    current_step TEXT NOT NULL,
    submitted_by UUID NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Individual approvals
CREATE TABLE approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id UUID NOT NULL REFERENCES approval_requests(id) ON DELETE CASCADE,
    step_id TEXT NOT NULL,
    approver_id UUID NOT NULL,
    decision TEXT NOT NULL,  -- 'approved', 'rejected', 'requested_changes'
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_teams_org ON teams(organization_id);
CREATE INDEX idx_team_members_user ON team_members(user_id);
CREATE INDEX idx_team_members_team ON team_members(team_id);
CREATE INDEX idx_team_content_team ON team_content(team_id);
CREATE INDEX idx_team_content_status ON team_content(status);
CREATE INDEX idx_approval_requests_content ON approval_requests(content_id);

-- Row Level Security
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_content ENABLE ROW LEVEL SECURITY;

-- RLS Policies (example for team_content)
CREATE POLICY "Team members can view team content"
    ON team_content FOR SELECT
    USING (
        team_id IN (
            SELECT team_id FROM team_members
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Editors can create content"
    ON team_content FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM team_members
            WHERE user_id = auth.uid()
            AND team_id = team_content.team_id
            AND role IN ('owner', 'admin', 'editor')
        )
    );
```

### API Endpoints

```yaml
# Team Management
POST /api/v1/organizations:
  description: Create new organization
  auth: required
  body: { name, slug, plan }

POST /api/v1/organizations/{orgId}/teams:
  description: Create team within organization
  auth: required (org owner/admin)
  body: { name, slug }

GET /api/v1/teams/{teamId}/members:
  description: List team members
  auth: required (team member)

POST /api/v1/teams/{teamId}/members:
  description: Invite team member
  auth: required (admin+)
  body: { email, role }

# Content Workflow
POST /api/v1/teams/{teamId}/content:
  description: Create content item
  auth: required (editor+)

POST /api/v1/content/{contentId}/submit:
  description: Submit for approval
  auth: required (creator or editor+)

POST /api/v1/content/{contentId}/approve:
  description: Approve content
  auth: required (reviewer+)
  body: { decision, comment }

# Real-time
WS /ws/teams/{teamId}/collaborate:
  description: WebSocket for real-time collaboration
  auth: required (team member)
```

### Migration Strategy (File-based to Database)

```python
# scripts/migrate_to_database.py

async def migrate_conversations():
    """Migrate file-based conversations to Supabase."""
    storage_dir = Path("./data/conversations")

    for file_path in storage_dir.glob("*.json"):
        conversation_id = file_path.stem

        with open(file_path) as f:
            messages = json.load(f)

        # Insert into database
        await supabase.table("conversations").upsert({
            "id": conversation_id,
            "messages": messages,
            "migrated_at": datetime.utcnow().isoformat()
        }).execute()

        # Archive original file
        archive_path = storage_dir / "archived" / file_path.name
        file_path.rename(archive_path)

async def migrate_api_keys():
    """Migrate file-based API keys to database."""
    # Similar pattern for api_keys.json
    pass
```

### Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| @supabase/supabase-js | 2.x | Auth and database client |
| @supabase/auth-helpers-nextjs | 0.8.x | Next.js auth integration |
| yjs | 13.x | CRDT implementation |
| y-websocket | 1.x | WebSocket sync provider |
| y-prosemirror | 1.x | Rich text editor binding |

### Security Considerations

1. **Row Level Security**: All tables use Supabase RLS
2. **JWT Validation**: All requests validate Supabase JWT
3. **Tenant Isolation**: Queries always scoped to organization/team
4. **Audit Logging**: All permission changes logged
5. **Invite Token Expiry**: Team invites expire after 7 days
6. **Session Management**: Redis-backed sessions with 24h expiry

### Complexity Assessment

| Aspect | Complexity | Rationale |
|--------|------------|-----------|
| Auth System | Medium | Supabase handles heavy lifting |
| Multi-tenancy | High | Complex data isolation |
| RBAC | Medium | Well-defined patterns |
| Workflow Engine | High | Custom state machine |
| Real-time Collab | High | CRDT complexity |
| Migration | Medium | One-time operation |
| **Overall** | **Very High** | Core infrastructure change |

**Estimated Development Time**: 8-12 weeks

---

## F13: Additional Publishing Integrations

### Overview

Extend Blog AI's publishing capabilities with additional platform integrations including Substack, LinkedIn Articles, Ghost CMS, Twitter/X threads, and social media schedulers.

### Architecture Diagram

```
+------------------------------------------------------------------+
|                      Publisher Abstraction Layer                   |
+------------------------------------------------------------------+
|                        PublisherInterface                          |
|  +authenticate() +publish() +schedule() +getAnalytics() +revoke() |
+------------------------------------------------------------------+
        |           |           |           |           |
        v           v           v           v           v
+----------+ +----------+ +----------+ +----------+ +----------+
| WordPress| | Medium   | | Substack | | LinkedIn | | Ghost    |
| Publisher| | Publisher| | Publisher| | Publisher| | Publisher|
+----------+ +----------+ +----------+ +----------+ +----------+
        |           |           |           |           |
        v           v           v           v           v
+------------------------------------------------------------------+
|                     OAuth Token Manager                            |
|              (Encrypted storage, refresh handling)                 |
+------------------------------------------------------------------+
        |
        v
+------------------------------------------------------------------+
|                     Scheduling Engine                              |
|         (Queue-based, timezone-aware, retry logic)                |
+------------------------------------------------------------------+
```

### Publisher Abstraction Interface

```python
# src/integrations/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class PublishOptions:
    title: str
    content: str
    content_format: str  # 'html', 'markdown', 'plain'
    tags: List[str]
    canonical_url: Optional[str] = None
    featured_image_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

@dataclass
class PublishResult:
    success: bool
    platform: str
    post_id: Optional[str]
    post_url: Optional[str]
    error_message: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class AnalyticsData:
    views: int
    likes: int
    comments: int
    shares: int
    engagement_rate: float
    period_start: datetime
    period_end: datetime

class PublisherInterface(ABC):
    """Abstract base class for all publishing integrations."""

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with the platform."""
        pass

    @abstractmethod
    async def publish(self, options: PublishOptions) -> PublishResult:
        """Publish content to the platform."""
        pass

    @abstractmethod
    async def schedule(
        self, options: PublishOptions, publish_at: datetime
    ) -> PublishResult:
        """Schedule content for future publication."""
        pass

    @abstractmethod
    async def get_analytics(
        self, post_id: str, period_days: int = 30
    ) -> AnalyticsData:
        """Get analytics for a published post."""
        pass

    @abstractmethod
    async def revoke(self) -> bool:
        """Revoke authentication tokens."""
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform identifier."""
        pass
```

### New Platform Implementations

```python
# src/integrations/substack.py

class SubstackPublisher(PublisherInterface):
    """Substack integration via unofficial API."""

    BASE_URL = "https://substack.com/api/v1"

    def __init__(self):
        self.session = None
        self.publication_id = None

    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        # Substack uses email/password auth (no official API)
        # Consider using browser automation or email-based auth
        self.session = await self._create_session(
            credentials['email'],
            credentials['password']
        )
        return self.session is not None

    async def publish(self, options: PublishOptions) -> PublishResult:
        payload = {
            "draft_title": options.title,
            "draft_body": self._convert_to_substack_format(options.content),
            "draft_subtitle": options.metadata.get('subtitle', ''),
            "audience": options.metadata.get('audience', 'everyone'),
        }

        response = await self._post(f"/publication/{self.publication_id}/drafts", payload)

        if options.scheduled_at is None:
            # Publish immediately
            await self._post(f"/drafts/{response['id']}/publish", {})

        return PublishResult(
            success=True,
            platform='substack',
            post_id=response['id'],
            post_url=response.get('canonical_url'),
            error_message=None,
            metadata={'draft_id': response['id']}
        )


# src/integrations/linkedin_articles.py

class LinkedInArticlesPublisher(PublisherInterface):
    """LinkedIn Articles API integration."""

    BASE_URL = "https://api.linkedin.com/v2"

    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        # OAuth 2.0 flow
        self.access_token = credentials.get('access_token')
        self.person_id = await self._get_person_id()
        return self.person_id is not None

    async def publish(self, options: PublishOptions) -> PublishResult:
        # LinkedIn UGC API for articles
        payload = {
            "author": f"urn:li:person:{self.person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": options.title
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [{
                        "status": "READY",
                        "description": {"text": options.content[:700]},
                        "originalUrl": options.canonical_url,
                        "title": {"text": options.title}
                    }]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        response = await self._post("/ugcPosts", payload)
        return PublishResult(
            success=True,
            platform='linkedin',
            post_id=response['id'],
            post_url=self._construct_post_url(response['id']),
            error_message=None,
            metadata={}
        )


# src/integrations/ghost.py

class GhostPublisher(PublisherInterface):
    """Ghost CMS Admin API integration."""

    def __init__(self, api_url: str, admin_api_key: str):
        self.api_url = api_url.rstrip('/')
        self.admin_api_key = admin_api_key
        self._token = None

    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        # Ghost uses JWT signed with Admin API key
        self._token = self._create_jwt_token()
        return True

    def _create_jwt_token(self) -> str:
        import jwt
        from datetime import datetime, timedelta

        key_id, secret = self.admin_api_key.split(':')
        iat = int(datetime.now().timestamp())

        payload = {
            'iat': iat,
            'exp': iat + 300,  # 5 minutes
            'aud': '/admin/'
        }

        return jwt.encode(
            payload,
            bytes.fromhex(secret),
            algorithm='HS256',
            headers={'kid': key_id}
        )

    async def publish(self, options: PublishOptions) -> PublishResult:
        payload = {
            "posts": [{
                "title": options.title,
                "html": options.content if options.content_format == 'html'
                        else self._markdown_to_html(options.content),
                "status": "published",
                "tags": [{"name": tag} for tag in options.tags],
                "feature_image": options.featured_image_url,
            }]
        }

        response = await self._post("/ghost/api/admin/posts/", payload)
        post = response['posts'][0]

        return PublishResult(
            success=True,
            platform='ghost',
            post_id=post['id'],
            post_url=post['url'],
            error_message=None,
            metadata={'slug': post['slug']}
        )


# src/integrations/twitter_threads.py

class TwitterThreadPublisher(PublisherInterface):
    """Twitter/X thread publishing via API v2."""

    BASE_URL = "https://api.twitter.com/2"

    async def publish(self, options: PublishOptions) -> PublishResult:
        # Split content into thread
        tweets = self._split_into_tweets(options.content)

        tweet_ids = []
        reply_to = None

        for i, tweet_text in enumerate(tweets):
            payload = {"text": tweet_text}
            if reply_to:
                payload["reply"] = {"in_reply_to_tweet_id": reply_to}

            response = await self._post("/tweets", payload)
            tweet_id = response['data']['id']
            tweet_ids.append(tweet_id)
            reply_to = tweet_id

        return PublishResult(
            success=True,
            platform='twitter',
            post_id=tweet_ids[0],
            post_url=f"https://twitter.com/i/status/{tweet_ids[0]}",
            error_message=None,
            metadata={'thread_ids': tweet_ids, 'tweet_count': len(tweets)}
        )

    def _split_into_tweets(self, content: str, max_length: int = 280) -> List[str]:
        """Split long content into tweet-sized chunks."""
        tweets = []
        paragraphs = content.split('\n\n')

        current_tweet = ""
        for para in paragraphs:
            if len(current_tweet) + len(para) + 2 <= max_length:
                current_tweet += para + "\n\n"
            else:
                if current_tweet:
                    tweets.append(current_tweet.strip())
                current_tweet = para + "\n\n"

        if current_tweet:
            tweets.append(current_tweet.strip())

        return tweets
```

### OAuth Flow Management

```python
# src/integrations/oauth_manager.py

from cryptography.fernet import Fernet
from datetime import datetime, timedelta

class OAuthTokenManager:
    """Manages OAuth tokens with encryption and refresh."""

    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key.encode())

    async def store_token(
        self,
        user_id: str,
        platform: str,
        token_data: Dict[str, Any]
    ) -> None:
        encrypted = self.cipher.encrypt(
            json.dumps(token_data).encode()
        ).decode()

        await supabase.table('oauth_tokens').upsert({
            'user_id': user_id,
            'platform': platform,
            'encrypted_token': encrypted,
            'expires_at': token_data.get('expires_at'),
            'updated_at': datetime.utcnow().isoformat()
        }).execute()

    async def get_token(
        self, user_id: str, platform: str
    ) -> Optional[Dict[str, Any]]:
        result = await supabase.table('oauth_tokens').select('*').eq(
            'user_id', user_id
        ).eq('platform', platform).single().execute()

        if not result.data:
            return None

        decrypted = self.cipher.decrypt(
            result.data['encrypted_token'].encode()
        ).decode()

        token_data = json.loads(decrypted)

        # Check if refresh needed
        if self._needs_refresh(token_data):
            token_data = await self._refresh_token(platform, token_data)
            await self.store_token(user_id, platform, token_data)

        return token_data

    def _needs_refresh(self, token_data: Dict[str, Any]) -> bool:
        expires_at = token_data.get('expires_at')
        if not expires_at:
            return False
        # Refresh if expiring within 5 minutes
        return datetime.fromisoformat(expires_at) < datetime.utcnow() + timedelta(minutes=5)
```

### Scheduling System

```python
# src/integrations/scheduler.py

from celery import Celery
from datetime import datetime
import pytz

celery_app = Celery('blog_ai', broker='redis://localhost:6379/0')

@dataclass
class ScheduledPost:
    id: str
    user_id: str
    platform: str
    options: PublishOptions
    scheduled_at: datetime
    timezone: str
    status: str  # 'pending', 'published', 'failed', 'cancelled'
    retry_count: int = 0
    max_retries: int = 3

class PublishScheduler:
    """Queue-based scheduling with timezone support."""

    async def schedule_post(
        self,
        user_id: str,
        platform: str,
        options: PublishOptions,
        scheduled_at: datetime,
        timezone: str = 'UTC'
    ) -> ScheduledPost:
        # Convert to UTC for storage
        tz = pytz.timezone(timezone)
        local_time = tz.localize(scheduled_at)
        utc_time = local_time.astimezone(pytz.UTC)

        post = ScheduledPost(
            id=str(uuid.uuid4()),
            user_id=user_id,
            platform=platform,
            options=options,
            scheduled_at=utc_time,
            timezone=timezone,
            status='pending'
        )

        # Store in database
        await self._save_scheduled_post(post)

        # Schedule Celery task
        publish_scheduled_post.apply_async(
            args=[post.id],
            eta=utc_time
        )

        return post

@celery_app.task(bind=True, max_retries=3)
def publish_scheduled_post(self, post_id: str):
    """Celery task to publish scheduled content."""
    try:
        post = get_scheduled_post(post_id)
        if post.status != 'pending':
            return

        publisher = get_publisher(post.platform)
        result = publisher.publish(post.options)

        if result.success:
            update_post_status(post_id, 'published', result)
        else:
            raise Exception(result.error_message)

    except Exception as e:
        if self.request.retries < 3:
            self.retry(countdown=60 * (2 ** self.request.retries))
        else:
            update_post_status(post_id, 'failed', {'error': str(e)})
```

### Database Schema

```sql
-- Migration: 012_create_publishing_tables.sql

-- OAuth tokens (encrypted)
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    encrypted_token TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    scopes TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, platform)
);

-- Scheduled posts
CREATE TABLE scheduled_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    options JSONB NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    status TEXT NOT NULL DEFAULT 'pending',
    retry_count INTEGER NOT NULL DEFAULT 0,
    result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

-- Publishing history
CREATE TABLE publishing_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    post_id TEXT,
    post_url TEXT,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    analytics JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Platform connections (user's connected accounts)
CREATE TABLE platform_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    platform_user_id TEXT,
    platform_username TEXT,
    connected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT true,
    UNIQUE(user_id, platform)
);

-- Indexes
CREATE INDEX idx_oauth_tokens_user_platform ON oauth_tokens(user_id, platform);
CREATE INDEX idx_scheduled_posts_user ON scheduled_posts(user_id);
CREATE INDEX idx_scheduled_posts_status ON scheduled_posts(status) WHERE status = 'pending';
CREATE INDEX idx_scheduled_posts_scheduled_at ON scheduled_posts(scheduled_at) WHERE status = 'pending';
CREATE INDEX idx_publishing_history_user ON publishing_history(user_id);
```

### API Endpoints

```yaml
# Platform connections
GET /api/v1/integrations/platforms:
  description: List available publishing platforms
  response: Platform[]

GET /api/v1/integrations/connections:
  description: List user's connected platforms
  auth: required
  response: PlatformConnection[]

POST /api/v1/integrations/{platform}/connect:
  description: Initiate OAuth flow for platform
  auth: required
  response: { authUrl: string }

GET /api/v1/integrations/{platform}/callback:
  description: OAuth callback handler
  query: { code, state }

DELETE /api/v1/integrations/{platform}/disconnect:
  description: Disconnect platform
  auth: required

# Publishing
POST /api/v1/publish:
  description: Publish to one or more platforms
  auth: required
  body:
    platforms: string[]
    title: string
    content: string
    tags: string[]
    scheduledAt?: datetime
    timezone?: string
  response: PublishResult[]

GET /api/v1/publish/scheduled:
  description: List scheduled posts
  auth: required
  response: ScheduledPost[]

DELETE /api/v1/publish/scheduled/{id}:
  description: Cancel scheduled post
  auth: required

# Analytics
GET /api/v1/publish/analytics:
  description: Aggregated analytics across platforms
  auth: required
  query: { periodDays: number }
  response: AggregatedAnalytics
```

### Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| celery | 5.x | Task queue for scheduling |
| redis | 4.x | Celery broker and result backend |
| cryptography | 41.x | Token encryption |
| PyJWT | 2.x | JWT for Ghost API |
| tweepy | 4.x | Twitter API client |
| pytz | 2023.x | Timezone handling |

### Security Considerations

1. **Token Encryption**: All OAuth tokens encrypted at rest with Fernet
2. **Scope Minimization**: Request only necessary OAuth scopes
3. **Token Rotation**: Automatic refresh before expiry
4. **Audit Trail**: All publishing actions logged
5. **Rate Limiting**: Per-platform rate limit awareness
6. **Revocation**: Users can disconnect platforms anytime

### Complexity Assessment

| Aspect | Complexity | Rationale |
|--------|------------|-----------|
| Publisher Interface | Low | Clean abstraction pattern |
| OAuth Management | High | Each platform has quirks |
| Scheduling | Medium | Celery handles complexity |
| Analytics Aggregation | Medium | API differences |
| **Overall** | **High** | Many external APIs |

**Estimated Development Time**: 6-8 weeks

---

## F14: Content Marketplace

### Overview

A marketplace for buying, selling, and sharing content templates, prompts, and generation presets. Includes revenue sharing for creators and discovery features.

### Architecture Diagram

```
+------------------------------------------------------------------+
|                     Marketplace Frontend                           |
+------------------------------------------------------------------+
| Discovery | Listings | Seller Dashboard | Purchase Flow | Reviews |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                     Marketplace API                                |
+------------------------------------------------------------------+
| Search | Listings | Purchases | Payouts | Reviews | Licensing     |
+------------------------------------------------------------------+
        |               |               |               |
        v               v               v               v
+----------+    +------------+   +------------+   +------------+
| Postgres |    | Stripe     |   | Algolia    |   | S3/R2      |
| (Data)   |    | Connect    |   | (Search)   |   | (Assets)   |
+----------+    +------------+   +------------+   +------------+
```

### Data Models

```typescript
// types/marketplace.ts

interface MarketplaceListing {
  id: string
  sellerId: string
  title: string
  description: string
  shortDescription: string
  type: ListingType
  category: string
  tags: string[]
  price: PriceInfo
  previewContent: string
  fullContent: string  // Encrypted, revealed after purchase
  screenshots: string[]
  demoUrl?: string
  stats: ListingStats
  status: 'draft' | 'pending_review' | 'active' | 'suspended'
  createdAt: Date
  updatedAt: Date
}

type ListingType = 'template' | 'prompt_pack' | 'workflow' | 'style_guide' | 'brand_voice'

interface PriceInfo {
  amount: number  // In cents
  currency: 'USD'
  tier: 'free' | 'paid'
  licensingModel: LicensingModel
}

type LicensingModel = 'single_use' | 'unlimited' | 'team' | 'enterprise'

interface ListingStats {
  views: number
  purchases: number
  rating: number
  reviewCount: number
  usageCount: number
}

interface SellerProfile {
  id: string
  userId: string
  displayName: string
  bio: string
  avatar: string
  stripeConnectId: string
  verified: boolean
  stats: SellerStats
  payoutSettings: PayoutSettings
  createdAt: Date
}

interface SellerStats {
  totalSales: number
  totalRevenue: number
  totalListings: number
  averageRating: number
  followersCount: number
}

interface Purchase {
  id: string
  buyerId: string
  listingId: string
  sellerId: string
  amount: number
  platformFee: number
  sellerPayout: number
  stripePaymentId: string
  licenseKey: string
  status: 'pending' | 'completed' | 'refunded'
  createdAt: Date
}

interface Review {
  id: string
  purchaseId: string
  buyerId: string
  listingId: string
  rating: number  // 1-5
  title: string
  content: string
  helpfulCount: number
  verified: boolean
  createdAt: Date
}

interface UsageRecord {
  id: string
  purchaseId: string
  userId: string
  listingId: string
  usedAt: Date
  context: string  // What they used it for
}
```

### Template/Prompt Packaging Format

```typescript
// types/package.ts

interface ContentPackage {
  version: '1.0'
  metadata: PackageMetadata
  content: PackageContent
  usage: UsageInstructions
}

interface PackageMetadata {
  id: string
  name: string
  description: string
  author: string
  license: string
  tags: string[]
  compatibleTools: string[]  // Tool IDs this works with
  requiredInputs: InputDefinition[]
}

interface PackageContent {
  type: 'template' | 'prompt' | 'workflow'

  // For templates
  template?: {
    systemPrompt: string
    userPromptTemplate: string
    outputFormat: string
    examples: Example[]
  }

  // For prompt packs
  prompts?: {
    name: string
    prompt: string
    variables: string[]
    category: string
  }[]

  // For workflows
  workflow?: {
    steps: WorkflowStep[]
    connections: Connection[]
  }
}

interface UsageInstructions {
  quickStart: string
  documentation: string
  examples: UsageExample[]
  tips: string[]
}

// Example package structure (JSON)
const examplePackage = {
  "version": "1.0",
  "metadata": {
    "id": "pkg_saas_landing_page",
    "name": "SaaS Landing Page Copy Generator",
    "description": "Generate high-converting landing page copy for SaaS products",
    "author": "seller_123",
    "license": "unlimited",
    "tags": ["saas", "landing-page", "copywriting"],
    "compatibleTools": ["blog_post", "value_proposition"],
    "requiredInputs": [
      { "name": "product_name", "type": "string", "required": true },
      { "name": "target_audience", "type": "string", "required": true },
      { "name": "key_features", "type": "array", "required": true }
    ]
  },
  "content": {
    "type": "template",
    "template": {
      "systemPrompt": "You are an expert SaaS copywriter...",
      "userPromptTemplate": "Create landing page copy for {{product_name}}...",
      "outputFormat": "markdown",
      "examples": []
    }
  }
}
```

### Revenue Sharing System (Stripe Connect)

```python
# src/marketplace/payments.py

import stripe
from decimal import Decimal

class MarketplacePayments:
    """Handles marketplace payments via Stripe Connect."""

    PLATFORM_FEE_PERCENT = Decimal('0.20')  # 20% platform fee

    def __init__(self):
        stripe.api_key = os.environ['STRIPE_SECRET_KEY']

    async def create_seller_account(self, user_id: str, email: str) -> str:
        """Create Stripe Connect Express account for seller."""
        account = stripe.Account.create(
            type='express',
            email=email,
            capabilities={
                'card_payments': {'requested': True},
                'transfers': {'requested': True},
            },
            metadata={'user_id': user_id}
        )

        # Store connect ID
        await supabase.table('seller_profiles').update({
            'stripe_connect_id': account.id
        }).eq('user_id', user_id).execute()

        return account.id

    async def get_onboarding_link(self, account_id: str) -> str:
        """Generate Stripe Connect onboarding link."""
        link = stripe.AccountLink.create(
            account=account_id,
            refresh_url=f"{BASE_URL}/seller/onboarding/refresh",
            return_url=f"{BASE_URL}/seller/onboarding/complete",
            type='account_onboarding',
        )
        return link.url

    async def process_purchase(
        self,
        buyer_id: str,
        listing_id: str,
        payment_method_id: str
    ) -> Purchase:
        """Process marketplace purchase with revenue split."""
        listing = await get_listing(listing_id)
        seller = await get_seller_profile(listing.seller_id)

        amount = listing.price.amount
        platform_fee = int(amount * self.PLATFORM_FEE_PERCENT)
        seller_payout = amount - platform_fee

        # Create payment intent with transfer
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            payment_method=payment_method_id,
            confirm=True,
            application_fee_amount=platform_fee,
            transfer_data={
                'destination': seller.stripe_connect_id,
            },
            metadata={
                'listing_id': listing_id,
                'buyer_id': buyer_id,
                'seller_id': listing.seller_id,
            }
        )

        # Create purchase record
        purchase = await create_purchase({
            'buyer_id': buyer_id,
            'listing_id': listing_id,
            'seller_id': listing.seller_id,
            'amount': amount,
            'platform_fee': platform_fee,
            'seller_payout': seller_payout,
            'stripe_payment_id': payment_intent.id,
            'license_key': generate_license_key(),
            'status': 'completed'
        })

        # Grant access to content
        await grant_content_access(buyer_id, listing_id, purchase.id)

        return purchase

    async def process_refund(self, purchase_id: str, reason: str) -> bool:
        """Process refund (within 7 days, no usage)."""
        purchase = await get_purchase(purchase_id)

        # Check refund eligibility
        if not self._is_refund_eligible(purchase):
            raise RefundNotEligibleError()

        # Reverse the transfer
        stripe.Refund.create(
            payment_intent=purchase.stripe_payment_id,
            reverse_transfer=True,
        )

        # Update purchase status
        await update_purchase_status(purchase_id, 'refunded')

        # Revoke content access
        await revoke_content_access(purchase.buyer_id, purchase.listing_id)

        return True
```

### Rating and Review System

```python
# src/marketplace/reviews.py

class ReviewSystem:
    """Manages marketplace reviews with verification."""

    async def submit_review(
        self,
        purchase_id: str,
        rating: int,
        title: str,
        content: str
    ) -> Review:
        """Submit a verified purchase review."""
        purchase = await get_purchase(purchase_id)

        # Verify purchase belongs to reviewer
        if purchase.buyer_id != get_current_user_id():
            raise UnauthorizedError()

        # Check if already reviewed
        existing = await get_review_by_purchase(purchase_id)
        if existing:
            raise AlreadyReviewedError()

        review = await create_review({
            'purchase_id': purchase_id,
            'buyer_id': purchase.buyer_id,
            'listing_id': purchase.listing_id,
            'rating': rating,
            'title': title,
            'content': content,
            'verified': True,  # Verified purchase
        })

        # Update listing stats
        await self._update_listing_rating(purchase.listing_id)

        return review

    async def _update_listing_rating(self, listing_id: str) -> None:
        """Recalculate listing average rating."""
        reviews = await get_listing_reviews(listing_id)

        if not reviews:
            return

        avg_rating = sum(r.rating for r in reviews) / len(reviews)

        await supabase.table('marketplace_listings').update({
            'stats': {
                'rating': round(avg_rating, 2),
                'review_count': len(reviews)
            }
        }).eq('id', listing_id).execute()
```

### Discovery and Search

```python
# src/marketplace/search.py

from algoliasearch.search_client import SearchClient

class MarketplaceSearch:
    """Algolia-powered marketplace search."""

    def __init__(self):
        self.client = SearchClient.create(
            os.environ['ALGOLIA_APP_ID'],
            os.environ['ALGOLIA_API_KEY']
        )
        self.index = self.client.init_index('marketplace_listings')

    async def index_listing(self, listing: MarketplaceListing) -> None:
        """Index or update listing in Algolia."""
        record = {
            'objectID': listing.id,
            'title': listing.title,
            'description': listing.description,
            'type': listing.type,
            'category': listing.category,
            'tags': listing.tags,
            'price': listing.price.amount,
            'priceT tier': listing.price.tier,
            'rating': listing.stats.rating,
            'purchases': listing.stats.purchases,
            'seller': listing.seller_id,
            '_tags': listing.tags,  # For faceting
        }
        self.index.save_object(record)

    async def search(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        page: int = 0,
        hits_per_page: int = 20
    ) -> SearchResults:
        """Search marketplace listings."""
        search_params = {
            'query': query,
            'page': page,
            'hitsPerPage': hits_per_page,
            'attributesToRetrieve': ['*'],
            'facets': ['type', 'category', 'tags', 'priceTier'],
        }

        if filters:
            filter_strings = []
            if filters.get('type'):
                filter_strings.append(f"type:{filters['type']}")
            if filters.get('category'):
                filter_strings.append(f"category:{filters['category']}")
            if filters.get('free_only'):
                filter_strings.append("priceTier:free")
            if filters.get('min_rating'):
                filter_strings.append(f"rating >= {filters['min_rating']}")

            search_params['filters'] = ' AND '.join(filter_strings)

        results = self.index.search(**search_params)

        return SearchResults(
            hits=[self._transform_hit(h) for h in results['hits']],
            total=results['nbHits'],
            page=results['page'],
            pages=results['nbPages'],
            facets=results.get('facets', {})
        )
```

### Database Schema

```sql
-- Migration: 013_create_marketplace_tables.sql

-- Seller profiles
CREATE TABLE seller_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    display_name TEXT NOT NULL,
    bio TEXT,
    avatar_url TEXT,
    stripe_connect_id TEXT UNIQUE,
    verified BOOLEAN NOT NULL DEFAULT false,
    total_sales INTEGER NOT NULL DEFAULT 0,
    total_revenue INTEGER NOT NULL DEFAULT 0,
    average_rating NUMERIC(3,2),
    followers_count INTEGER NOT NULL DEFAULT 0,
    payout_settings JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Marketplace listings
CREATE TABLE marketplace_listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seller_id UUID NOT NULL REFERENCES seller_profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    short_description TEXT NOT NULL,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    price_amount INTEGER NOT NULL DEFAULT 0,
    price_currency TEXT NOT NULL DEFAULT 'USD',
    licensing_model TEXT NOT NULL DEFAULT 'unlimited',
    preview_content TEXT NOT NULL,
    full_content_encrypted TEXT NOT NULL,
    screenshots TEXT[] DEFAULT '{}',
    demo_url TEXT,
    views INTEGER NOT NULL DEFAULT 0,
    purchases INTEGER NOT NULL DEFAULT 0,
    rating NUMERIC(3,2),
    review_count INTEGER NOT NULL DEFAULT 0,
    usage_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Purchases
CREATE TABLE marketplace_purchases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    buyer_id UUID NOT NULL REFERENCES users(id),
    listing_id UUID NOT NULL REFERENCES marketplace_listings(id),
    seller_id UUID NOT NULL REFERENCES seller_profiles(id),
    amount INTEGER NOT NULL,
    platform_fee INTEGER NOT NULL,
    seller_payout INTEGER NOT NULL,
    stripe_payment_id TEXT,
    license_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'pending',
    refunded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(buyer_id, listing_id)
);

-- Reviews
CREATE TABLE marketplace_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    purchase_id UUID NOT NULL UNIQUE REFERENCES marketplace_purchases(id),
    buyer_id UUID NOT NULL REFERENCES users(id),
    listing_id UUID NOT NULL REFERENCES marketplace_listings(id),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    helpful_count INTEGER NOT NULL DEFAULT 0,
    verified BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Usage tracking
CREATE TABLE listing_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    purchase_id UUID NOT NULL REFERENCES marketplace_purchases(id),
    user_id UUID NOT NULL REFERENCES users(id),
    listing_id UUID NOT NULL REFERENCES marketplace_listings(id),
    context TEXT,
    used_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_listings_seller ON marketplace_listings(seller_id);
CREATE INDEX idx_listings_category ON marketplace_listings(category);
CREATE INDEX idx_listings_status ON marketplace_listings(status);
CREATE INDEX idx_listings_type ON marketplace_listings(type);
CREATE INDEX idx_purchases_buyer ON marketplace_purchases(buyer_id);
CREATE INDEX idx_purchases_listing ON marketplace_purchases(listing_id);
CREATE INDEX idx_reviews_listing ON marketplace_reviews(listing_id);
CREATE INDEX idx_usage_listing ON listing_usage(listing_id);

-- Full-text search
CREATE INDEX idx_listings_search ON marketplace_listings
    USING GIN (to_tsvector('english', title || ' ' || description));

-- Row Level Security
ALTER TABLE seller_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketplace_listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketplace_purchases ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketplace_reviews ENABLE ROW LEVEL SECURITY;
```

### API Endpoints

```yaml
# Seller
POST /api/v1/marketplace/seller/register:
  description: Register as a seller
  auth: required
  body: { displayName, bio }

GET /api/v1/marketplace/seller/onboarding:
  description: Get Stripe Connect onboarding URL
  auth: required (seller)

GET /api/v1/marketplace/seller/dashboard:
  description: Seller dashboard stats
  auth: required (seller)

GET /api/v1/marketplace/seller/payouts:
  description: Payout history
  auth: required (seller)

# Listings
GET /api/v1/marketplace/listings:
  description: Search/browse listings
  query: { q, type, category, page, sort }

GET /api/v1/marketplace/listings/{id}:
  description: Get listing details

POST /api/v1/marketplace/listings:
  description: Create listing
  auth: required (seller)

PUT /api/v1/marketplace/listings/{id}:
  description: Update listing
  auth: required (owner)

# Purchases
POST /api/v1/marketplace/purchase:
  description: Purchase a listing
  auth: required
  body: { listingId, paymentMethodId }

GET /api/v1/marketplace/purchases:
  description: User's purchases
  auth: required

POST /api/v1/marketplace/purchases/{id}/refund:
  description: Request refund
  auth: required (buyer)

# Reviews
POST /api/v1/marketplace/reviews:
  description: Submit review
  auth: required
  body: { purchaseId, rating, title, content }

GET /api/v1/marketplace/listings/{id}/reviews:
  description: Get listing reviews
```

### Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| stripe | 7.x | Payment processing |
| algoliasearch | 3.x | Search and discovery |
| cryptography | 41.x | Content encryption |

### Security Considerations

1. **Content Protection**: Full content encrypted until purchase
2. **Payment Security**: Stripe handles all payment data
3. **License Keys**: Unique, non-guessable keys
4. **Refund Policy**: 7-day window, no usage required
5. **Seller Verification**: Stripe Connect KYC
6. **Review Authenticity**: Only verified purchasers can review

### Complexity Assessment

| Aspect | Complexity | Rationale |
|--------|------------|-----------|
| Stripe Connect | High | Complex multi-party payments |
| Search | Medium | Algolia handles complexity |
| Content Packaging | Medium | Well-defined format |
| Reviews | Low | Standard implementation |
| **Overall** | **High** | Payment complexity |

**Estimated Development Time**: 8-10 weeks

---

## F15: Humanizer Pro (AI Detection Bypass)

### Overview

Advanced content humanization system designed to make AI-generated content indistinguishable from human-written text while maintaining quality and meaning.

### Architecture Diagram

```
+------------------------------------------------------------------+
|                      Humanizer Pro Pipeline                        |
+------------------------------------------------------------------+
|  Input Content                                                     |
|       |                                                            |
|       v                                                            |
|  +------------------+                                              |
|  | Detection Score  |  <-- AI Detection APIs                      |
|  | (Pre-analysis)   |      (GPTZero, Originality.ai, etc.)        |
|  +--------+---------+                                              |
|           |                                                        |
|           v                                                        |
|  +------------------+     +------------------+                     |
|  | Pattern Analysis |---->| Style Mimicry    |                     |
|  | Engine           |     | Engine           |                     |
|  +--------+---------+     +--------+---------+                     |
|           |                        |                               |
|           v                        v                               |
|  +------------------------------------------+                      |
|  |         Multi-Pass Humanization           |                     |
|  |  Pass 1: Structural Variation             |                     |
|  |  Pass 2: Lexical Substitution             |                     |
|  |  Pass 3: Rhythm & Cadence                 |                     |
|  |  Pass 4: Personal Touch Injection         |                     |
|  +------------------------------------------+                      |
|           |                                                        |
|           v                                                        |
|  +------------------+                                              |
|  | Detection Score  |  <-- Re-check against detectors             |
|  | (Post-analysis)  |                                              |
|  +--------+---------+                                              |
|           |                                                        |
|           v                                                        |
|  [Score < Threshold?]--No--> [Iterate]                            |
|           |                                                        |
|          Yes                                                       |
|           |                                                        |
|           v                                                        |
|  Output Humanized Content                                          |
+------------------------------------------------------------------+
```

### Data Models

```typescript
// types/humanizer.ts

interface HumanizerRequest {
  content: string
  targetStyle?: WritingStyle
  targetAudience?: string
  intensityLevel: 'light' | 'moderate' | 'aggressive'
  preserveKeywords?: string[]
  targetDetectionScore?: number  // 0-100, lower = more human
  maxIterations?: number
}

interface HumanizerResponse {
  originalContent: string
  humanizedContent: string
  preScore: DetectionScore
  postScore: DetectionScore
  iterations: number
  techniques: TechniqueApplied[]
  metadata: HumanizerMetadata
}

interface DetectionScore {
  overall: number  // 0-100, probability of AI
  gptzero?: number
  originality?: number
  copyleaks?: number
  sapling?: number
  confidence: 'low' | 'medium' | 'high'
}

interface WritingStyle {
  name: string
  characteristics: StyleCharacteristics
  sampleTexts?: string[]
}

interface StyleCharacteristics {
  sentenceLengthVariation: 'low' | 'medium' | 'high'
  vocabularyComplexity: 'simple' | 'moderate' | 'sophisticated'
  formalityLevel: number  // 1-10
  useOfContractions: boolean
  preferredTransitions: string[]
  typicalMistakes: string[]  // Intentional human-like errors
}

interface TechniqueApplied {
  name: string
  description: string
  before: string
  after: string
  impactScore: number
}

interface HumanizerMetadata {
  processingTimeMs: number
  tokensUsed: number
  modelUsed: string
}
```

### Enhanced Humanization Algorithms

```python
# src/post_processing/humanizer_pro.py

from typing import List, Optional
import random
import re

class HumanizerPro:
    """Advanced AI content humanization engine."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.detection_client = AIDetectionClient()
        self.style_analyzer = StyleAnalyzer()

    async def humanize(
        self,
        content: str,
        request: HumanizerRequest
    ) -> HumanizerResponse:
        """Main humanization pipeline with iterative improvement."""

        # Initial detection score
        pre_score = await self.detection_client.analyze(content)

        current_content = content
        iterations = 0
        max_iterations = request.max_iterations or 5
        target_score = request.target_detection_score or 30

        techniques_applied = []

        while iterations < max_iterations:
            # Check if target reached
            current_score = await self.detection_client.analyze(current_content)
            if current_score.overall <= target_score:
                break

            # Apply humanization passes
            current_content, techniques = await self._apply_humanization_passes(
                current_content,
                request,
                current_score
            )
            techniques_applied.extend(techniques)
            iterations += 1

        # Final score
        post_score = await self.detection_client.analyze(current_content)

        return HumanizerResponse(
            original_content=content,
            humanized_content=current_content,
            pre_score=pre_score,
            post_score=post_score,
            iterations=iterations,
            techniques=techniques_applied,
            metadata=HumanizerMetadata(...)
        )

    async def _apply_humanization_passes(
        self,
        content: str,
        request: HumanizerRequest,
        score: DetectionScore
    ) -> tuple[str, List[TechniqueApplied]]:
        """Apply multi-pass humanization."""
        techniques = []

        # Pass 1: Structural Variation
        content, tech = await self._structural_variation(content, request)
        techniques.extend(tech)

        # Pass 2: Lexical Substitution
        content, tech = await self._lexical_substitution(content, request)
        techniques.extend(tech)

        # Pass 3: Rhythm & Cadence
        content, tech = await self._rhythm_variation(content, request)
        techniques.extend(tech)

        # Pass 4: Personal Touch
        content, tech = await self._personal_touch(content, request)
        techniques.extend(tech)

        return content, techniques
```

### Writing Pattern Variation Techniques

```python
# src/post_processing/techniques/patterns.py

class PatternVariation:
    """Techniques for varying writing patterns."""

    @staticmethod
    async def structural_variation(content: str, provider: LLMProvider) -> str:
        """Vary sentence and paragraph structure."""
        prompt = f"""
        Rewrite the following content with these structural changes:
        1. Vary sentence lengths - mix very short (5-8 words) with longer (20-30 words)
        2. Occasionally start sentences with "And" or "But"
        3. Use sentence fragments sparingly for emphasis
        4. Vary paragraph lengths significantly
        5. Occasionally use questions to engage the reader

        Content:
        {content}

        Return only the rewritten content.
        """
        return await generate_text(prompt, provider)

    @staticmethod
    async def lexical_substitution(content: str, provider: LLMProvider) -> str:
        """Replace AI-typical phrases with human alternatives."""

        # Common AI patterns to replace
        ai_patterns = {
            r'\bin conclusion\b': ['to wrap up', 'all in all', 'at the end of the day'],
            r'\bfurthermore\b': ['also', 'plus', 'and another thing'],
            r'\bhowever\b': ['but', 'though', 'that said'],
            r'\bmoreover\b': ['what is more', 'on top of that', 'besides'],
            r'\bnevertheless\b': ['still', 'even so', 'yet'],
            r'\bconsequently\b': ['so', 'as a result', 'because of this'],
            r'\bdelve into\b': ['explore', 'look at', 'dig into'],
            r'\bleverage\b': ['use', 'take advantage of', 'make use of'],
            r'\butilize\b': ['use', 'employ', 'work with'],
            r'\bfacilitate\b': ['help', 'make easier', 'enable'],
            r'\bimplement\b': ['put in place', 'set up', 'do'],
        }

        result = content
        for pattern, replacements in ai_patterns.items():
            result = re.sub(
                pattern,
                lambda m: random.choice(replacements),
                result,
                flags=re.IGNORECASE
            )

        return result

    @staticmethod
    async def rhythm_variation(content: str, provider: LLMProvider) -> str:
        """Adjust rhythm and cadence for natural flow."""
        prompt = f"""
        Adjust the rhythm of this content to feel more natural:
        1. Break up any sentences that sound too "perfect"
        2. Add natural pauses with em dashes or ellipses occasionally
        3. Include some parenthetical asides
        4. Make the flow less predictable
        5. Add occasional rhetorical questions

        Do NOT change the meaning or information.

        Content:
        {content}

        Return only the adjusted content.
        """
        return await generate_text(prompt, provider)

    @staticmethod
    async def inject_human_elements(content: str, provider: LLMProvider) -> str:
        """Add human-like elements."""
        prompt = f"""
        Add subtle human touches to this content:
        1. Include 1-2 personal observations or opinions
        2. Add a relatable analogy or metaphor
        3. Include a minor self-correction ("Actually, let me rephrase that...")
        4. Add a touch of appropriate humor if fitting
        5. Reference a hypothetical "I remember when..." moment if appropriate

        Keep changes subtle and natural. Do NOT overdo it.

        Content:
        {content}

        Return only the adjusted content.
        """
        return await generate_text(prompt, provider)
```

### AI Detection Integration

```python
# src/post_processing/detection.py

import aiohttp
from typing import Dict, Any

class AIDetectionClient:
    """Client for multiple AI detection services."""

    def __init__(self):
        self.services = {
            'gptzero': GPTZeroClient(),
            'originality': OriginalityAIClient(),
            'copyleaks': CopyleaksClient(),
        }

    async def analyze(self, content: str) -> DetectionScore:
        """Get detection scores from multiple services."""
        results = {}

        # Query all services in parallel
        tasks = {
            name: client.detect(content)
            for name, client in self.services.items()
        }

        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                results[name] = None

        # Calculate weighted average
        weights = {'gptzero': 0.4, 'originality': 0.4, 'copyleaks': 0.2}
        total_weight = 0
        weighted_sum = 0

        for name, score in results.items():
            if score is not None:
                weighted_sum += score * weights.get(name, 0.3)
                total_weight += weights.get(name, 0.3)

        overall = weighted_sum / total_weight if total_weight > 0 else 50

        return DetectionScore(
            overall=overall,
            gptzero=results.get('gptzero'),
            originality=results.get('originality'),
            copyleaks=results.get('copyleaks'),
            confidence=self._calculate_confidence(results)
        )


class GPTZeroClient:
    """GPTZero API client."""

    BASE_URL = "https://api.gptzero.me/v2/predict"

    async def detect(self, content: str) -> float:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.BASE_URL}/text",
                headers={"x-api-key": os.environ['GPTZERO_API_KEY']},
                json={"document": content}
            ) as response:
                data = await response.json()
                return data['documents'][0]['completely_generated_prob'] * 100
```

### Style Mimicry System

```python
# src/post_processing/style_mimicry.py

class StyleMimicry:
    """Mimic specific writing styles."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.style_analyzer = StyleAnalyzer()

    async def learn_style(self, sample_texts: List[str]) -> WritingStyle:
        """Analyze sample texts to learn writing style."""
        analysis_prompt = f"""
        Analyze these writing samples and identify the key characteristics:

        Samples:
        {chr(10).join(f'---Sample {i+1}---{chr(10)}{text}' for i, text in enumerate(sample_texts))}

        Identify:
        1. Average sentence length and variation
        2. Vocabulary complexity level
        3. Formality level (1-10)
        4. Use of contractions
        5. Common transition words/phrases
        6. Any recurring stylistic patterns
        7. Common "mistakes" or informal elements

        Return as JSON.
        """

        response = await generate_text(analysis_prompt, self.provider)
        characteristics = json.loads(response)

        return WritingStyle(
            name="Custom Style",
            characteristics=StyleCharacteristics(**characteristics),
            sample_texts=sample_texts
        )

    async def apply_style(self, content: str, style: WritingStyle) -> str:
        """Rewrite content in the target style."""
        prompt = f"""
        Rewrite this content to match the following writing style:

        Style characteristics:
        - Sentence variation: {style.characteristics.sentence_length_variation}
        - Vocabulary: {style.characteristics.vocabulary_complexity}
        - Formality: {style.characteristics.formality_level}/10
        - Uses contractions: {style.characteristics.use_of_contractions}
        - Typical transitions: {', '.join(style.characteristics.preferred_transitions)}

        Sample of target style:
        {style.sample_texts[0] if style.sample_texts else 'Not provided'}

        Content to rewrite:
        {content}

        Maintain the same information but adjust the style.
        """

        return await generate_text(prompt, self.provider)
```

### API Endpoints

```yaml
POST /api/v1/humanizer/analyze:
  description: Analyze content for AI detection
  auth: required
  body:
    content: string
  response:
    score: DetectionScore

POST /api/v1/humanizer/humanize:
  description: Humanize content
  auth: required (Pro plan)
  body:
    content: string
    intensity: 'light' | 'moderate' | 'aggressive'
    targetScore?: number
    preserveKeywords?: string[]
  response:
    humanizedContent: string
    preScore: DetectionScore
    postScore: DetectionScore
    iterations: number

POST /api/v1/humanizer/style/learn:
  description: Learn a writing style from samples
  auth: required (Pro plan)
  body:
    sampleTexts: string[]
  response:
    styleId: string
    characteristics: StyleCharacteristics

POST /api/v1/humanizer/style/apply:
  description: Apply learned style to content
  auth: required (Pro plan)
  body:
    content: string
    styleId: string
  response:
    styledContent: string
```

### Database Schema

```sql
-- Migration: 014_create_humanizer_tables.sql

-- Learned writing styles
CREATE TABLE writing_styles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    characteristics JSONB NOT NULL,
    sample_texts TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Humanization history
CREATE TABLE humanization_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_content TEXT NOT NULL,
    humanized_content TEXT NOT NULL,
    pre_score JSONB NOT NULL,
    post_score JSONB NOT NULL,
    intensity TEXT NOT NULL,
    iterations INTEGER NOT NULL,
    techniques JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Detection cache (avoid repeated API calls)
CREATE TABLE detection_cache (
    content_hash TEXT PRIMARY KEY,
    scores JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_writing_styles_user ON writing_styles(user_id);
CREATE INDEX idx_humanization_history_user ON humanization_history(user_id);
CREATE INDEX idx_detection_cache_expires ON detection_cache(expires_at);
```

### Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| aiohttp | 3.x | Async HTTP client for detection APIs |
| nltk | 3.x | Natural language processing |
| spacy | 3.x | Advanced NLP for style analysis |

### Ethical Considerations and Guardrails

```python
# src/post_processing/ethics.py

class HumanizerGuardrails:
    """Ethical guardrails for humanization feature."""

    PROHIBITED_USES = [
        'academic_submission',
        'plagiarism',
        'fraud',
        'deception',
    ]

    def __init__(self):
        self.content_classifier = ContentClassifier()

    async def check_content(self, content: str, user_context: dict) -> GuardrailResult:
        """Check if humanization request is ethical."""

        # Check for academic content
        if await self._is_academic_content(content):
            return GuardrailResult(
                allowed=False,
                reason="Academic content detected. Humanization for academic submissions violates academic integrity policies.",
                suggestion="Consider using our proofreading feature instead."
            )

        # Check for prohibited patterns
        prohibited = await self._check_prohibited_patterns(content)
        if prohibited:
            return GuardrailResult(
                allowed=False,
                reason=f"Content appears to be intended for {prohibited}.",
                suggestion="This use case is not supported."
            )

        # Log for audit
        await self._log_humanization_request(content, user_context)

        return GuardrailResult(allowed=True)

    async def _is_academic_content(self, content: str) -> bool:
        """Detect academic/essay content."""
        academic_signals = [
            'thesis statement',
            'in this essay',
            'works cited',
            'bibliography',
            'as per the assignment',
            'professor',
            'term paper',
        ]
        content_lower = content.lower()
        return any(signal in content_lower for signal in academic_signals)
```

### Security Considerations

1. **Rate Limiting**: Strict limits on detection API calls (expensive)
2. **Abuse Prevention**: Block academic and fraudulent use cases
3. **Audit Logging**: All humanization requests logged
4. **Content Classification**: ML-based detection of prohibited uses
5. **User Verification**: Pro plan required, linked to identity
6. **Ethical Guidelines**: Clear ToS prohibiting misuse

### Complexity Assessment

| Aspect | Complexity | Rationale |
|--------|------------|-----------|
| Detection Integration | Medium | Multiple API integrations |
| Pattern Variation | High | Complex NLP techniques |
| Style Mimicry | High | ML-based style learning |
| Iterative Improvement | Medium | Standard feedback loop |
| Ethics/Guardrails | Medium | Important but manageable |
| **Overall** | **High** | Novel ML/NLP work |

**Estimated Development Time**: 6-8 weeks

---

## Summary: Implementation Priority Matrix

| Feature | Complexity | Est. Time | Dependencies | Priority |
|---------|------------|-----------|--------------|----------|
| F13: Publishing Integrations | High | 6-8 weeks | OAuth, Celery | High |
| F11: Browser Extension | High | 4-6 weeks | Auth system | Medium |
| F12: Team Collaboration | Very High | 8-12 weeks | Database migration | Medium |
| F14: Content Marketplace | High | 8-10 weeks | Stripe Connect | Low |
| F15: Humanizer Pro | High | 6-8 weeks | Detection APIs | Low |

### Recommended Implementation Order

1. **F13: Publishing Integrations** - Extends existing integration pattern
2. **F12: Team Collaboration** - Foundation for other features
3. **F11: Browser Extension** - Requires auth system from F12
4. **F15: Humanizer Pro** - Independent, can parallel develop
5. **F14: Content Marketplace** - Requires user base for viability

### Total Estimated Development Time

- **Conservative**: 40-52 weeks (1 engineer)
- **With Team (3 engineers)**: 16-20 weeks
- **Recommended Approach**: Phase over 2-3 quarters with incremental releases
