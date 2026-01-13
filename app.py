from fastapi import FastAPI, Request, Form, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sys
import io
import tempfile
from pathlib import Path
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
            source = kwargs.get("paper_text") or kwargs.get("pdf_path") or None
            # Prefer bots to return strings instead of printing; handle None safely
            output = conference_bot(question.strip(), source=source)
            if output is None:
                output = "(no output returned)"
            return output, None

        elif bot_id == "writer":
            from src.paper_writerBot.agent import paper_writer
            text = kwargs.get("input_text", "").strip()
            return paper_writer(text), None

        elif bot_id == "reviewer":
            from src.paperReviewerBot.bot import paper_reviewer_rag
            doc = kwargs.get("paper_text") or kwargs.get("pdf_path") or ""
            question = kwargs.get("question") or "Please provide a structured review of the paper."
            return paper_reviewer_rag(doc, question), None

        elif bot_id == "analyst":
            from src.Reseach_AnalysisBot.bot import Research_paper_analyst
            doc = kwargs.get("paper_text") or kwargs.get("pdf_path") or ""
            return Research_paper_analyst(doc), None

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
    paper_text: str = Form(None),
    pdf_path: str = Form(None),
    input_text: str = Form(None),
):
    bot = next((b for b in BOTS if b["id"] == bot_id), None)
    if not bot:
        return "<h1>404</h1>", 404

    # Read raw form to capture uploaded file if present (file input uses multipart forms)
    form = await request.form()
    uploaded = form.get('pdf_file')
    if uploaded is not None and getattr(uploaded, 'filename', ''):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        content = await uploaded.read()
        tmp.write(content)
        tmp.flush()
        tmp.close()
        pdf_path = tmp.name

    # Fall back to explicit params if form values aren't present
    paper_text = form.get('paper_text') or paper_text
    pdf_path = form.get('pdf_path') or pdf_path
    question = form.get('question') or question

    last_values = {
        "bibtex": bibtex,
        "style": style,
        "question": question,
        "field": field,
        "topic": topic,
        "novelty": novelty,
        "target_venue": target_venue,
        "style_text": style_text,
        "paper_text": paper_text,
        "pdf_path": pdf_path,
        "input_text": input_text,
    }

    # If PDF / document provided but no question, build an index and return readiness
    if bot_id in ("reviewer", "analyst", "conference") and (paper_text or pdf_path) and not question:
        try:
            if bot_id == "reviewer":
                from src.paperReviewerBot.bot import build_index as reviewer_build
                msg = reviewer_build(paper_text or pdf_path)
            elif bot_id == "analyst":
                from src.Reseach_AnalysisBot.bot import build_index as analyst_build
                msg = analyst_build(paper_text or pdf_path)
            else:
                from src.conferencebot.bot import build_index as conf_build
                msg = conf_build(paper_text or pdf_path)

            return templates.TemplateResponse("bot.html", {
                "request": request,
                "bot": bot,
                "result": msg,
                "error": None,
                "last_values": last_values
            })
        except Exception as e:
            pass

    result, error = run_bot_logic(
        bot_id,
        bibtex=bibtex,
        style=style,
        question=question,
        field=field,
        topic=topic,
        novelty=novelty,
        target_venue=target_venue,
        paper_text=paper_text,
        pdf_path=pdf_path,
        input_text=input_text
       # style=style_text
    )

    return templates.TemplateResponse("bot.html", {
        "request": request,
        "bot": bot,
        "result": result,
        "error": error,
        "last_values": last_values
    })


@app.post("/bot/{bot_id}/stream")
async def stream_bot(request: Request, bot_id: str):
    """Stream bot output by returning chunked text. This is a simple server-side chunked stream
    (if LLM streaming is available, integrate here).
    """
    form = await request.form()
    # extract form fields commonly used by different bots
    bibtex = form.get('bibtex')
    style = form.get('style')
    question = form.get('question')
    field = form.get('field')
    topic = form.get('topic')
    novelty = form.get('novelty')
    target_venue = form.get('target_venue')
    paper_text = form.get('paper_text')
    pdf_path = form.get('pdf_path')
    input_text = form.get('input_text')

    # Handle uploaded file if provided
    uploaded = form.get('pdf_file')
    if uploaded is not None and getattr(uploaded, 'filename', ''):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        content = await uploaded.read()
        tmp.write(content)
        tmp.flush()
        tmp.close()
        pdf_path = tmp.name

    # If PDF/doc provided but no question - build an index and stream a readiness message
    if bot_id in ("reviewer", "analyst", "conference") and (paper_text or pdf_path) and not question:
        try:
            if bot_id == "reviewer":
                from src.paperReviewerBot.bot import build_index as reviewer_build
                msg = reviewer_build(paper_text or pdf_path)
            elif bot_id == "analyst":
                from src.Reseach_AnalysisBot.bot import build_index as analyst_build
                msg = analyst_build(paper_text or pdf_path)
            else:
                from src.conferencebot.bot import build_index as conf_build
                msg = conf_build(paper_text or pdf_path)

            async def idx_gen():
                yield msg
            return StreamingResponse(idx_gen(), media_type='text/plain; charset=utf-8')
        except Exception as e:
            pass

    result, error = run_bot_logic(
        bot_id,
        bibtex=bibtex,
        style=style,
        question=question,
        field=field,
        topic=topic,
        novelty=novelty,
        target_venue=target_venue,
        paper_text=paper_text,
        pdf_path=pdf_path,
        input_text=input_text
    )
    if error:
        async def error_gen():
            yield f"Error: {error}"
        return StreamingResponse(error_gen(), media_type='text/plain; charset=utf-8')

    text = result or "(no result)"

    async def stream_gen():
        # Simple chunking into ~200-char pieces so the UI can show progressive output
        chunk_size = 200
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            yield chunk
        # final newline to signal completion
        yield '\n'

    return StreamingResponse(stream_gen(), media_type='text/plain; charset=utf-8')


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)