import os 
import sys 
from dotenv import find_dotenv,load_dotenv
from langchain_groq import  ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS,Chroma
from langchain_core.runnables import RunnablePassthrough
from .prompt import prompt

# Module-level cache
_VECTORSTORE_CACHE = {}


def _key_for_source(source: str):
    if not source:
        return "__default__"
    return source


def build_index(input_data: str):
    """Build a vectorstore for the given input (local PDF path, URL, or raw text) and cache it."""
    key = _key_for_source(input_data)
    if key in _VECTORSTORE_CACHE:
        return f"Already indexed source: {key}"

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    if isinstance(input_data, str) and (input_data.strip().lower().endswith('.pdf') or input_data.strip().lower().startswith('http')):
        loader = PyMuPDFLoader(input_data)
        documents = loader.load()
        texts = [d.page_content for d in documents]
    else:
        raw_text = input_data or ""
        texts = text_splitter.split_text(raw_text)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = FAISS.from_texts(texts, embeddings)
    _VECTORSTORE_CACHE[key] = vectordb
    return f"Indexed {len(texts)} chunks for {key}"


def paper_reviewer_rag(input_data, question="Please provide a structured review of the paper."):
    """Accepts either a PDF path/URL or raw text content as `input_data`.
    Uses cached vectorstore if available; otherwise builds and runs the review chain.
    """
    _ = load_dotenv(find_dotenv())  # read local .env file
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

    # model define 
    chat_model = ChatGroq(model="llama-3.3-70b-versatile")

    key = _key_for_source(input_data)
    if key in _VECTORSTORE_CACHE:
        vectordb = _VECTORSTORE_CACHE[key]
    else:
        # Build on the fly
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        if isinstance(input_data, str) and (input_data.strip().lower().endswith('.pdf') or input_data.strip().lower().startswith('http')):
            loader = PyMuPDFLoader(input_data)
            documents = loader.load()
            texts = [d.page_content for d in documents]
        else:
            raw_text = input_data or ""
            texts = text_splitter.split_text(raw_text)

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectordb = FAISS.from_texts(texts, embeddings)

    retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k":3})

    chain   = (
        {
                "context": retriever,
                "question": RunnablePassthrough()
            }
        | prompt
        | chat_model
    )

    # Invoke the chain with the provided question and return the text
    response = chain.invoke(question)
    return response.content if hasattr(response, 'content') else str(response) 
