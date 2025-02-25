"""
File saving functionality.
"""
import os
from typing import Optional, Dict, Any

from ..types.post_processing import SaveOptions, OutputFormat


class FileSavingError(Exception):
    """Exception raised for errors in the file saving process."""
    pass


def save_to_file(
    content: str,
    options: SaveOptions
) -> str:
    """
    Save content to a file.
    
    Args:
        content: The content to save.
        options: Options for saving.
        
    Returns:
        The path to the saved file.
        
    Raises:
        FileSavingError: If an error occurs during saving.
    """
    try:
        file_path = options.file_path
        
        # Check if file exists and overwrite is not allowed
        if os.path.exists(file_path) and not options.overwrite:
            raise FileSavingError(f"File {file_path} already exists and overwrite is not allowed")
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Save content to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return file_path
    except Exception as e:
        raise FileSavingError(f"Error saving to file: {str(e)}")


def save_blog_post(
    content: str,
    title: str,
    output_dir: str = "content/blog",
    format: OutputFormat = "markdown",
    overwrite: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a blog post to a file.
    
    Args:
        content: The blog post content.
        title: The title of the blog post.
        output_dir: The directory to save the blog post in.
        format: The format to save the blog post in.
        overwrite: Whether to overwrite existing files.
        metadata: Metadata to include in the blog post.
        
    Returns:
        The path to the saved file.
        
    Raises:
        FileSavingError: If an error occurs during saving.
    """
    try:
        # Create a safe filename from the title
        safe_title = title.lower().replace(" ", "-").replace(":", "").replace("'", "").replace('"', "")
        
        # Determine file extension based on format
        if format == "markdown":
            file_extension = ".md"
        elif format == "html":
            file_extension = ".html"
        elif format == "docx":
            file_extension = ".docx"
        elif format == "pdf":
            file_extension = ".pdf"
        else:
            file_extension = ".txt"
        
        # Create file path
        file_path = os.path.join(output_dir, safe_title + file_extension)
        
        # Add metadata if needed
        if metadata and format == "markdown":
            content = add_markdown_metadata(content, metadata)
        elif metadata and format == "html":
            content = add_html_metadata(content, metadata)
        
        # Save content to file
        save_options = SaveOptions(file_path=file_path, format=format, overwrite=overwrite)
        return save_to_file(content, save_options)
    except Exception as e:
        raise FileSavingError(f"Error saving blog post: {str(e)}")


def save_book(
    content: str,
    title: str,
    output_dir: str = "content/books",
    format: OutputFormat = "docx",
    overwrite: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a book to a file.
    
    Args:
        content: The book content.
        title: The title of the book.
        output_dir: The directory to save the book in.
        format: The format to save the book in.
        overwrite: Whether to overwrite existing files.
        metadata: Metadata to include in the book.
        
    Returns:
        The path to the saved file.
        
    Raises:
        FileSavingError: If an error occurs during saving.
    """
    try:
        # Create a safe filename from the title
        safe_title = title.lower().replace(" ", "-").replace(":", "").replace("'", "").replace('"', "")
        
        # Determine file extension based on format
        if format == "markdown":
            file_extension = ".md"
        elif format == "html":
            file_extension = ".html"
        elif format == "docx":
            file_extension = ".docx"
        elif format == "pdf":
            file_extension = ".pdf"
        else:
            file_extension = ".txt"
        
        # Create file path
        file_path = os.path.join(output_dir, safe_title + file_extension)
        
        # Add metadata if needed
        if metadata and format == "markdown":
            content = add_markdown_metadata(content, metadata)
        elif metadata and format == "html":
            content = add_html_metadata(content, metadata)
        
        # Save content to file
        save_options = SaveOptions(file_path=file_path, format=format, overwrite=overwrite)
        return save_to_file(content, save_options)
    except Exception as e:
        raise FileSavingError(f"Error saving book: {str(e)}")


def add_markdown_metadata(content: str, metadata: Dict[str, Any]) -> str:
    """
    Add metadata to Markdown content.
    
    Args:
        content: The Markdown content.
        metadata: The metadata to add.
        
    Returns:
        The Markdown content with metadata.
        
    Raises:
        FileSavingError: If an error occurs during addition.
    """
    try:
        # Create YAML front matter
        front_matter = "---\n"
        for key, value in metadata.items():
            if isinstance(value, list):
                front_matter += f"{key}:\n"
                for item in value:
                    front_matter += f"  - {item}\n"
            else:
                front_matter += f"{key}: {value}\n"
        front_matter += "---\n\n"
        
        return front_matter + content
    except Exception as e:
        raise FileSavingError(f"Error adding Markdown metadata: {str(e)}")


def add_html_metadata(content: str, metadata: Dict[str, Any]) -> str:
    """
    Add metadata to HTML content.
    
    Args:
        content: The HTML content.
        metadata: The metadata to add.
        
    Returns:
        The HTML content with metadata.
        
    Raises:
        FileSavingError: If an error occurs during addition.
    """
    try:
        # Check if content has a head tag
        head_start = content.find("<head>")
        head_end = content.find("</head>")
        
        if head_start != -1 and head_end != -1:
            # Add metadata to existing head tag
            head_content = content[head_start + 6:head_end]
            
            # Add meta tags
            meta_tags = ""
            for key, value in metadata.items():
                if key == "title":
                    # Check if title tag exists
                    title_start = head_content.find("<title>")
                    title_end = head_content.find("</title>")
                    
                    if title_start != -1 and title_end != -1:
                        # Replace existing title
                        head_content = head_content[:title_start + 7] + value + head_content[title_end:]
                    else:
                        # Add title tag
                        meta_tags += f"<title>{value}</title>\n"
                else:
                    # Add meta tag
                    meta_tags += f'<meta name="{key}" content="{value}">\n'
            
            # Insert meta tags at the beginning of the head tag
            new_head_content = meta_tags + head_content
            
            # Replace head content
            content = content[:head_start + 6] + new_head_content + content[head_end:]
        else:
            # Create head tag with metadata
            head_tag = "<head>\n"
            
            # Add title tag if present
            if "title" in metadata:
                head_tag += f"<title>{metadata['title']}</title>\n"
            
            # Add meta tags
            for key, value in metadata.items():
                if key != "title":
                    head_tag += f'<meta name="{key}" content="{value}">\n'
            
            head_tag += "</head>\n"
            
            # Check if content has an html tag
            html_start = content.find("<html>")
            
            if html_start != -1:
                # Insert head tag after html tag
                content = content[:html_start + 6] + head_tag + content[html_start + 6:]
            else:
                # Add html and head tags
                content = f"<html>\n{head_tag}{content}\n</html>"
        
        return content
    except Exception as e:
        raise FileSavingError(f"Error adding HTML metadata: {str(e)}")


def create_directory_if_not_exists(directory: str) -> None:
    """
    Create a directory if it doesn't exist.
    
    Args:
        directory: The directory to create.
        
    Raises:
        FileSavingError: If an error occurs during creation.
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except Exception as e:
        raise FileSavingError(f"Error creating directory: {str(e)}")


def get_safe_filename(title: str) -> str:
    """
    Get a safe filename from a title.
    
    Args:
        title: The title to convert to a filename.
        
    Returns:
        A safe filename.
        
    Raises:
        FileSavingError: If an error occurs during conversion.
    """
    try:
        # Replace spaces with hyphens
        filename = title.lower().replace(" ", "-")
        
        # Remove special characters
        filename = "".join(c for c in filename if c.isalnum() or c == "-")
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename
    except Exception as e:
        raise FileSavingError(f"Error getting safe filename: {str(e)}")
