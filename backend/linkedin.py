from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAI

def create_linkedin_post(rss_item):
    linkedin_template = PromptTemplate(
        input_variables=["title", "description", "url"], 
        template="""You are a social media manager. Create a LinkedIn post for the following news article.

Title: {title}
Description: {description}
URL: {url}

The post should be engaging, professional, and optimized for LinkedIn. It should include relevant hashtags and a call to action.
        """
    )

    llm = OpenAI(model="gpt-4o")
    linkedin_memory = ConversationBufferMemory(
        input_key="title", memory_key="chat_history"
    )
    linkedin_chain = LLMChain(
        llm=llm,
        prompt=linkedin_template,
        memory=linkedin_memory,
    )
    linkedin_post = linkedin_chain.run({
        "title": rss_item["title"], 
        "description": rss_item["description"], 
        "url": rss_item["link"]
    })
    print(f"LinkedIn Post: {linkedin_post}\n")
    return linkedin_post.strip()
