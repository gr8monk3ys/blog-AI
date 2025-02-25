"""
Blog post generation functionality.
"""
import os
import json
from typing import List, Dict, Any, Optional

from ..text_generation.core import generate_text, LLMProvider, GenerationOptions, create_provider_from_env
from ..types.content import BlogPost, Section, SubTopic, ContentType
from ..types.providers import ProviderType
from ..research.web_researcher import conduct_web_research
from ..planning.content_outline import generate_content_outline, generate_content_outline_with_research
from ..blog_sections.introduction_generator import generate_introduction
from ..blog_sections.conclusion_generator import generate_conclusion
from ..blog_sections.faq_generator import generate_faqs
from ..seo.meta_description import generate_meta_description
from ..post_processing.proofreader import proofread_content
from ..post_processing.humanizer import humanize_content


class BlogGenerationError(Exception):
    """Exception raised for errors in the blog generation process."""
    pass


def generate_blog_post(
    title: str,
    keywords: Optional[List[str]] = None,
    num_sections: int = 5,
    include_faqs: bool = True,
    tone: str = "informative",
    provider_type: ProviderType = "openai",
    options: Optional[GenerationOptions] = None
) -> BlogPost:
    """
    Generate a blog post.
    
    Args:
        title: The title of the blog post.
        keywords: The keywords to include in the blog post.
        num_sections: The number of sections to include in the blog post.
        include_faqs: Whether to include FAQs in the blog post.
        tone: The tone of the blog post.
        provider_type: The type of provider to use.
        options: Options for text generation.
        
    Returns:
        The generated blog post.
        
    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # Create provider
        provider = create_provider_from_env(provider_type)
        
        # Generate outline
        outline = generate_content_outline(title, keywords, num_sections, provider, options)
        
        # Generate sections
        sections = []
        
        # Generate introduction
        introduction_section = generate_introduction_section(title, outline.sections, keywords, tone, provider, options)
        sections.append(introduction_section)
        
        # Generate main sections
        for i, section_title in enumerate(outline.sections[1:-1]):  # Skip introduction and conclusion
            section = generate_section(section_title, keywords, tone, provider, options)
            sections.append(section)
        
        # Generate conclusion
        conclusion_section = generate_conclusion_section(title, outline.sections, keywords, tone, provider, options)
        sections.append(conclusion_section)
        
        # Generate FAQs if requested
        if include_faqs:
            # Combine all section content for context
            content = ""
            for section in sections:
                content += section.title + "\n"
                for subtopic in section.subtopics:
                    if subtopic.content:
                        content += subtopic.content + "\n"
            
            # Generate FAQs
            faq_section = generate_faq_section(title, content, keywords, tone, provider, options)
            sections.append(faq_section)
        
        # Generate meta description
        description = generate_meta_description(title, keywords or [], provider=provider, options=options).content
        
        return BlogPost(
            title=title,
            description=description,
            sections=sections,
            tags=keywords or []
        )
    except Exception as e:
        raise BlogGenerationError(f"Error generating blog post: {str(e)}")


def generate_blog_post_with_research(
    title: str,
    keywords: Optional[List[str]] = None,
    num_sections: int = 5,
    include_faqs: bool = True,
    tone: str = "informative",
    provider_type: ProviderType = "openai",
    options: Optional[GenerationOptions] = None
) -> BlogPost:
    """
    Generate a blog post with research.
    
    Args:
        title: The title of the blog post.
        keywords: The keywords to include in the blog post.
        num_sections: The number of sections to include in the blog post.
        include_faqs: Whether to include FAQs in the blog post.
        tone: The tone of the blog post.
        provider_type: The type of provider to use.
        options: Options for text generation.
        
    Returns:
        The generated blog post.
        
    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # Create provider
        provider = create_provider_from_env(provider_type)
        
        # Conduct research
        research_keywords = [title]
        if keywords:
            research_keywords.extend(keywords)
        
        research_results = conduct_web_research(research_keywords)
        
        # Generate outline
        outline = generate_content_outline_with_research(title, keywords, num_sections, provider, options)
        
        # Generate sections
        sections = []
        
        # Generate introduction
        introduction_section = generate_introduction_section_with_research(
            title, outline.sections, research_results, keywords, tone, provider, options
        )
        sections.append(introduction_section)
        
        # Generate main sections
        for i, section_title in enumerate(outline.sections[1:-1]):  # Skip introduction and conclusion
            section = generate_section_with_research(
                section_title, research_results, keywords, tone, provider, options
            )
            sections.append(section)
        
        # Generate conclusion
        conclusion_section = generate_conclusion_section(title, outline.sections, keywords, tone, provider, options)
        sections.append(conclusion_section)
        
        # Generate FAQs if requested
        if include_faqs:
            # Combine all section content for context
            content = ""
            for section in sections:
                content += section.title + "\n"
                for subtopic in section.subtopics:
                    if subtopic.content:
                        content += subtopic.content + "\n"
            
            # Generate FAQs
            faq_section = generate_faq_section(title, content, keywords, tone, provider, options)
            sections.append(faq_section)
        
        # Generate meta description
        description = generate_meta_description(title, keywords or [], provider=provider, options=options).content
        
        return BlogPost(
            title=title,
            description=description,
            sections=sections,
            tags=keywords or []
        )
    except Exception as e:
        raise BlogGenerationError(f"Error generating blog post with research: {str(e)}")


