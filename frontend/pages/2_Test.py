import streamlit as st
from llm import *
import os

st.set_page_config(
    page_title="TAlker Test",
    page_icon="🦙",
    layout="wide",
)

llm_instance = Llm_chain()

# @st.cache_resource
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
    st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

with st.sidebar:
    # st.write(f'Welcome *{name}*')
    if 'OPENAI_API_KEY' in st.secrets:
        st.success('API key already provided!', icon='✅')
        openai_api = st.secrets['OPENAI_API_KEY']
    else:
        openai_api = st.text_input('Enter OpenAI API token:', type='password')
        if not (openai_api.startswith('sk-') and len(openai_api)==40):
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to entering your prompt message!', icon='👉')
    os.environ['OPENAI_API_KEY'] = openai_api
    clear_chat_history()

st.title("Test")

if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "TA", "content": "How may I assist you today?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input(disabled=not openai_api):
    st.session_state.messages.append({"role": "user", "content": ""})
    with st.chat_message("user"):
        st.write(prompt)

    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "TA":
        with st.chat_message("Teacher assistant"):
            with st.spinner("Thinking..."):
                response = llm_instance.generate_response(str(prompt), 'DSCI 560')
                placeholder = st.empty()
                full_response = ''
                for item in response:
                    full_response += item
                    placeholder.markdown(full_response)
                placeholder.markdown(full_response)
                message = {"role": "Teacher assistant", "content": full_response}
        st.session_state.messages.append(message)