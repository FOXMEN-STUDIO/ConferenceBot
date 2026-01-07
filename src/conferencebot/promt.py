from langchain_core.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_template(
    """You are a helpful assistant that helps people find information about Aziz Ashfak from his personal website.
    "Use the following pieces of context to answer the question at the end. "
    "If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    context:
    {context}
    
    Question: 
    {question}"""
)