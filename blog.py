import os
import json
import time
import datetime
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from langchain_openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain, SequentialChain
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from tools import blog_tools

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Ensure the API key is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

# Initialize the OpenAI client with the API key
# openai.api_key = OPENAI_API_KEY
client = OpenAI(api_key=OPENAI_API_KEY)

def import_rss_feed(url, max_items=1):
    feed = feedparser.parse(url)
    entries = feed.entries[:max_items]
    rss_items = []

    for entry in entries:
        item = {
            "title": entry.title,
            "link": entry.link,
            "description": entry.description,
            "published": entry.published
        }
        rss_items.append(item)

    return rss_items

def create_title(prompt):
    title_template = PromptTemplate(
        input_variables=["topic"], 
        template="""You are a professional blogger. Write me a maximum 11 word blog title with optimal SEO in mind about {topic}, Also, this is for a .mdx file."""
    )

    llm = OpenAI(model_name="gpt-3.5-turbo-instruct")
    title_memory = ConversationBufferMemory(
        input_key="topic", memory_key="chat_history"
    )
    title_chain = LLMChain(
        llm=llm,
        prompt=title_template,
        verbose=True,
        output_key="title",
        memory=title_memory,
    )
    title = title_chain.invoke({"topic": prompt})
    print("Title:", title, "\n")
    return title["title"].strip()

def create_description(title):
    description_template = PromptTemplate(
        input_variables=["title"], 
        template="You are a professional blogger. In one to two sentences write a description with optimal SEO in mind about {title}."
    )

    llm = OpenAI(model_name="gpt-3.5-turbo-instruct", temperature=0.9)
    description_memory = ConversationBufferMemory(
        input_key="title", memory_key="chat_history"
    )
    description_chain = LLMChain(
        llm=llm,
        prompt=description_template,
        verbose=True,
        output_key="description",
        memory=description_memory,
    )
    description = description_chain.invoke({"title": title})
    print("Description:", description, "\n")
    return description["description"].strip()

def create_index(title):
    print("Initializing creation of index...")
    model = ChatOpenAI()
    class BlogIndex(BaseModel):
        title: str = Field(description="The title of the blog")
        sections: List[Dict[str, Any]] = Field(description="The sections of the blog with their subtopics")

    query = """You are a professional blogger. Write me a blog outline on a blog called '{title}' with 5-6 sections. Each section has 2 subtopics, output as a 
        JSON code. Please make sure to not say anything else except output the code.
        """.format(title=title)
    
    parser = JsonOutputParser(pydantic_object=BlogIndex)

    prompt = PromptTemplate(
        template="Answer the queyry.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | model | parser
    res = chain.invoke({"query": query})
    print(json.dumps(res, indent=2))
    return res

def create_section(index):
    # Directly use the index dictionary
    data = index
    sections = data["sections"]
    title = data["title"]

    blog_post = ""
    from openai import OpenAI
    client = OpenAI()

    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a SEO optimized blog writer that writes 3000 - 4000 word blog posts."},
        {"role": "user", "content": 
        """
        Here is the title of the article: '{blog}' that has a structure like '{index}',
        You're a blog write and  you are turning the article given above into a unique seo-optimized blog post. The title is already written so please start with the body of the article.

        Formatting: Use H1, H2, and H3 headers Use HTML: You choose what yto bold and bullet point. Make sure if ou want to bold anything to put in <b></b> tags and <li></li> tags for bullet points.

        Parameters: This blog post and it should be approx. 3000 words long and each subsection should be 500 words long.

        I don't want transition words such as finally, conclusion, or overall. I don't want spaces between as well the format should be in markdown but
        only provide the text needed.""".format(blog=title,index=index)}
    ]
    )

    print(completion.choices[0].message)
    body = completion.choices[0].message.content
    blog_post += f"{body}\n"

    # for section in sections:
    #     section_title = list(section.items())[0]
    #     subtopics = list(section['subtopics'])

    #     blog_post += f"## {section_title}\n\n"

    #     for subtopic in subtopics:
    #         llm = OpenAI(model_name="gpt-3.5-turbo-instruct")
    #         subtopic_template = PromptTemplate(
    #             input_variables=["blog", "section", "subtopic"],
    #             template="""The following is a blog called '{blog}' that has a section named '{section}', 
    #             the sub-section that needs to be focused on in the section is called '{subtopic}' and must be written with optimal SEO in mind. 
    #             I don't want transition words such as finally, conclusion, or overall. I don't want spaces between as well as this is for a .mdx file.""",
    #         )

    #         subtopic_memory = ConversationBufferMemory(
    #             input_key="section", memory_key="chat_history"
    #         )
    #         subtopic_chain = LLMChain(
    #             llm=llm,
    #             prompt=subtopic_template,
    #             verbose=True,
    #             output_key="subtopic",
    #             memory=subtopic_memory,
    #         )
    #         subtopic_text = subtopic_chain.invoke({"blog": title, "section": section_title, "subtopic": subtopic})
    #         time.sleep(2)

    #         blog_post += f"{subtopic_text['subtopic']}\n"
    return blog_post

if __name__ == "__main__":

    prompt = input("Enter the topic here: ")
    if prompt:
        # Removed the quote function as it's not defined in the code
        title = create_title(prompt)
        description = create_description(title)
        index = create_index(title)
        blog_post = create_section(index)

        title = title.replace('"', '')
        file_title = title.replace(' ', '-')

        description = description.replace('"', '')

        # Get today's date
        today = datetime.date.today()
        formatted_date = today.strftime('%Y-%m-%d')
        directory = "data/test/"

        with open(directory + f"content.mdx", "w") as f:
            f.write(
                f"""
import {{ BlogLayout }} from "@/components/BlogLayout";

import {{ CodeWindow }} from "@/components/CodeWindow";

export const meta = {{
date: '{formatted_date}',
title: '{title}',
description: '{description}',
image: 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2370&q=80',
tags: ["tailwindcss", "css", "frontend"],
}};

export default (props) => <BlogLayout meta={{meta}} {{...props}} />;

""")
            f.write(blog_post)
