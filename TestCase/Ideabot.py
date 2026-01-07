from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.idea_Bot.bot import idea_generation_Bot

field= "ML/AI"
topic= "Advancements in Federated Learning for Healthcare Applications"
novelty = "High",
target_venue= "NeurIPS"

style= "empirical"
idea_generation_Bot(field,topic,novelty,target_venue,style)