---
name: mcp-builder
description: Use this skill when creating Model Context Protocol (MCP) servers, adding tools to extend Claude's capabilities, or integrating external APIs as MCP tools.
---

# MCP Builder Skill

You have expertise in building Model Context Protocol servers to extend Claude's capabilities.

## When to Use

This skill activates for:
- Creating new MCP servers
- Adding tools to existing servers
- Integrating external APIs as MCP tools
- Configuring MCP servers in Claude Desktop/Code
- Debugging MCP server issues

## MCP Server Quickstart

### Project Setup
```bash
mkdir my-mcp-server && cd my-mcp-server
npm init -y
npm install @modelcontextprotocol/sdk zod
npm install -D typescript @types/node
```

### Minimal Server Template
```typescript
// src/index.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "my-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// Define tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "my_tool",
      description: "What this tool does and when Claude should use it",
      inputSchema: {
        type: "object",
        properties: {
          param: { type: "string", description: "Parameter description" }
        },
        required: ["param"]
      }
    }
  ]
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "my_tool") {
    const { param } = request.params.arguments as { param: string };
    return {
      content: [{ type: "text", text: `Result for: ${param}` }]
    };
  }
  throw new Error(`Unknown tool: ${request.params.name}`);
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

### package.json
```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "bin": { "my-mcp-server": "./dist/index.js" },
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js"
  }
}
```

### tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["src/**/*"]
}
```

## Tool Design Patterns

### API Wrapper Tool
```typescript
{
  name: "api_search",
  description: "Search the [Service] API. Use when user asks to find [things].",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string", description: "Search query" },
      limit: { type: "number", description: "Max results (1-100)", default: 10 }
    },
    required: ["query"]
  }
}
```

### Database Query Tool
```typescript
{
  name: "db_query",
  description: "Execute a read-only SQL query against the database.",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string", description: "SELECT query (read-only)" },
      params: { type: "array", items: { type: "string" }, description: "Query parameters" }
    },
    required: ["query"]
  }
}
```

### File Operation Tool
```typescript
{
  name: "file_read",
  description: "Read contents of a file within the allowed directory.",
  inputSchema: {
    type: "object",
    properties: {
      path: { type: "string", description: "Relative file path" }
    },
    required: ["path"]
  }
}
```

## Input Validation

```typescript
import { z } from "zod";

const SearchSchema = z.object({
  query: z.string().min(1).max(500),
  limit: z.number().min(1).max(100).default(10),
  filters: z.object({
    type: z.enum(["all", "recent", "popular"]).optional()
  }).optional()
});

// In handler
const validated = SearchSchema.parse(request.params.arguments);
```

## Error Handling

```typescript
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";

// Validation error
throw new McpError(ErrorCode.InvalidParams, "Query cannot be empty");

// Not found
throw new McpError(ErrorCode.InvalidRequest, "Resource not found");

// Internal error
throw new McpError(ErrorCode.InternalError, "API request failed");
```

## Configuration

### Claude Desktop (~/.claude/claude_desktop_config.json)
```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/path/to/dist/index.js"],
      "env": {
        "API_KEY": "your-key"
      }
    }
  }
}
```

### Published Package
```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "@yourorg/my-mcp-server"],
      "env": { "API_KEY": "your-key" }
    }
  }
}
```

## Best Practices

1. **Clear Descriptions** - Help Claude understand when to use each tool
2. **Validate Everything** - Use Zod for input validation
3. **Handle Errors Gracefully** - Return meaningful error messages
4. **Environment Variables** - Never hardcode secrets
5. **Rate Limiting** - Protect against excessive API calls
6. **Logging** - Log to stderr for debugging (stdout is for MCP protocol)

## Common Integrations

| Service | Package | Use Case |
|---------|---------|----------|
| GitHub | `@octokit/rest` | Repository operations |
| Slack | `@slack/web-api` | Team communication |
| Notion | `@notionhq/client` | Workspace management |
| Stripe | `stripe` | Payment operations |
| Supabase | `@supabase/supabase-js` | Database & auth |
| OpenAI | `openai` | AI operations |
