import os
import json
import time
import datetime
import argparse
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain

load_dotenv()

class SubTopic(BaseModel):
    title: str
    content: Optional[str] = None

class Section(BaseModel):
    title: str
    subtopics: List[SubTopic]

class BlogPost(BaseModel):
    title: str
    description: str
    date: str = Field(default_factory=lambda: datetime.datetime.now().strftime("%Y-%m-%d"))
    image: str = "/images/blog/default.jpg"
    tags: List[str] = ["AI", "technology"]
    sections: List[Section]

def create_mdx_header(blog_post: BlogPost) -> str:
    header = f'''import {{ BlogLayout }} from "@/components/BlogLayout";

export const meta = {{
  date: "{blog_post.date}",
  title: "{blog_post.title}",
  description:
    "{blog_post.description}",
  image:
    "{blog_post.image}",
  tags: {json.dumps(blog_post.tags)},
}};

export default (props) => <BlogLayout meta={{meta}} {{...props}} />;

'''
    return header

def create_title(topic: str) -> str:
    llm = ChatOpenAI(model="gpt-4", temperature=0.9)
    title_template = PromptTemplate(
        input_variables=["topic"],
        template="""You are a blog writer and your job is to create an SEO optimized title for a blog post about the following topic: {topic}

Please generate an SEO Optimized Article Title.

Parameters:
Max 10 words & 1 sentence flow
DO NOT put quotes around the title."""
    )
    
    title_chain = LLMChain(
        llm=llm,
        prompt=title_template,
        verbose=True,
    )
    
    title = title_chain.run(topic=topic)
    return title.strip()

def create_description(title: str) -> str:
    llm = ChatOpenAI(model="gpt-4", temperature=0.9)
    desc_template = PromptTemplate(
        input_variables=["title"],
        template="""You are a professional blogger. In one to two sentences write a description with optimal SEO in mind about "{title}" """
    )
    
    desc_chain = LLMChain(
        llm=llm,
        prompt=desc_template,
        verbose=True,
    )
    
    description = desc_chain.run(title=title)
    return description.strip()

def create_section_content(section: Section) -> None:
    llm = ChatOpenAI(model="gpt-4", temperature=0.9)
    for subtopic in section.subtopics:
        subtopic_template = PromptTemplate(
            input_variables=["section", "subtopic"],
            template="""Write a detailed, informative paragraph about '{subtopic}' as part of the section '{section}' in a blog post. 
            The content should be engaging, informative, and SEO-optimized. 
            Keep paragraphs concise and avoid unnecessary transitions or redundant text.
            Focus on providing value to the reader."""
        )
        
        subtopic_memory = ConversationBufferMemory(
            input_key="section", memory_key="chat_history"
        )
        subtopic_chain = LLMChain(
            llm=llm,
            prompt=subtopic_template,
            verbose=True,
            output_key="subtopic",
            memory=subtopic_memory,
        )
        subtopic.content = subtopic_chain.run(section=section.title, subtopic=subtopic.title)
        time.sleep(2)

def create_blog_structure(topic: str) -> BlogPost:
    llm = ChatOpenAI(model="gpt-4", temperature=0.9)
    structure_template = PromptTemplate(
        input_variables=["topic"],
        template="""Create a blog post structure about {topic}. The blog should have 3 main sections, each with 2-3 subtopics.
        Return the structure as a JSON object with the following format:
        {{
            "sections": [
                {{
                    "title": "section title",
                    "subtopics": [
                        "subtopic 1",
                        "subtopic 2"
                    ]
                }}
            ]
        }}
        Make sure the sections and subtopics flow logically and cover the topic comprehensively."""
    )
    
    structure_chain = LLMChain(
        llm=llm,
        prompt=structure_template,
        verbose=True,
    )
    
    structure_json = json.loads(structure_chain.run(topic=topic))
    
    # Convert JSON to Pydantic models
    sections = []
    for section in structure_json["sections"]:
        subtopics = [SubTopic(title=st) for st in section["subtopics"]]
        sections.append(Section(title=section["title"], subtopics=subtopics))
    
    title = create_title(topic)
    description = create_description(title)
    
    # Remove any quotes from title and description
    title = title.strip('"').strip("'")
    description = description.strip('"').strip("'")
    
    return BlogPost(
        title=title,
        description=description,
        sections=sections
    )

def create_blog_content(blog_post: BlogPost) -> str:
    # Generate content for each section
    for section in blog_post.sections:
        create_section_content(section)
    
    # Create the MDX content
    content = create_mdx_header(blog_post)
    
    for section in blog_post.sections:
        content += f"\n## {section.title}\n\n"
        for subtopic in section.subtopics:
            if subtopic.content:
                content += f"{subtopic.content.strip()}\n\n"
    
    return content

def main():
    parser = argparse.ArgumentParser(description='Generate a blog post about a specific topic')
    parser.add_argument('topic', type=str, help='The topic to write about')
    args = parser.parse_args()
    
    # Create blog structure
    blog_post = create_blog_structure(args.topic)
    
    # Generate content
    content = create_blog_content(blog_post)
    
    # Create safe filename from title
    safe_title = blog_post.title.lower().replace(" ", "-").replace(":", "").replace("'", "")
    filename = f"content/blog/{safe_title}.mdx"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Write content to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Blog post generated successfully at {filename}")

if __name__ == "__main__":
    main()