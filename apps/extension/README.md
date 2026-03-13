# Blog AI Browser Extension

This extension lets users send webpage context into Blog AI without leaving the current tab.

## What It Does

- captures selected text from a page
- opens quick generation actions from the popup or context menu
- sends requests to the Blog AI API using the user’s API key

## Local Setup

1. Open `chrome://extensions/`.
2. Enable `Developer mode`.
3. Click `Load unpacked`.
4. Select [`apps/extension`](/workspaces/blog-AI/apps/extension).

## Configuration

The extension needs:

- a reachable Blog AI API base URL
- a valid user API key

By default it is configured for local development against `http://localhost:8000`.

## Build

From [`apps/extension`](/workspaces/blog-AI/apps/extension):

```bash
chmod +x build.sh
./build.sh
```

That creates a distributable zip for browser-store submission or manual distribution.

## Structure

```text
apps/extension/
  background/
  content/
  lib/
  options/
  popup/
  build.sh
  manifest.json
```
