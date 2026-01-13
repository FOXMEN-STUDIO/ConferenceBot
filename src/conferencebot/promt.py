from langchain_core.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_template(
    """You are a helpful assistant that returns concise, professional answers about the provided conference/profile context.

Use the following pieces of context to answer the question at the end. If you don't know the answer, say you don't know.

Requirements:
- Return the answer in Markdown.
- Start with a short one-sentence summary line.
- When appropriate, include a small bulleted list of key details (dates, location, main topics, important links).

Context:
{context}

Question:
{question}
"""
)