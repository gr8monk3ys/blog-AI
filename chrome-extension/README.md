# Blog AI Chrome Extension

A Chrome extension that allows you to generate AI-powered blog content from any webpage. Highlight text, right-click, and create content instantly.

## Features

- **Text Selection Detection**: Highlight any text on a webpage to generate content based on it
- **Context Menu Integration**: Right-click to access quick generation options
- **Popup Interface**: Full-featured popup with generation options and history
- **Multiple Content Types**: Generate blog posts, outlines, summaries, and expanded articles
- **Customizable Settings**: Configure default tone, length, and processing options
- **Dark Mode Support**: Automatic theme switching based on system preferences

## Installation

### Developer Mode (Recommended for Development)

1. Clone this repository or download the `chrome-extension` folder
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable **Developer mode** (toggle in top right)
4. Click **Load unpacked**
5. Select the `chrome-extension` folder
6. The extension icon will appear in your toolbar

### Chrome Web Store (Production)

The extension will be available on the Chrome Web Store after approval.

## Setup

### Getting Your API Key

1. Sign up or log in at [blogai.com](https://blogai.com)
2. Navigate to your [Dashboard](https://blogai.com/dashboard)
3. Go to **Settings** > **API Keys**
4. Click **Generate New Key**
5. Copy the API key (it will only be shown once)

### Configuring the Extension

1. Click the Blog AI extension icon in your toolbar
2. Enter your API key in the input field
3. Click **Connect**
4. Once connected, you can start generating content!

## Usage

### From the Popup

1. Click the extension icon
2. Enter a topic or paste text
3. Select tone, length, and options
4. Click **Generate**

### Using Text Selection

1. Highlight any text on a webpage
2. A floating button will appear near your selection
3. Click the button or right-click and select "Generate with Blog AI"
4. Choose your generation type:
   - **Generate Blog Post**: Create a full blog article
   - **Create Outline**: Generate a content outline
   - **Summarize**: Create a concise summary
   - **Expand into Article**: Transform short text into a longer piece

### Keyboard Shortcuts

- Select text + `Alt+G`: Quick generate (if enabled in settings)

## Configuration Options

Access settings by clicking the gear icon in the popup or going to the extension options page.

### Default Settings

| Setting | Options | Description |
|---------|---------|-------------|
| Default Tone | Professional, Casual, Formal, Friendly, Authoritative, Conversational | Writing style for generated content |
| Default Length | Short (~500), Medium (~1000), Long (~2000) | Approximate word count |
| Include Research | On/Off | Automatically research topics before generating |
| Enable Proofreading | On/Off | Proofread content after generation |

### Advanced Settings

| Setting | Description |
|---------|-------------|
| API Endpoint | Custom API server URL (for self-hosted instances) |
| Theme | System, Light, or Dark mode |

## Building for Production

### Prerequisites

- Bash shell (Linux/macOS) or Git Bash (Windows)
- zip command-line utility

### Build Steps

```bash
cd chrome-extension

# Make the build script executable
chmod +x build.sh

# Run the build script
./build.sh
```

This will create a `blog-ai-extension-v1.0.0.zip` file ready for Chrome Web Store submission.

### Manual Build

```bash
cd chrome-extension

# Create a zip file excluding development files
zip -r blog-ai-extension.zip . \
  -x "*.git*" \
  -x "*.DS_Store" \
  -x "build.sh" \
  -x "README.md" \
  -x "*.map"
```

## Development

### Project Structure

```
chrome-extension/
├── manifest.json          # Extension manifest (Manifest V3)
├── popup/
│   ├── popup.html         # Popup UI
│   ├── popup.css          # Popup styles
│   └── popup.js           # Popup logic
├── background/
│   └── service-worker.js  # Background service worker
├── content/
│   ├── content.js         # Content script
│   └── content.css        # Content script styles
├── options/
│   ├── options.html       # Options page
│   └── options.js         # Options logic
├── lib/
│   └── api.js             # API client library
├── icons/
│   └── *.png              # Extension icons
├── build.sh               # Build script
└── README.md              # This file
```

### Local Development

1. Make changes to the source files
2. Go to `chrome://extensions/`
3. Click the refresh icon on the Blog AI extension card
4. Test your changes

### API Endpoints Used

The extension communicates with the following Blog AI API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/extension/auth` | POST | Verify API key |
| `/extension/user` | GET | Get user info |
| `/extension/generate` | POST | Generate content |
| `/extension/usage` | GET | Get usage statistics |

## Permissions

The extension requires the following permissions:

| Permission | Reason |
|------------|--------|
| `activeTab` | Access the current tab for text selection |
| `storage` | Store API key and settings |
| `contextMenus` | Add right-click menu items |
| `notifications` | Show generation status notifications |

### Host Permissions

- `http://localhost:8000/*` - Local development API
- `https://api.blogai.com/*` - Production API

## Troubleshooting

### Extension Not Working

1. Ensure you're on a regular webpage (not `chrome://` pages)
2. Try refreshing the page
3. Check that your API key is valid
4. Verify your internet connection

### "Cannot access this page" Error

The extension cannot run on:
- Chrome internal pages (`chrome://`, `chrome-extension://`)
- Chrome Web Store pages
- Some protected pages

### Generation Failing

1. Check your API key is valid
2. Verify you have remaining quota
3. Try a shorter text selection
4. Check the console for error details (F12 > Console)

### Dark Mode Not Working

Ensure your system's color scheme preference is set correctly, or manually select a theme in the extension settings.

## Privacy

- Your API key is stored locally and never shared
- Selected text is sent to Blog AI servers only when you initiate generation
- No browsing data is collected or transmitted
- See our [Privacy Policy](https://blogai.com/privacy) for details

## Support

- **Documentation**: [docs.blogai.com](https://docs.blogai.com)
- **Email**: support@blogai.com
- **Issues**: [GitHub Issues](https://github.com/blogai/extension/issues)

## License

Copyright 2024 Blog AI. All rights reserved.