def generate_introduction_section(
    title: str,
    outline_sections: List[str],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> Section:
    """
    Generate an introduction section.
    
    Args:
        title: The title of the blog post.
        outline_sections: The sections in the outline.
        keywords: The keywords to include in the introduction.
        tone: The tone of the introduction.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated introduction section.
        
    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # Generate introduction
        introduction = generate_introduction(
            title=title,
            outline="\n".join(outline_sections),
            keywords=keywords,
            tone=tone,
            provider=provider,
            options=options
        )
        
        # Create subtopic
        subtopic = SubTopic(
            title="",
            content=introduction.content
        )
        
        # Create section
        section = Section(
            title="Introduction",
            subtopics=[subtopic]
        )
        
        return section
    except Exception as e:
        raise BlogGenerationError(f"Error generating introduction section: {str(e)}")


def generate_introduction_section_with_research(
    title: str,
    outline_sections: List[str],
    research_results: Any,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> Section:
    """
    Generate an introduction section with research.
    
    Args:
        title: The title of the blog post.
        outline_sections: The sections in the outline.
        research_results: The research results.
        keywords: The keywords to include in the introduction.
        tone: The tone of the introduction.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated introduction section.
        
    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # Create prompt for introduction generation
        prompt = f"""
        Generate an engaging introduction for a blog post with the following details:
        
        Title: {title}
        """
        
        if keywords:
            prompt += f"\nKeywords: {', '.join(keywords)}"
        
        prompt += f"""
        Outline:
        {", ".join(outline_sections)}
        
        Based on the following research:
        
        {str(research_results)[:2000]}...
        
        Requirements:
        - The introduction should be 3-4 paragraphs.
        - Include a compelling hook in the first paragraph to grab the reader's attention.
        - Clearly state the purpose or thesis of the blog post.
        - Include at least one of the main keywords naturally.
        - Incorporate insights from the research.
        - Set the tone and expectations for the rest of the blog post.
        - Use a {tone} tone throughout.
        
        Return only the introduction, nothing else.
        """
        
        # Generate introduction
        introduction_text = generate_text(prompt, provider, options)
        
        # Clean up the introduction
        introduction_text = introduction_text.strip()
        
        # Create subtopic
        subtopic = SubTopic(
            title="",
            content=introduction_text
        )
        
        # Create section
        section = Section(
            title="Introduction",
            subtopics=[subtopic]
        )
        
        return section
    except Exception as e:
        raise BlogGenerationError(f"Error generating introduction section with research: {str(e)}")


def generate_section(
    section_title: str,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> Section:
    """
    Generate a section.
    
    Args:
        section_title: The title of the section.
        keywords: The keywords to include in the section.
        tone: The tone of the section.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated section.
        
    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # Create prompt for section generation
        prompt = f"""
        Generate content for a blog post section with the following title:
        
        {section_title}
        """
        
        if keywords:
            prompt += f"\n\nKeywords to include: {', '.join(keywords)}"
        
        prompt += f"""
        
        Requirements:
        - The content should be 3-4 paragraphs.
        - Include relevant information, examples, and insights.
        - Use a {tone} tone throughout.
        - Write in a clear, engaging style.
        """
        
        if keywords:
            prompt += """
            - Incorporate the keywords naturally throughout the content.
            """
        
        prompt += """
        Return only the section content, nothing else.
        """
        
        # Generate section content
        section_content = generate_text(prompt, provider, options)
        
        # Clean up the section content
        section_content = section_content.strip()
        
        # Create subtopic
        subtopic = SubTopic(
            title="",
            content=section_content
        )
        
        # Create section
        section = Section(
            title=section_title,
            subtopics=[subtopic]
        )
        
        return section
    except Exception as e:
        raise BlogGenerationError(f"Error generating section: {str(e)}")


def generate_section_with_research(
    section_title: str,
    research_results: Any,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> Section:
    """
    Generate a section with research.
    
    Args:
        section_title: The title of the section.
        research_results: The research results.
        keywords: The keywords to include in the section.
        tone: The tone of the section.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated section.
        
    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # Create prompt for section generation
        prompt = f"""
        Generate content for a blog post section with the following title:
        
        {section_title}
        
        Based on the following research:
        
        {str(research_results)[:2000]}...
        """
        
        if keywords:
            prompt += f"\n\nKeywords to include: {', '.join(keywords)}"
        
        prompt += f"""
        
        Requirements:
        - The content should be 3-4 paragraphs.
        - Include relevant information, examples, and insights from the research.
        - Use a {tone} tone throughout.
        - Write in a clear, engaging style.
        """
        
        if keywords:
            prompt += """
            - Incorporate the keywords naturally throughout the content.
            """
        
        prompt += """
        Return only the section content, nothing else.
        """
        
        # Generate section content
        section_content = generate_text(prompt, provider, options)
        
        # Clean up the section content
        section_content = section_content.strip()
        
        # Create subtopic
        subtopic = SubTopic(
            title="",
            content=section_content
        )
        
        # Create section
        section = Section(
            title=section_title,
            subtopics=[subtopic]
        )
        
        return section
    except Exception as e:
        raise BlogGenerationError(f"Error generating section with research: {str(e)}")


def generate_conclusion_section(
    title: str,
    outline_sections: List[str],
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> Section:
    """
    Generate a conclusion section.
    
    Args:
        title: The title of the blog post.
        outline_sections: The sections in the outline.
        keywords: The keywords to include in the conclusion.
        tone: The tone of the conclusion.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated conclusion section.
        
    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # Create content from outline sections
        content = f"Title: {title}\n\nSections:\n"
        for section in outline_sections:
            content += f"- {section}\n"
        
        # Generate conclusion
        conclusion = generate_conclusion(
            title=title,
            content=content,
            keywords=keywords,
            tone=tone,
            provider=provider,
            options=options
        )
        
        # Create subtopic
        subtopic = SubTopic(
            title="",
            content=conclusion.content
        )
        
        # Create section
        section = Section(
            title="Conclusion",
            subtopics=[subtopic]
        )
        
        return section
    except Exception as e:
        raise BlogGenerationError(f"Error generating conclusion section: {str(e)}")


def generate_faq_section(
    title: str,
    content: str,
    keywords: Optional[List[str]] = None,
    tone: str = "informative",
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> Section:
    """
    Generate a FAQ section.
    
    Args:
        title: The title of the blog post.
        content: The content of the blog post.
        keywords: The keywords to include in the FAQs.
        tone: The tone of the FAQs.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated FAQ section.
        
    Raises:
        BlogGenerationError: If an error occurs during generation.
    """
    try:
        # Generate FAQs
        faq_result = generate_faqs(
            content=content,
            count=5,
            provider=provider,
            options=options
        )
        
        # Create subtopics
        subtopics = []
        
        for faq in faq_result.faqs:
            subtopic = SubTopic(
                title=faq.question,
                content=faq.answer
            )
            
            subtopics.append(subtopic)
        
        # Create section
        section = Section(
            title="Frequently Asked Questions",
            subtopics=subtopics
        )
        
        return section
    except Exception as e:
        raise BlogGenerationError(f"Error generating FAQ section: {str(e)}")


def post_process_blog_post(
    blog_post: BlogPost,
    proofread: bool = True,
    humanize: bool = True,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> BlogPost:
    """
    Post-process a blog post.
    
    Args:
        blog_post: The blog post to post-process.
        proofread: Whether to proofread the blog post.
        humanize: Whether to humanize the blog post.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The post-processed blog post.
        
    Raises:
        BlogGenerationError: If an error occurs during post-processing.
    """
    try:
        # Create a copy of the blog post
        processed_blog_post = BlogPost(
            title=blog_post.title,
            description=blog_post.description,
            sections=[],
            tags=blog_post.tags,
            date=blog_post.date,
            image=blog_post.image
        )
        
        # Process each section
        for section in blog_post.sections:
            processed_section = Section(
                title=section.title,
                subtopics=[]
            )
            
            for subtopic in section.subtopics:
                processed_subtopic = SubTopic(
                    title=subtopic.title,
                    content=subtopic.content
                )
                
                if subtopic.content:
                    # Proofread content if requested
                    if proofread:
                        proofreading_result = proofread_content(subtopic.content, provider=provider, options=options)
                        if proofreading_result.corrected_text:
                            processed_subtopic.content = proofreading_result.corrected_text
                    
                    # Humanize content if requested
                    if humanize:
                        processed_subtopic.content = humanize_content(processed_subtopic.content, provider=provider, options=options)
                
                processed_section.subtopics.append(processed_subtopic)
            
            processed_blog_post.sections.append(processed_section)
        
        return processed_blog_post
    except Exception as e:
        raise BlogGenerationError(f"Error post-processing blog post: {str(e)}")


def save_blog_post_to_markdown(
    blog_post: BlogPost,
    file_path: str
) -> None:
    """
    Save a blog post to a Markdown file.
    
    Args:
        blog_post: The blog post to save.
        file_path: The path to save the blog post to.
        
    Raises:
        BlogGenerationError: If an error occurs during saving.
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Create Markdown content
        markdown = f"# {blog_post.title}\n\n"
        
        # Add metadata
        markdown += "---\n"
        markdown += f"title: {blog_post.title}\n"
        markdown += f"description: {blog_post.description}\n"
        markdown += f"date: {blog_post.date}\n"
        markdown += f"image: {blog_post.image}\n"
        markdown += f"tags: {', '.join(blog_post.tags)}\n"
        markdown += "---\n\n"
        
        # Add sections
        for section in blog_post.sections:
            markdown += f"## {section.title}\n\n"
            
            for subtopic in section.subtopics:
                if subtopic.title:
                    markdown += f"### {subtopic.title}\n\n"
                
                if subtopic.content:
                    markdown += f"{subtopic.content}\n\n"
        
        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown)
    except Exception as e:
        raise BlogGenerationError(f"Error saving blog post to Markdown: {str(e)}")


def save_blog_post_to_json(
    blog_post: BlogPost,
    file_path: str
) -> None:
    """
    Save a blog post to a JSON file.
    
    Args:
        blog_post: The blog post to save.
        file_path: The path to save the blog post to.
        
    Raises:
        BlogGenerationError: If an error occurs during saving.
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Convert blog post to JSON-serializable format
        blog_post_data = {
            "title": blog_post.title,
            "description": blog_post.description,
            "date": blog_post.date,
            "image": blog_post.image,
            "tags": blog_post.tags,
            "sections": []
        }
        
        for section in blog_post.sections:
            section_data = {
                "title": section.title,
                "subtopics": []
            }
            
            for subtopic in section.subtopics:
                subtopic_data = {
                    "title": subtopic.title,
                    "content": subtopic.content
                }
                
                section_data["subtopics"].append(subtopic_data)
            
            blog_post_data["sections"].append(section_data)
        
        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(blog_post_data, f, indent=2)
    except Exception as e:
        raise BlogGenerationError(f"Error saving blog post to JSON: {str(e)}")


def load_blog_post_from_json(
    file_path: str
) -> BlogPost:
    """
    Load a blog post from a JSON file.
    
    Args:
        file_path: The path to load the blog post from.
        
    Returns:
        The loaded blog post.
        
    Raises:
        BlogGenerationError: If an error occurs during loading.
    """
    try:
        # Read from file
        with open(file_path, "r", encoding="utf-8") as f:
            blog_post_data = json.load(f)
        
        # Convert JSON data to BlogPost
        sections = []
        
        for section_data in blog_post_data["sections"]:
            subtopics = []
            
            for subtopic_data in section_data["subtopics"]:
                subtopic = SubTopic(
                    title=subtopic_data["title"],
                    content=subtopic_data["content"]
                )
                
                subtopics.append(subtopic)
            
            section = Section(
                title=section_data["title"],
                subtopics=subtopics
            )
            
            sections.append(section)
        
        blog_post = BlogPost(
            title=blog_post_data["title"],
            description=blog_post_data["description"],
            sections=sections,
            tags=blog_post_data["tags"],
            date=blog_post_data["date"],
            image=blog_post_data["image"]
        )
        
        return blog_post
    except Exception as e:
        raise BlogGenerationError(f"Error loading blog post from JSON: {str(e)}")
