# Blog-AI Frontend

This is the frontend for the Blog-AI application, which provides a user interface for generating and managing blog posts and books using AI.

## Features

- **Blog Post Generation**: Create high-quality blog posts on any topic with customizable options
- **Book Generation**: Generate complete books with chapters and topics
- **Content Editing**: Edit generated content with an intuitive interface
- **Conversation History**: Track your interactions with the AI
- **Download Options**: Export your content in different formats

## Components

### Content Generation

- **ContentGenerator**: UI for generating blog posts with options for tone, research, proofreading, and humanization
- **BookGenerator**: UI for generating books with options for number of chapters, sections per chapter, and more

### Content Viewing and Editing

- **ContentViewer**: Displays generated content based on its type (blog or book)
- **BookViewer**: Specialized component for viewing books with chapter navigation
- **BookEditor**: Full-featured editor for modifying book content, including chapter titles and topic content

## Type Definitions

The application uses TypeScript for type safety. Key type definitions include:

### Blog Types

- `Section`: Represents a section of a blog post with an ID and content
- `BlogPost`: Represents a complete blog post with title, sections, tags, and date
- `BlogGenerationOptions`: Options for generating a blog post

### Book Types

- `Topic`: Represents a topic within a chapter with title and content
- `Chapter`: Represents a chapter with number, title, and topics
- `Book`: Represents a complete book with title, chapters, tags, and date
- `BookGenerationOptions`: Options for generating a book

## Getting Started

1. Install dependencies:
   ```
   npm install
   ```

2. Run the development server:
   ```
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

## API Integration

The frontend communicates with the backend API to generate and manage content. Key endpoints include:

- `/generate-blog`: Generate a blog post
- `/generate-book`: Generate a book
- `/edit-section`: Edit a section of content
- `/save-book`: Save changes to a book
- `/download-book`: Download a book in different formats

## Technologies Used

- Next.js
- React
- TypeScript
- Tailwind CSS
- Headless UI
