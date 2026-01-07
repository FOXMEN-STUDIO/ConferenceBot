import os 
import sys
from dotenv import load_dotenv,find_dotenv
from langchain_groq import ChatGroq
from .task import WriterTask,PolisherTask

def paper_writer(input_text):
    _ = load_dotenv(find_dotenv())  # read local .env file
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

    llm = ChatGroq(model="llama-3.3-70b-versatile")


    # Instantiate tasks by passing field names and inject the LLM instance
    writer_task = WriterTask(text=input_text, llm=llm)
    writer_result = writer_task()
    draft_paragraph = writer_result["paragraph"]

    polisher_task = PolisherTask(draft=draft_paragraph, llm=llm)
    polisher_result = polisher_task()
    polished_paragraph = polisher_result["polished"]


    # 5. Display Results
    # -----------------------------
    print("Generated Paragraph:\n", draft_paragraph)
    print("\nPolished Paragraph:\n", polished_paragraph)

