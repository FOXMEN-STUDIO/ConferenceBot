from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sys
import io
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Research Tools Dashboard")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

BOTS = [
    {"id": "citation",   "name": "Citation Formatter"},
    {"id": "idea",       "name": "Idea Generator"},
    {"id": "conference", "name": "Conference Profile Bot"},
    {"id": "reviewer",   "name": "Paper Reviewer"},
    {"id": "analyst",    "name": "Paper Analyst"},
    {"id": "writer",     "name": "Paper Writer Agent"},
]

# Very simple function router (expand later with real logic)
def run_bot_logic(bot_id: str, **kwargs) -> tuple[str | None, str | None]:
    """
    Replace this with real calls to your bot functions
    Return (result, error) or (None, error)
    """
    try:
        if bot_id == "citation":
            from src.citrationmaker.citration import convert_bibtex_to_style
            bibtex = kwargs.get("bibtex", "")
            style = kwargs.get("style", "APA").upper()
            return convert_bibtex_to_style(bibtex.strip(), style), None

        elif bot_id == "idea":
            from src.idea_Bot.bot import idea_generation_Bot
            return idea_generation_Bot(
                field=kwargs.get("field", "Computer Science"),
                topic=kwargs.get("topic", "Sample topic"),
                novelty=kwargs.get("novelty", "Medium"),
                target_venue=kwargs.get("target_venue", "Any venue"),
                style=kwargs.get("style", "Formal")
            ), None

        elif bot_id == "conference":
            from src.conferencebot.bot import conference_bot
            question = kwargs.get("question", "")
            # temporary print capture - you should refactor to return!
            old_stdout = sys.stdout
            buf = io.StringIO()
            sys.stdout = buf
            conference_bot(question.strip())
            output = buf.getvalue().strip() or "(no output captured)"
            sys.stdout = old_stdout
            return output, None

        # Placeholder for remaining bots - replace when ready
        return None, f"{bot_id} is not fully implemented yet"

    except Exception as e:
        return None, str(e)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "bots": BOTS
    })


@app.get("/bot/{bot_id}", response_class=HTMLResponse)
async def bot_page(request: Request, bot_id: str):
    bot = next((b for b in BOTS if b["id"] == bot_id), None)
    if not bot:
        return "<h1>404 - Bot not found</h1>", 404

    return templates.TemplateResponse("bot.html", {
        "request": request,
        "bot": bot,
        "result": None,
        "error": None,
        "last_values": {}
    })


@app.post("/bot/{bot_id}", response_class=HTMLResponse)
async def execute_bot(
    request: Request,
    bot_id: str,
    bibtex: str = Form(None),
    style: str = Form("APA"),
    question: str = Form(None),
    field: str = Form(None),
    topic: str = Form(None),
    novelty: str = Form(None),
    target_venue: str = Form(None),
    style_text: str = Form(None),
):
    bot = next((b for b in BOTS if b["id"] == bot_id), None)
    if not bot:
        return "<h1>404</h1>", 404

    result, error = run_bot_logic(
        bot_id,
        bibtex=bibtex,
        style=style,
        question=question,
        field=field,
        topic=topic,
        novelty=novelty,
        target_venue=target_venue,
       # style=style_text
    )

    last_values = {
        "bibtex": bibtex,
        "style": style,
        "question": question,
        "field": field,
        "topic": topic,
        "novelty": novelty,
        "target_venue": target_venue,
        "style_text": style_text
    }

    return templates.TemplateResponse("bot.html", {
        "request": request,
        "bot": bot,
        "result": result,
        "error": error,
        "last_values": last_values
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)