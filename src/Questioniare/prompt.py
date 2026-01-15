PROMPT_TEMPLATE = """
TASK:
Design a high-quality questionnaire for academic research.

STUDY CONTEXT:
- Research variables: {variables}
- Target population: {population}
- Country / culture: {culture}
- Language: {language}
- Measurement scale: {scale}-point Likert scale
- Research domain: {domain}

INSTRUCTIONS:
1. Generate clear, single-concept Likert-scale items.
2. Avoid leading, biased, or double-barreled questions.
3. Ensure cultural appropriateness.
4. Include approximately 30% reverse-coded items marked as [REVERSE].
5. Items must be suitable for reliability analysis (Cronbach’s alpha).

OUTPUT FORMAT (STRICT):
Variable-wise items with Likert scale labels.
"""