# Blog AI Generation Tool

An AI-powered tool for generating blog posts and books using GPT-4 and LangChain.

## Features

- **Blog Post Generation**: Generate SEO-optimized blog posts with structured content
- **Book Generation**: Create complete books with chapters and sections
- **Modern AI Integration**: Uses GPT-4 via LangChain for high-quality content
- **Clean Output**: Generates content in MDX format for blog posts and DOCX for books

## Project Structure

```
blog-AI/
├── src/                  # Source code
│   ├── make_book.py     # Book generation script
│   └── make_mdx.py      # Blog post generation script
├── content/             # Generated content
│   ├── blog/           # Blog posts
│   └── books/          # Generated books
├── tests/              # Test files
├── .env                # Environment configuration
├── .env.example        # Example environment configuration
├── requirements.txt    # Project dependencies
├── LICENSE            # License information
└── README.md          # Project documentation
```

## Setup

1. Clone the repository
2. Create a `.env` file based on `.env.example`
3. Add your OpenAI API key to `.env`:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Generate a Blog Post

```bash
python src/make_mdx.py "Your Blog Topic"
```

### Generate a Book

```bash
python src/make_book.py "Your Book Topic" --output "book_name.docx"
```

Optional parameters:
- `--output`: Specify output filename (default: book.docx)
- `--model`: Specify OpenAI model (default: gpt-4)

## Dependencies

- langchain
- langchain-openai
- python-docx
- pydantic
- python-dotenv

## License

See [LICENSE](LICENSE) file for details.
