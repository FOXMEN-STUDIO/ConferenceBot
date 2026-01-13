import os 
import sys 
from pathlib import Path
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


def build_index(input_data: str, background: bool = False):
    """Build a vectorstore for the given input (local PDF path, URL, or raw text) and cache it.
    If background=True the indexing runs in a background thread and returns immediately.
    """
    import hashlib
    cache_root = Path('.cache/faiss')
    cache_root.mkdir(parents=True, exist_ok=True)

    key = _key_for_source(input_data)
    key_hash = hashlib.sha1((key or '').encode('utf-8')).hexdigest()
    cache_dir = cache_root / key_hash

    if key in _VECTORSTORE_CACHE:
        return f"Already indexed source: {key} (in-memory)"

    if cache_dir.exists():
        try:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vect = FAISS.load_local(str(cache_dir), embeddings)
            _VECTORSTORE_CACHE[key] = vect
            return f"Loaded index from disk for source: {key}"
        except Exception:
            pass

    def _build_and_save():
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
        try:
            vectordb.save_local(str(cache_dir))
        except Exception:
            pass
        _VECTORSTORE_CACHE[key] = vectordb

    if background:
        import threading
        t = threading.Thread(target=_build_and_save, daemon=True)
        t.start()
        return f"Indexing started in background for {key}"

    _build_and_save()
    return f"Indexed {len(texts)} chunks for {key} (saved to disk: {str(cache_dir)})"

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


async def paper_reviewer_rag_stream(input_data, question="Please provide a structured review of the paper."):
    """Async generator that yields progressive review chunks."""
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
    chat_model = ChatGroq(model="llama-3.3-70b-versatile")

    chain   = (
        {
                "context": retriever,
                "question": RunnablePassthrough()
            }
        | prompt
        | chat_model
    )

    try:
        if hasattr(chat_model, 'stream'):
            async for tok in chat_model.stream(question):
                yield tok
            return
    except Exception:
        pass

    result = chain.invoke(question)
    text = result.content if hasattr(result, 'content') else str(result)
    from src.utils.formatter import format_for_bot, chunk_text_for_stream
    text = format_for_bot('reviewer', text)
    import asyncio
    for c in chunk_text_for_stream(text, max_chars=60):
        yield c
        await asyncio.sleep(0.03) 
