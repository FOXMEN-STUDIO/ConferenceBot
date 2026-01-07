from crewai import Crew, Agent, Task
from langchain_groq import ChatGroq
from typing import Optional


class WriterTask(Task):
    # Input field
    text: str
    # Optional LLM instance (injected by caller). If None, a default ChatGroq will be created.
    llm: Optional[ChatGroq] = None

    # Required CrewAI fields
    description: str = "Generate a well-structured academic paragraph from input text"
    expected_output: str = "A polished academic paragraph based on input text"

    def __call__(self):
        prompt = f"""
Write a clear, coherent, and well-structured academic paragraph based on the following text:
{self.text}

Ensure formal, logical flow. Use scholarly tone, proper grammar, and connect ideas naturally. Do NOT use bullet points in output.
"""
        if self.llm is None:
            self.llm = ChatGroq(model="llama-3.3-70b-versatile")
        response = self.llm.invoke(prompt)
        paragraph = response.content if hasattr(response, "content") else response
        return {"paragraph": paragraph}

# 3. PolisherTask: refine paragraph
# -----------------------------
class PolisherTask(Task):
    draft: str
    llm: Optional[ChatGroq] = None

    description: str = "Polish an academic paragraph for tone, grammar, clarity, and flow"
    expected_output: str = "A polished, publication-ready paragraph"

    def __call__(self):
        prompt = f"""
Act as a professional academic editor. Polish the following paragraph for academic clarity, tone, grammar, and readability.
Ensure formal, cohesive, and publication-ready style.

Draft:
{self.draft}
"""
        if self.llm is None:
            self.llm = ChatGroq(model="llama-3.3-70b-versatile")
        response = self.llm.invoke(prompt)
        polished = response.content if hasattr(response, "content") else response
        return {"polished": polished}
