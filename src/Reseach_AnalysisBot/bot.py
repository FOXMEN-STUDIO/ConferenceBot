from pathlib import Path
import json
import os
from dotenv import load_dotenv, find_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS  # or Chroma
from .prompt import prompt


def Research_paper_analyst(path):
    _ = load_dotenv(find_dotenv())  # read local .env file
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

    # model define 
    chat_model = ChatGroq(model="llama-3.3-70b-versatile")

    # make vectodatabase
    loader = PyMuPDFLoader(path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = FAISS.from_documents(texts, embeddings)
    # or use chroma

    retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k":3})

    chain   = (
        {
                "context": retriever,
                "question": RunnablePassthrough()
            }
        | prompt
        | chat_model
        
        
    )
    response = chain.invoke("Explain the summary of the paper in detail.")
    print(response.content)