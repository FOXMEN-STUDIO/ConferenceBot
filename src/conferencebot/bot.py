import sys
import os 
from dotenv import load_dotenv,find_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader,WebBaseLoader,UnstructuredURLLoader
from langchain_core.runnables import RunnablePassthrough
from .promt import prompt

# Convert Documents → string
def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

def conference_bot(question):
    _ = load_dotenv(find_dotenv())  # read local .env file
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

    # loading data 
    loader = UnstructuredURLLoader(urls=["https://aziz-ashfak.github.io/profile/"])
    data = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(data)

    texts = [doc.page_content for doc in docs]
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_texts(texts, embeddings)
    retrive = vectorstore.as_retriever()
    # Convert Documents → string

    # # Chain
    chain = (
        {
            "context": retrive | format_docs,
            "question": RunnablePassthrough() 
        }
        | prompt
        | llm
    )
    print(chain.invoke(question).content)
