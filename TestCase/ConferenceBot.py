from pathlib import Path
import sys
# Ensure repository root (where `src/` lives) is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.conferencebot.bot import conference_bot

conference_bot("Who is Aziz Ashfak?")

