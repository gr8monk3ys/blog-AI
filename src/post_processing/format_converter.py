"""
Format conversion functionality.
"""
import os
from typing import Optional, Dict, Any

from ..types.post_processing import FormatConversionOptions, OutputFormat


class FormatConversionError(Exception):
    """Exception raised for errors in the format conversion process."""
    pass


def convert_format(
    content: str,
    options: FormatConversionOptions
) -> str:
    """
    Convert content from one format to another.
    
    Args:
        content: The content to convert.
        options: Options for format conversion.
        
    Returns:
        The converted content.
        
    Raises:
        FormatConversionError: If an error occurs during format conversion.
    """
    try:
        source_format = options.source_format.lower()
        target_format = options.target_format.lower()
        
        # If source and target formats are the same, return the content as is
        if source_format == target_format:
            return content
        
        # Convert from source format to target format
        if source_format == "markdown" and target_format == "html":
            return markdown_to_html(content, options.include_metadata)
        elif source_format == "markdown" and target_format == "docx":
            return markdown_to_docx(content, options.include_metadata, options.include_images)
        elif source_format == "markdown" and target_format == "pdf":
            return markdown_to_pdf(content, options.include_metadata, options.include_images)
        elif source_format == "html" and target_format == "markdown":
            return html_to_markdown(content, options.include_metadata)
        elif source_format == "html" and target_format == "docx":
            return html_to_docx(content, options.include_metadata, options.include_images)
        elif source_format == "html" and target_format == "pdf":
            return html_to_pdf(content, options.include_metadata, options.include_images)
        elif source_format == "docx" and target_format == "markdown":
            return docx_to_markdown(content, options.include_metadata)
        elif source_format == "docx" and target_format == "html":
            return docx_to_html(content, options.include_metadata, options.include_images)
        elif source_format == "docx" and target_format == "pdf":
            return docx_to_pdf(content, options.include_metadata, options.include_images)
        else:
            raise FormatConversionError(f"Unsupported conversion: {source_format} to {target_format}")
    except Exception as e:
        raise FormatConversionError(f"Error converting format: {str(e)}")


def markdown_to_html(content: str, include_metadata: bool = True) -> str:
    """
    Convert Markdown to HTML.
    
    Args:
        content: The Markdown content to convert.
        include_metadata: Whether to include metadata in the output.
        
    Returns:
        The HTML content.
        
    Raises:
        FormatConversionError: If an error occurs during conversion.
    """
    try:
        import markdown
        
        # Extract metadata if needed
        metadata = {}
        if include_metadata:
            content, metadata = extract_markdown_metadata(content)
        
        # Convert Markdown to HTML
        html = markdown.markdown(content, extensions=['extra', 'codehilite', 'tables'])
        
        # Add metadata to HTML if needed
        if include_metadata and metadata:
            html = add_html_metadata(html, metadata)
        
        return html
    except ImportError:
        raise FormatConversionError("Markdown package not installed. Install it with 'pip install markdown'.")
    except Exception as e:
        raise FormatConversionError(f"Error converting Markdown to HTML: {str(e)}")


def markdown_to_docx(content: str, include_metadata: bool = True, include_images: bool = True) -> str:
    """
    Convert Markdown to DOCX.
    
    Args:
        content: The Markdown content to convert.
        include_metadata: Whether to include metadata in the output.
        include_images: Whether to include images in the output.
        
    Returns:
        The path to the generated DOCX file.
        
    Raises:
        FormatConversionError: If an error occurs during conversion.
    """
    try:
        import tempfile
        import subprocess
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as md_file:
            md_file.write(content.encode("utf-8"))
            md_file_path = md_file.name
        
        docx_file_path = md_file_path.replace(".md", ".docx")
        
        # Use pandoc to convert Markdown to DOCX
        cmd = ["pandoc", md_file_path, "-o", docx_file_path]
        
        if not include_metadata:
            cmd.append("--standalone")
        
        if not include_images:
            cmd.append("--extract-media=.")
        
        subprocess.run(cmd, check=True)
        
        # Clean up temporary Markdown file
        os.remove(md_file_path)
        
        return docx_file_path
    except ImportError:
        raise FormatConversionError("Pandoc not installed. Install it from https://pandoc.org/installing.html.")
    except Exception as e:
        raise FormatConversionError(f"Error converting Markdown to DOCX: {str(e)}")


