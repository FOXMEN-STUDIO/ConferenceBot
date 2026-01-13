
from langchain_core.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_template(
    """
Act as an expert academic reviewer. Analyze the provided research paper and provide a structured review using ONLY Markdown with the following top-level headings (in this exact order):

## Title Assessment
Brief comment on clarity, relevance, and accuracy of the paper’s title.

## Abstract Evaluation
Assess the abstract for conciseness and whether it reflects the main content.

## Strengths
Provide a concise bulleted list (3–6 items) with the paper's key strengths.

## Weaknesses
Provide a concise bulleted list (3–6 items) with the main weaknesses and suggested improvements.

## Detailed Comments
Give section-by-section feedback (Introduction, Methods, Results, Discussion) with short paragraphs or bullets.

## Overall Recommendation
State one of: Accept / Minor revision / Major revision / Reject and justify in 1–2 sentences.

Constraints:
- Return only Markdown with the headings above and no extraneous text or apology lines.
- Keep each bullet concise (1–2 sentences), be professional and specific.

Context:
{context}

Question:
{question}
"""

)