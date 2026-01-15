import os 
import sys 
from dotenv import load_dotenv,find_dotenv
from langchain_groq import ChatGroq
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma,FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from .prompt import PROMPT_TEMPLATE


def generate_questionnaire(example_input: dict) -> str:
    """Generate questionnaire using the PROMPT_TEMPLATE and return text result."""
    _ = load_dotenv(find_dotenv())  # read local .env file
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.0)

    # Build prompt properly using from_template
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    # Build chain mapping prompt variables to passthroughs
    chain = (
        {
            "variables": RunnablePassthrough(),
            "population": RunnablePassthrough(),
            "culture": RunnablePassthrough(),
            "language": RunnablePassthrough(),
            "scale": RunnablePassthrough(),
            "domain": RunnablePassthrough()
        }
        | prompt
        | llm
    )

    try:
        response = chain.invoke(example_input)
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        return f"Invocation error: {e}"
