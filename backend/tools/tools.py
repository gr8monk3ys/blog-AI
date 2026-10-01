import os
import json
import feedparser
from openai import OpenAI
from langchain.tools import tool
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI()

class BlogTools:
    @tool("Import RSS feed")
    def import_rss_feed(self, url, max_items=5):
        """Import RSS feed and return the latest items"""
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
    
    @tool("Create Title")
    def create_title(rss_item, role):
        """Create a title"""

        res = client.chat.completions.create(
            model='gpt-4o-mini',
            # response_format={"type": "json_object"},
            messages=[
                {"role": "user", "title":
                """
                You are a {role} and your job is to turn the following news article into an unique SEO optimized blog post
                Here is the title of the example news article: {title}

                Here's the URL please read it here:
                {url}

                Based on the information given above, please generate an SEO Optimized Article Title.

                Parameters:
                Max 10 words & 1 sentence flow
                DO NOT put quotes around the title. """.format(role=role, title=rss_item["title"], url=rss_item["URL"])}
            ]
        )
        print("Title: " + res.choices[0].message.content)
        return res.choices[0].message.content
    
    @tool("Create Description")
    def create_description(title):
        """Create an description"""
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

    @tool("Create Index")
    def create_index(title):
        """Create an index"""
        model = ChatOpenAI()
        class BlogIndex(BaseModel):
            title: str = Field(description="The title of the blog")
            sections: List[Dict[str, Any]] = Field(description="The sections of the blog with their subtopics")

        query = """You are a professional blogger. Write me a blog outline on a blog called '{title}' with 5-6 sections. Each section has 2 subtopics, output as a 
            JSON code. Please make sure to not say anything else except output the code.
            """.format(title=title)
        
        parser = JsonOutputParser(pydantic_object=BlogIndex)

        prompt = PromptTemplate(
            template="Answer the query.\n{format_instructions}\n{query}\n",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt | model | parser
        res = chain.invoke({"query": query})
        print(json.dumps(res, indent=2))
        return res

    @tool("Create Body")
    def create_body(rss_url, title):
        """Create the body"""
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
        return blog_post