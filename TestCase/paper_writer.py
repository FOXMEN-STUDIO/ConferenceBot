from pathlib import Path
import sys
# Ensure repository root (where `src/` lives) is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.paper_writerBot.agent import paper_writer

input_text = """
Climate change is a pressing global issue. It leads to rising temperatures, melting ice caps, extreme weather events,
and has a significant impact on biodiversity. Human activities such as deforestation and carbon emissions are major contributors.
"""
paper_writer(input_text)