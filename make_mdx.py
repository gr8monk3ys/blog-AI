import os
import json
import time
import openai
import datetime
import feedparser
from dotenv import find_dotenv, load_dotenv
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.utilities import WikipediaAPIWrapper
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain, SequentialChain

load_dotenv(find_dotenv())
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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


def create_title(rss_item):
    title_template = PromptTemplate(
        input_variables=["title", "url"], 
        template="""You are a blog writer and your job is to turn the following news article into an unique SEO optimized blog post.

Here is the title of the article: {title}

Here's the URL please read it here:
{url}

Based on the information given above, please generate an SEO Optimized Article Title.

Parameters:

Max 10 words & 1 sentence flow

DO NOT put quotes around the title.
        """
    )

    llm = OpenAI(model="gpt-4", temperature=0.9)
    title_memory = ConversationBufferMemory(
        input_key="title", memory_key="chat_history"
    )
    title_chain = LLMChain(
        llm=llm,
        prompt=title_template,
        verbose=True,
        output_key="title",
        memory=title_memory,
    )
    title = title_chain.run(title=rss_item["title"], url=rss_item["link"])
    print(f"Title: {title}\n")
    return title.strip()

def create_description(title):
    description_template = PromptTemplate(
        input_variables=["title"], 
        template="You are a professional blogger. In one to two sentences write a description with optimal SEO in mind about {title} "
    )

    llm = OpenAI(model="gpt-4o", temperature=0.9)
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
    description = description_chain.run(title=title)
    print(f"Description: {description}\n")
    return description.strip()

def create_index(title):
    print("Initializing creation of index...")
    index_prompt = f""" You are a professional blogger. Write me a blog outline on a blog called '{title}' with 7 sections. Each section has 4 subtopics, output as a 
    json code. Please make sure to not say anything else except output the code. Assuming multiple sections, it should look exactly 
    like the following in terms of structure: 
        {{\"Title\": \"\",\"Sections\": [{{\"Section 1\": \"\",\"Subtopics\": [\"\", \"\", \"\", \"\"]}},{{\"Section 2\": 
        \"\",\"Subtopics\": [\"\", \"\", \"\", \"\"]}},{{\"Section 3\": \"\",\"Subtopics\": [\"\", \"\", \"\", \"\"]}}]}}"""

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=index_prompt,
        temperature=0.9,
        max_tokens=1500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
        stop=[" Human:", " AI:"],
    )

    response_dict = response.choices[0].to_dict()
    print(json.dumps(response_dict, indent=4))
    return response_dict


def create_section(index):
    json_string = index["text"]
    data = json.loads(json_string)
    sections = data["Sections"]
    title = data["Title"]

    blog_post = ""
    for section in sections:
        section_num, section_name = list(section.items())[0]
        subtopics = section["Subtopics"]

        blog_post += f"## {section_name}\n\n"
        for subtopic in subtopics:
            llm = OpenAI(model="gpt-4o", temperature=0.9)
            subtopic_template = PromptTemplate(
                input_variables=["blog", "section", "subtopic"],
                template=""" The following is a blog called '{blog}' that has a section named '{section}' about 350 words each, 
                the sub-section that needs to be focused on in the section is called '{subtopic}' and must be written with optimal SEO in mind. 
                I don't want transition words such as finally, conclusion, or overall. I don't want spaces between
                paragraphs and the beginning of all paragraphs must be indented:""",
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
            subtopic_text = subtopic_chain.run(blog=title, section=section_name, subtopic=subtopic)
            time.sleep(2)

            blog_post += f"{subtopic_text}\n"
    return blog_post

def create_body(rss_url, title):
    body_prompt = f"""
    Generate an article on this topic: {rss_url}

    Here is the title of the article:
    {title}

    You're a blog writer and you are turning the article given above into a unique SEO-optimized blog post. The title is already written so please start with the body of the article.

    Formatting: Use H1, H2, and H3 headers. Use HTML: You choose what to bold and bullet point. Make sure if you want to bold anything to put in <b></b> tags and <li></li> tags for bullet points.

    Parameters: This blog post should be approx. 2000 words long.
    """

    llm = OpenAI(model="gpt-4o", temperature=0.9)
    body_template = PromptTemplate(
        input_variables=["rss_url", "title"],
        template=body_prompt,
    )

    body_memory = ConversationBufferMemory(
        input_key="rss_url", memory_key="chat_history"
    )
    body_chain = LLMChain(
        llm=llm,
        prompt=body_template,
        verbose=True,
        output_key="body",
        memory=body_memory,
    )
    body_text = body_chain.run(rss_url=rss_url, title=title)
    time.sleep(2)

    return body_text


if __name__ == "__main__":

    # prompt = input("Enter the topic here: ")
    # url = input("Please input the URL that you would like to turn into a blog post")
    url = 'https://rss.app/feeds/uqWWFSTUYneBNbrq.xml'


    # if prompt:
    if url:
        max_items = 1

        rss_items = import_rss_feed(url, max_items)
        title = create_title(rss_items[0])
        description = create_description(title)
        index = create_index(title)
        # blog_post = create_section(index)
        blog_post = create_body(url, title)

        title = title.replace('"', '')
        file_title = title.replace(' ', '-')

        today = datetime.date.today()
        formatted_date = today.strftime('%Y-%m-%d')

        with open(directory + f"{file_title}.mdx", "w") as f:
            f.write(
                f"""import {{ ArticleLayout }} from '@/components/ArticleLayout'
                import Image from 'next/future/image'

export const meta = {{
author: 'Lorenzo Scaturchio',
date: '{formatted_date}',
title: '{title}',
description: '{description}',
}}

export default (props) => <ArticleLayout meta={{meta}} {{...props}} />\n\n""")
            f.write(blog_post)