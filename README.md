# ✨ Blog AI Generation Tool

Welcome to the **Blog AI Generation Tool** – a smart, AI-driven solution designed to streamline the process of writing blog posts and even entire books. Harness the power of **GPT-4** and **LangChain** to transform your ideas into well-structured, SEO-friendly content with minimal effort.

## 🌟 Key Features

- **📝 Blog Post Generation**: Create structured, SEO-optimized blog posts in MDX format with a single command.  
- **📚 Book Creation**: Generate full-length books with chapters, sections, and consistent style, saved as DOCX files.  
- **🤖 Modern AI Integration**: Built on GPT-4 and LangChain for reliable, high-quality content output.  
- **💎 Clean Output**: Produce polished MDX for blogs and DOCX for books—perfect for publishing or further editing.

## 🗂️ Project Structure

```
blog-AI/
├── src/                  # Source code
│   ├── make_book.py      # Book generation script
│   └── make_mdx.py       # Blog post generation script
├── content/              # Generated content
│   ├── blog/             # Blog posts
│   └── books/            # Generated books
├── tests/                # Test files
├── .env                  # Environment configuration
├── .env.example          # Example environment configuration
├── requirements.txt      # Project dependencies
├── LICENSE               # License information
└── README.md             # Project documentation
```

## 🚀 Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/blog-AI.git
   ```
   
2. **Configure environment**:  
   Create a `.env` file based on `.env.example` and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=your_api_key_here
   ```
   
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **You’re all set!** The tool is now ready to generate content at your command.

## 💻 Usage

### Generate a Blog Post (MDX)

```bash
python src/make_mdx.py "Your Blog Topic"
```

This command creates a fully formatted blog post in MDX format and saves it under the `content/blog/` directory.

### Generate a Book (DOCX)

```bash
python src/make_book.py "Your Book Topic" --output "book_name.docx"
```

**Optional Parameters**:  
- `--output`: Specify the output filename (default: `book.docx`)  
- `--model`: Choose the OpenAI model (default: `gpt-4`)

## ⚙️ Dependencies

- **langchain**  
- **langchain-openai**  
- **python-docx**  
- **pydantic**  
- **python-dotenv**

These libraries ensure a smooth and scalable workflow for text generation and file handling.

## 📜 License

This project is available under the [MIT License](LICENSE). Feel free to explore, fork, and contribute!

**Happy Writing!** 🎉 Turn your ideas into captivating blog posts or fully-fledged books with minimal hassle—just let the AI do the heavy lifting.
