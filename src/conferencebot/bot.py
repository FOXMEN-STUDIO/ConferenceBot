import sys
import os 
from dotenv import load_dotenv,find_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader,WebBaseLoader,UnstructuredURLLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.runnables import RunnablePassthrough
from .promt import prompt

# Module-level cache for vectorstores keyed by source
_VECTORSTORE_CACHE = {}

# Convert Documents → string
def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])


def _key_for_source(source: str):
    if not source:
        return "__default_profile__"
    return source


def build_index(source: str = None):
    """Build and cache a vectorstore for the given source (URL, local PDF path, or raw text)."""
    key = _key_for_source(source)
    if key in _VECTORSTORE_CACHE:
        return f"Already indexed source: {key}"

    if source and source.strip().lower().endswith('.pdf'):
        loader = PyMuPDFLoader(source)
        documents = loader.load()
        texts = [d.page_content for d in documents]
    elif source and source.strip().lower().startswith('http'):
        loader = UnstructuredURLLoader(urls=[source])
        data = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        docs = text_splitter.split_documents(data)
        texts = [doc.page_content for doc in docs]
    else:
        # treat source as raw text or use default profile
        raw = source or "https://aziz-ashfak.github.io/profile/"
        if raw.startswith('http'):
            loader = UnstructuredURLLoader(urls=[raw])
            data = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
            docs = text_splitter.split_documents(data)
            texts = [doc.page_content for doc in docs]
        else:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
            texts = text_splitter.split_text(raw)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_texts(texts, embeddings)
    _VECTORSTORE_CACHE[key] = vectorstore
    return f"Indexed {len(texts)} chunks for source: {key}"


def conference_bot(question, source: str = None):
    _ = load_dotenv(find_dotenv())  # read local .env file
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.9)

    key = _key_for_source(source)
    if key not in _VECTORSTORE_CACHE:
        # build index for default or given source
        build_index(source)

    vectorstore = _VECTORSTORE_CACHE[key]
    retrive = vectorstore.as_retriever()

    # # Chain
    chain = (
        {
            "context": retrive | format_docs,
            "question": RunnablePassthrough() 
        }
        | prompt
        | llm
    )
    # Return the resulting content so callers can display it
    return chain.invoke(question).content


async def conference_bot_stream(question, source: str = None):
    """Async generator that yields partial outputs for the conference bot.
    It will yield sentence chunks with small delays to simulate streaming if the LLM does not support streaming directly.
    """
    # Build or reuse index
    key = _key_for_source(source)
    if key not in _VECTORSTORE_CACHE:
        build_index(source)

    vectorstore = _VECTORSTORE_CACHE[key]
    retrive = vectorstore.as_retriever()

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.9)
    chain = (
        {
            "context": retrive | format_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
    )

    # Try to call streaming-capable API if available, else fall back to full invoke and chunk
    try:
        # If the llm supports a streaming 'stream' or 'invoke_stream' method, use it
        if hasattr(llm, 'stream'):
            async for token in llm.stream(question):
                yield token
            return
        if hasattr(llm, 'invoke_stream'):
            async for chunk in llm.invoke_stream(question):
                yield chunk
            return
    except Exception:
        # ignore and fallback
        pass

    # Fallback: full generation then chunk
    result = chain.invoke(question)
    text = result.content if hasattr(result, 'content') else str(result)

    from src.utils.formatter import format_for_bot, chunk_text_for_stream
    text = format_for_bot('conference', text)
    import asyncio
    for chunk in chunk_text_for_stream(text, max_chars=60):
        yield chunk
        await asyncio.sleep(0.03)

