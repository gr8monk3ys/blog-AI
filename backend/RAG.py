#from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import os
from dotenv import load_dotenv

class Llm_chain:
    def __init__(self):
        self._data_path = '../data/pdf_slides.txt'  
        self.conversation_chain = None
        self._setup_chain()
        
    def _get_doc_text(self):
        with open(self._data_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return text

    def _get_text_chunks(self, text):
        chunk_size = 500
        splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=chunk_size,
            chunk_overlap=100,
            length_function=len
        )
        chunks = splitter.split_text(text)
        return chunks

    def _get_vectorstore(self, chunks):
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_texts(chunks, embeddings)
        return vectorstore

    def _get_conversation_chain(self, vectorstore):
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        conversation_chain = ConversationalRetrievalChain.from_llm(ChatOpenAI(temperature=0, model='gpt-3.5-turbo'), vectorstore.as_retriever(), memory=memory)
        return conversation_chain

    def _setup_chain(self):
        load_dotenv()
        text = self._get_doc_text()
        chunks = self._get_text_chunks(text)
        embeddings = self._get_vectorstore(chunks)
        self.conversation_chain = self._get_conversation_chain(embeddings)

    def generate_answer(self, user_input):
        if self.conversation_chain is None:
            raise ValueError("Conversation chain is not set. Call set_pdf_path() first.")
        response = self.conversation_chain({'question': user_input})
        return response['answer']


if __name__ == '__main__':
    llm_chain = Llm_chain()
    user_input = input('You:')
    try:
        answer = llm_chain.generate_answer(user_input)
        print('Bot:', answer)
        print('\n')
    except ValueError as e:
        print("Error:", e)
        
