import yaml, os, sys
import streamlit as st
from pathlib import Path
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

st.set_page_config(
    page_title="Vivace Tools",
    page_icon="🦙",
    layout="wide",
)

def get_new_posts():
    profile = Profile()
    st.sidebar.button('Get New Posts', on_click=profile.main())

@st.cache_data
def load_posts():
    st.table(posts_df)

def run():
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days'],
            config['preauthorized']
        )

        name, authentication_status, username = authenticator.login(fields={'Login':'Login', 'Form name':'Login'})
        if authentication_status:
            if username == 'gr8monk3ys':
                main(authenticator, name)
        elif authentication_status == False:
            st.error('Username/password is incorrect')
        elif authentication_status == None:
            st.warning('Please enter your username and password')

def main(authenticator, name):
    with st.sidebar:
        st.write(f'Welcome *{name}*')
        # get_new_posts()
        authenticator.logout('Logout', 'main')
    
    st.write("# Welcome to TAlker! 👋")

    st.markdown(
        """
        The TA Bot is a cutting-edge tool designed to enhance teaching assistant interactions and streamline the management of coursework queries. Leveraging the powerful capabilities of the Piazza Python API, LangChain, FAISS, and Ollama2, this bot transforms the way educators and students engage on platforms like Piazza.

        **👈 Select a feature from the sidebar** to discover the diverse functionalities of the TA Bot, from automatic question answering to personalized feedback provision.

        ### Want to dive deeper?
        - Explore the TA Bot's integration with Piazza at [Piazza's API documentation](https://piazza.com)
        - Delve into the mechanics of LangChain and how it powers conversational AI at [LangChain documentation](https://langchain.com)
        - Understand the role of FAISS in efficient similarity search through [FAISS GitHub repository](https://github.com/facebookresearch/faiss)
        - Learn about the advancements in LLM technology with Ollama2 at [Ollama2 GitHub repository](https://github.com/OpenAI/ollama)

        ### Discover advanced implementations
        - See how the TA Bot leverages Ollama2 for nuanced language understanding and response generation
        - Explore the bot's use of the Piazza API to seamlessly fetch and categorize academic queries
        - Witness the efficiency of FAISS in clustering and retrieving relevant educational content

        The TA Bot embodies the synergy of AI and education, providing an intuitive interface for educators to enhance their teaching methods and for students to access information promptly and accurately.

        ### Want to learn more?
        - Check out [streamlit.io](https://streamlit.io)
        - Jump into our [documentation](https://docs.streamlit.io)
        - Ask a question in our [community
          forums](https://discuss.streamlit.io)
        ### See more complex demos
        - Use a neural net to [analyze the Udacity Self-driving Car Image
          Dataset](https://github.com/streamlit/demo-self-driving)
        - Explore a [New York City rideshare dataset](https://github.com/streamlit/demo-uber-nyc-pickups)
    """
    )

if __name__ == "__main__":
    run()

