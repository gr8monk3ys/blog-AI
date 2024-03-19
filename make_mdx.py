import os
import json
import time
import openai
import datetime
from dotenv import find_dotenv, load_dotenv
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.utilities import WikipediaAPIWrapper
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain, SequentialChain

load_dotenv(find_dotenv())
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def create_title(prompt):
    title_template = PromptTemplate(
        input_variables=["topic"], 
        template="""You are a professional bloggger. Write me a maximum 11 word blog title with optimal SEO in mind about {topic}
        """
    )

    llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0.9)
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
    title = title_chain.run(prompt)
    print(f"Title: {title}\n")
    return title.strip()

def create_description(title):
    title_template = PromptTemplate(
        input_variables=["title"], template="You are a professional bloggger. In one to two sentences write a description with optimal SEO in mind about {title} "
    )

    llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0.9)
    title_memory = ConversationBufferMemory(
        input_key="title", memory_key="chat_history"
    )
    title_chain = LLMChain(
        llm=llm,
        prompt=title_template,
        verbose=True,
        output_key="description",
        memory=title_memory,
    )
    description = title_chain.run(title)
    print(f"Description: {description}\n")
    return description.strip()

def create_index(title):
    print("Initializing creation of index...")
    index_prompt = f""" You are a professional bloggger. Write me a blog outline on a blog called '{title}' with 7 sections. Each section has 4 subtopics, output as a 
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
    # Removed the slicing of the string
    data = json.loads(json_string)
    sections = data["Sections"]
    title = data["Title"]

    blog_post = ""
    for section in sections:
        section_num, section_name = list(section.items())[0]
        subtopics = section["Subtopics"]

        blog_post += f"## {section_name}\n\n"
        for subtopic in subtopics:
            llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0.9)
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

if __name__ == "__main__":

    prompt = input("Enter the topic here: ")
    # for topic in favorites:
    #     prompt = topic

    if prompt:
        # Removed the quote function as it's not defined in the code
        title = create_title(prompt)
        description = create_description(title)
        index = create_index(title)
        blog_post = create_section(index)

        title = title.replace('"', '')
        file_title = title.replace(' ', '-')

        # Get today's date
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

