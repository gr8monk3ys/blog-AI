# ✨ Blog AI Generation Tool

Welcome to the **Blog AI Generation Tool** – a smart, AI-driven solution designed to streamline the process of writing blog posts and even entire books. Harness the power of **GPT-4** and advanced AI techniques to transform your ideas into well-structured, SEO-friendly content with minimal effort.

## 🌟 Key Features

- **📝 Blog Post Generation**: Create structured, SEO-optimized blog posts with a single command.
- **📚 Book Creation**: Generate full-length books with chapters, sections, and consistent style.
- **📅 Content Planning**: Plan your content with calendars, topic clusters, and outlines.
- **🔍 Competitor Analysis**: Analyze competitors to identify content gaps and opportunities.
- **🔎 Web Research**: Conduct research to enhance content with accurate information.
- **🔄 Post-Processing**: Proofread, humanize, and format your content for various platforms.
- **🔌 Integrations**: Publish directly to WordPress, GitHub, and Medium.
- **🤖 Modern AI Integration**: Built on GPT-4 for reliable, high-quality content output.

## 🗂️ Project Structure

```
blog-AI/
├── src/                      # Source code
│   ├── blog/                 # Blog generation modules
│   ├── book/                 # Book generation modules
│   ├── blog_sections/        # Blog section generators
│   ├── planning/             # Content planning tools
│   │   ├── content_calendar.py  # Content calendar generation
│   │   ├── competitor_analysis.py # Competitor analysis
│   │   ├── topic_clusters.py # Topic cluster generation
│   │   └── content_outline.py # Content outline generation
│   ├── research/             # Research tools
│   ├── seo/                  # SEO optimization tools
│   ├── integrations/         # Publishing integrations
│   │   ├── github.py         # GitHub integration
│   │   ├── medium.py         # Medium integration
│   │   └── wordpress.py      # WordPress integration
│   ├── post_processing/      # Content post-processing
│   ├── text_generation/      # Text generation core
│   └── types/                # Type definitions
├── tests/                    # Test files
├── frontend/                 # Web interface (Next.js)
├── .env                      # Environment configuration
├── .env.example              # Example environment configuration
├── pyproject.toml            # Project dependencies
├── LICENSE                   # License information
└── README.md                 # Project documentation
```

## 🚀 Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/blog-AI.git
   ```
   
2. **Configure environment**:  
   Create a `.env` file based on `.env.example` and add your API keys:
   ```bash
   # Required for basic functionality
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Optional - for additional features
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   SERP_API_KEY=your_serp_api_key_here
   SEC_API_API_KEY=your_sec_api_key_here
   ```
   
3. **Install dependencies**:
   Using Poetry (recommended):
   ```bash
   poetry install
   ```
   
   Or using pip:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the backend server** (required for the web interface):
   ```bash
   python server.py
   ```
   This will start the server at http://localhost:8000

5. **Start the frontend** (optional, for web interface):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   This will start the frontend at http://localhost:3000

6. **You're all set!** The tool is now ready to generate content at your command.

## 🐳 Docker Setup

You can also run the application using Docker, which simplifies the setup process:

1. **Build and start the containers**:
   ```bash
   docker-compose up -d
   ```

2. **Configure environment**:  
   Before starting the containers, make sure to create a `.env` file based on `.env.example` with your API keys.

3. **Access the application**:
   - Backend API: http://localhost:8000
   - Frontend: http://localhost:3000

4. **Stop the containers**:
   ```bash
   docker-compose down
   ```

### Docker Commands

- **View logs**:
  ```bash
  docker-compose logs -f
  ```

- **Rebuild the containers** (after making changes):
  ```bash
  docker-compose up -d --build
  ```

- **Run a command inside the container**:
  ```bash
  docker-compose exec blog-ai bash
  ```

## 💻 Usage

### Generate a Blog Post

```bash
python -m src.blog.make_blog "Your Blog Topic" --keywords "keyword1,keyword2" --research
```

This command creates a fully formatted blog post and saves it under the `content/blog/` directory.

**Optional Parameters**:  
- `--keywords`: Comma-separated list of keywords to include
- `--research`: Enable web research for more accurate content
- `--tone`: Set the tone of the content (default: "informative")
- `--output`: Specify the output filename and format (default: markdown)
- `--proofread`: Enable proofreading
- `--humanize`: Make the content more human-like

### Generate a Book

```bash
python -m src.book.make_book "Your Book Topic" --chapters 5 --sections 3 --output "book_name.md"
```

**Optional Parameters**:  
- `--chapters`: Number of chapters to generate (default: 5)
- `--sections`: Number of sections per chapter (default: 3)
- `--keywords`: Comma-separated list of keywords to include
- `--research`: Enable web research for more accurate content
- `--tone`: Set the tone of the content (default: "informative")
- `--output`: Specify the output filename and format
- `--proofread`: Enable proofreading
- `--humanize`: Make the content more human-like

### Content Planning

```bash
# Generate a content calendar
python -m src.planning.content_calendar "Your Niche" --timeframe month --frequency 7

# Analyze competitors
python -m src.planning.competitor_analysis "Your Niche" --competitors "Competitor1,Competitor2"

# Generate topic clusters
python -m src.planning.topic_clusters "Your Niche" --clusters 3 --subtopics 5

# Create content outlines
python -m src.planning.content_outline "Your Topic" --keywords "keyword1,keyword2" --sections 5
```

### Publishing Integrations

```bash
# Publish to WordPress
python -m src.integrations.wordpress "Your Blog Post" --url "https://yourblog.com" --username "user" --password "pass"

# Publish to GitHub
python -m src.integrations.github "Your Blog Post" --repo "username/repo" --token "github_token"

# Publish to Medium
python -m src.integrations.medium "Your Blog Post" --token "medium_token" --tags "tag1,tag2"
```

## 🧪 Testing

Run the test suite to ensure everything is working correctly:

```bash
python -m unittest discover tests
```

## 🔧 Troubleshooting

If you encounter any issues while setting up or using the Blog AI Generation Tool, please refer to the [Troubleshooting Guide](troubleshooting.md) for solutions to common problems.

## ⚙️ Dependencies

- **openai**: OpenAI API client for text generation
- **anthropic**: Anthropic API client for Claude models
- **google-generativeai**: Google's Gemini API client
- **requests**: HTTP requests for API interactions
- **pydantic**: Data validation and settings management
- **python-dotenv**: Environment variable management
- **fastapi**: Backend API framework
- **uvicorn**: ASGI server for FastAPI
- **websockets**: WebSocket support for real-time communication

## 📜 License

This project is available under the [MIT License](LICENSE). Feel free to explore, fork, and contribute!

**Happy Writing!** 🎉 Turn your ideas into captivating blog posts or fully-fledged books with minimal hassle—just let the AI do the heavy lifting.