def markdown_to_pdf(content: str, include_metadata: bool = True, include_images: bool = True) -> str:
    """
    Convert Markdown to PDF.
    
    Args:
        content: The Markdown content to convert.
        include_metadata: Whether to include metadata in the output.
        include_images: Whether to include images in the output.
        
    Returns:
        The path to the generated PDF file.
        
    Raises:
        FormatConversionError: If an error occurs during conversion.
    """
    try:
        import tempfile
        import subprocess
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as md_file:
            md_file.write(content.encode("utf-8"))
            md_file_path = md_file.name
        
        pdf_file_path = md_file_path.replace(".md", ".pdf")
        
        # Use pandoc to convert Markdown to PDF
        cmd = ["pandoc", md_file_path, "-o", pdf_file_path]
        
        if not include_metadata:
            cmd.append("--standalone")
        
        if not include_images:
            cmd.append("--extract-media=.")
        
        subprocess.run(cmd, check=True)
        
        # Clean up temporary Markdown file
        os.remove(md_file_path)
        
        return pdf_file_path
    except ImportError:
        raise FormatConversionError("Pandoc not installed. Install it from https://pandoc.org/installing.html.")
    except Exception as e:
        raise FormatConversionError(f"Error converting Markdown to PDF: {str(e)}")


def html_to_markdown(content: str, include_metadata: bool = True) -> str:
    """
    Convert HTML to Markdown.
    
    Args:
        content: The HTML content to convert.
        include_metadata: Whether to include metadata in the output.
        
    Returns:
        The Markdown content.
        
    Raises:
        FormatConversionError: If an error occurs during conversion.
    """
    try:
        import html2text
        
        # Extract metadata if needed
        metadata = {}
        if include_metadata:
            content, metadata = extract_html_metadata(content)
        
        # Convert HTML to Markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_tables = False
        h.body_width = 0
        
        markdown_content = h.handle(content)
        
        # Add metadata to Markdown if needed
        if include_metadata and metadata:
            markdown_content = add_markdown_metadata(markdown_content, metadata)
        
        return markdown_content
    except ImportError:
        raise FormatConversionError("HTML2Text package not installed. Install it with 'pip install html2text'.")
    except Exception as e:
        raise FormatConversionError(f"Error converting HTML to Markdown: {str(e)}")


def html_to_docx(content: str, include_metadata: bool = True, include_images: bool = True) -> str:
    """
    Convert HTML to DOCX.
    
    Args:
        content: The HTML content to convert.
        include_metadata: Whether to include metadata in the output.
        include_images: Whether to include images in the output.
        
    Returns:
        The path to the generated DOCX file.
        
    Raises:
        FormatConversionError: If an error occurs during conversion.
    """
    try:
        import tempfile
        import subprocess
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as html_file:
            html_file.write(content.encode("utf-8"))
            html_file_path = html_file.name
        
        docx_file_path = html_file_path.replace(".html", ".docx")
        
        # Use pandoc to convert HTML to DOCX
        cmd = ["pandoc", html_file_path, "-o", docx_file_path]
        
        if not include_metadata:
            cmd.append("--standalone")
        
        if not include_images:
            cmd.append("--extract-media=.")
        
        subprocess.run(cmd, check=True)
        
        # Clean up temporary HTML file
        os.remove(html_file_path)
        
        return docx_file_path
    except ImportError:
        raise FormatConversionError("Pandoc not installed. Install it from https://pandoc.org/installing.html.")
    except Exception as e:
        raise FormatConversionError(f"Error converting HTML to DOCX: {str(e)}")


