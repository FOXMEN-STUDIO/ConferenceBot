from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.Reseach_AnalysisBot.bot import Research_paper_analyst

# Resolve PDF path relative to this script so it works from any CWD
pdf_path = Path(__file__).resolve().parents[1] / "Human_Segmentation.pdf"
if not pdf_path.exists():
    raise FileNotFoundError(
        f"PDF not found at {pdf_path!s}. Place 'Human_Segmentation.pdf' at the repository root or pass a valid path."
    )

Research_paper_analyst(str(pdf_path))