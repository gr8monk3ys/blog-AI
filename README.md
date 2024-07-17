# Project Overview

This project is designed to automate the creation of blog posts and books using OpenAI's GPT-4 model. It leverages various libraries and APIs to fetch content, generate titles, descriptions, outlines, and full articles or book chapters.

## Table of Contents
- [Project Overview](#project-overview)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Environment Variables](#environment-variables)
    - [make\_mdx.py](#make_mdxpy)
    - [make\_book.py](#make_bookpy)
  - [License](#license)

## Installation

To install the required dependencies, run:

```bash
pip install -r requirements.txt
```

## Usage

### Environment Variables

Ensure you have a `OPENAI_API_KEY` environment variable set with your OpenAI API key.

### make_mdx.py

This script generates a blog post in Markdown format. It takes the following arguments:

- `topic`: The topic of the blog post.
- `length`: The desired length of the blog post in words.

Example usage:

```bash
python make_mdx.py --topic "Artificial Intelligence" --length 500
```

### make_book.py

This script generates a book in Markdown format. It takes the following arguments:

- `title`: The title of the book.
- `chapters`: The number of chapters to generate.
- `length`: The desired length of each chapter in words.

Example usage:

```bash
python make_book.py --title "The Future of AI" --chapters 5 --length 1000
```

## License

This project is licensed under the [MIT License](LICENSE).