def html_to_pdf(content: str, include_metadata: bool = True, include_images: bool = True) -> str:
    """
    Convert HTML to PDF.
    
    Args:
        content: The HTML content to convert.
        include_metadata: Whether to include metadata in the output.
        include_images: Whether to include images in the output.
        
    Returns:
        The path to the generated PDF file.
        
    Raises:
        FormatConversionError: If an error occurs during conversion.
    """
    try:
        import tempfile
        import subprocess
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as html_file:
            html_file.write(content.encode("utf-8"))
            html_file_path = html_file.name
        
        pdf_file_path = html_file_path.replace(".html", ".pdf")
        
        # Use pandoc to convert HTML to PDF
        cmd = ["pandoc", html_file_path, "-o", pdf_file_path]
        
        if not include_metadata:
            cmd.append("--standalone")
        
        if not include_images:
            cmd.append("--extract-media=.")
        
        subprocess.run(cmd, check=True)
        
        # Clean up temporary HTML file
        os.remove(html_file_path)
        
        return pdf_file_path
    except ImportError:
        raise FormatConversionError("Pandoc not installed. Install it from https://pandoc.org/installing.html.")
    except Exception as e:
        raise FormatConversionError(f"Error converting HTML to PDF: {str(e)}")


def docx_to_markdown(content: str, include_metadata: bool = True) -> str:
    """
    Convert DOCX to Markdown.
    
    Args:
        content: The path to the DOCX file to convert.
        include_metadata: Whether to include metadata in the output.
        
    Returns:
        The Markdown content.
        
    Raises:
        FormatConversionError: If an error occurs during conversion.
    """
    try:
        import tempfile
        import subprocess
        
        # Create temporary files
        md_file_path = content.replace(".docx", ".md")
        
        # Use pandoc to convert DOCX to Markdown
        cmd = ["pandoc", content, "-o", md_file_path]
        
        if not include_metadata:
            cmd.append("--standalone")
        
        subprocess.run(cmd, check=True)
        
        # Read the generated Markdown file
        with open(md_file_path, "r", encoding="utf-8") as md_file:
            markdown_content = md_file.read()
        
        # Clean up temporary Markdown file
        os.remove(md_file_path)
        
        return markdown_content
    except ImportError:
        raise FormatConversionError("Pandoc not installed. Install it from https://pandoc.org/installing.html.")
    except Exception as e:
        raise FormatConversionError(f"Error converting DOCX to Markdown: {str(e)}")


def docx_to_html(content: str, include_metadata: bool = True, include_images: bool = True) -> str:
    """
    Convert DOCX to HTML.
    
    Args:
        content: The path to the DOCX file to convert.
        include_metadata: Whether to include metadata in the output.
        include_images: Whether to include images in the output.
        
    Returns:
        The HTML content.
        
    Raises:
        FormatConversionError: If an error occurs during conversion.
    """
    try:
        import tempfile
        import subprocess
        
        # Create temporary files
        html_file_path = content.replace(".docx", ".html")
        
        # Use pandoc to convert DOCX to HTML
        cmd = ["pandoc", content, "-o", html_file_path]
        
        if not include_metadata:
            cmd.append("--standalone")
        
        if not include_images:
            cmd.append("--extract-media=.")
        
        subprocess.run(cmd, check=True)
        
        # Read the generated HTML file
        with open(html_file_path, "r", encoding="utf-8") as html_file:
            html_content = html_file.read()
        
        # Clean up temporary HTML file
        os.remove(html_file_path)
        
        return html_content
    except ImportError:
        raise FormatConversionError("Pandoc not installed. Install it from https://pandoc.org/installing.html.")
    except Exception as e:
        raise FormatConversionError(f"Error converting DOCX to HTML: {str(e)}")


def docx_to_pdf(content: str, include_metadata: bool = True, include_images: bool = True) -> str:
    """
    Convert DOCX to PDF.
    
    Args:
        content: The path to the DOCX file to convert.
        include_metadata: Whether to include metadata in the output.
        include_images: Whether to include images in the output.
        
    Returns:
        The path to the generated PDF file.
        
    Raises:
        FormatConversionError: If an error occurs during conversion.
    """
    try:
        import tempfile
        import subprocess
        
        # Create temporary files
        pdf_file_path = content.replace(".docx", ".pdf")
        
        # Use pandoc to convert DOCX to PDF
        cmd = ["pandoc", content, "-o", pdf_file_path]
        
        if not include_metadata:
            cmd.append("--standalone")
        
        if not include_images:
            cmd.append("--extract-media=.")
        
        subprocess.run(cmd, check=True)
        
        return pdf_file_path
    except ImportError:
        raise FormatConversionError("Pandoc not installed. Install it from https://pandoc.org/installing.html.")
    except Exception as e:
        raise FormatConversionError(f"Error converting DOCX to PDF: {str(e)}")


