import os 
import sys
from dotenv import load_dotenv,find_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from .prompt import prompt
def idea_generation_Bot(field,topic,novelty,target_venue,style):
    _ = load_dotenv(find_dotenv())
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.9)
    # Build chain using existing 'prompt' (defined in an earlier cell)
    chain = (
        {
            "field": RunnablePassthrough(),
            "topic": RunnablePassthrough(),
            "explicit_keywords": RunnablePassthrough(),
            "novelty": RunnablePassthrough(),
            "target_venue": RunnablePassthrough(),
            "constraints": RunnablePassthrough(),
            "style": RunnablePassthrough()
        }
        | prompt
        | llm
    )

    # Example usage
    user_input = {
        "field": field,
        "topic": topic,
        "novelty": novelty,
        "target_venue": target_venue,
        
        "style": style
    }

    # Generate research idea
    response = chain.invoke(user_input)
    # Return output string for the UI to display
    return response.content
