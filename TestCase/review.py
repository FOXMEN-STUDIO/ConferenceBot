from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.paperReviewerBot.bot import paper_reviewer_rag

# Resolve PDF path relative to this script so it works from any CWD
pdf_path = Path(__file__).resolve().parents[1] / "Human_Segmentation.pdf"
if not pdf_path.exists():
    raise FileNotFoundError(
        f"PDF not found at {pdf_path!s}. Place 'Human_Segmentation.pdf' at the repository root or pass a valid path."
    )

chain = paper_reviewer_rag(str(pdf_path))
response = chain.invoke('what are the strengths and weaknesses of the paper?')
print(response.content)