def extract_markdown_metadata(content: str) -> tuple:
    """
    Extract metadata from Markdown content.
    
    Args:
        content: The Markdown content.
        
    Returns:
        A tuple containing the content without metadata and the metadata.
        
    Raises:
        FormatConversionError: If an error occurs during extraction.
    """
    try:
        metadata = {}
        
        # Check if content starts with YAML front matter
        if content.startswith("---"):
            # Find the end of the front matter
            end_index = content.find("---", 3)
            if end_index != -1:
                # Extract the front matter
                front_matter = content[3:end_index].strip()
                
                # Parse the front matter
                for line in front_matter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip()] = value.strip()
                
                # Remove the front matter from the content
                content = content[end_index + 3:].strip()
        
        return content, metadata
    except Exception as e:
        raise FormatConversionError(f"Error extracting Markdown metadata: {str(e)}")


def extract_html_metadata(content: str) -> tuple:
    """
    Extract metadata from HTML content.
    
    Args:
        content: The HTML content.
        
    Returns:
        A tuple containing the content without metadata and the metadata.
        
    Raises:
        FormatConversionError: If an error occurs during extraction.
    """
    try:
        from bs4 import BeautifulSoup
        
        metadata = {}
        
        # Parse the HTML
        soup = BeautifulSoup(content, "html.parser")
        
        # Extract metadata from meta tags
        for meta in soup.find_all("meta"):
            if meta.get("name") and meta.get("content"):
                metadata[meta["name"]] = meta["content"]
        
        # Extract metadata from title tag
        title = soup.find("title")
        if title:
            metadata["title"] = title.string
        
        return str(soup), metadata
    except ImportError:
        raise FormatConversionError("BeautifulSoup package not installed. Install it with 'pip install beautifulsoup4'.")
    except Exception as e:
        raise FormatConversionError(f"Error extracting HTML metadata: {str(e)}")


def add_markdown_metadata(content: str, metadata: Dict[str, Any]) -> str:
    """
    Add metadata to Markdown content.
    
    Args:
        content: The Markdown content.
        metadata: The metadata to add.
        
    Returns:
        The Markdown content with metadata.
        
    Raises:
        FormatConversionError: If an error occurs during addition.
    """
    try:
        # Create YAML front matter
        front_matter = "---\n"
        for key, value in metadata.items():
            front_matter += f"{key}: {value}\n"
        front_matter += "---\n\n"
        
        return front_matter + content
    except Exception as e:
        raise FormatConversionError(f"Error adding Markdown metadata: {str(e)}")


def add_html_metadata(content: str, metadata: Dict[str, Any]) -> str:
    """
    Add metadata to HTML content.
    
    Args:
        content: The HTML content.
        metadata: The metadata to add.
        
    Returns:
        The HTML content with metadata.
        
    Raises:
        FormatConversionError: If an error occurs during addition.
    """
    try:
        from bs4 import BeautifulSoup
        
        # Parse the HTML
        soup = BeautifulSoup(content, "html.parser")
        
        # Create head tag if it doesn't exist
        if not soup.head:
            soup.html.insert(0, soup.new_tag("head"))
        
        # Add metadata as meta tags
        for key, value in metadata.items():
            if key == "title":
                # Add title tag
                title_tag = soup.find("title")
                if title_tag:
                    title_tag.string = value
                else:
                    title_tag = soup.new_tag("title")
                    title_tag.string = value
                    soup.head.append(title_tag)
            else:
                # Add meta tag
                meta_tag = soup.new_tag("meta")
                meta_tag["name"] = key
                meta_tag["content"] = value
                soup.head.append(meta_tag)
        
        return str(soup)
    except ImportError:
        raise FormatConversionError("BeautifulSoup package not installed. Install it with 'pip install beautifulsoup4'.")
    except Exception as e:
        raise FormatConversionError(f"Error adding HTML metadata: {str(e)}")
