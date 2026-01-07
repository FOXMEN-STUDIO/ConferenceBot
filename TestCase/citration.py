from pathlib import Path
import sys
# Ensure repository root (where `src/` lives) is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.citrationmaker.citration import convert_bibtex_to_style

bib = """
@article{ref2020,
  title={Deep Learning for AI},
  author={John Doe and Jane Smith},
  journal={Journal of AI Research},
  volume={12},
  number={3},
  pages={45--60},
  year={2020}
}
"""

style = "MLA"
result = convert_bibtex_to_style(bib, style)
print(result)