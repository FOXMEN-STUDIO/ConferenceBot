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
    {"id": "questionaire", "name": "Questionnaire Designer"},
    {"id": "sample_size", "name": "Sample Size Calculator"},
    {"id": "statistical", "name": "Statistical Test Selector"},
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

        elif bot_id == "questionaire":
            from src.Questioniare.question import generate_questionnaire
            example_input = {
                "variables": kwargs.get("variables", ""),
                "population": kwargs.get("population", ""),
                "culture": kwargs.get("culture", ""),
                "language": kwargs.get("language", "English"),
                "scale": kwargs.get("scale", "5"),
                "domain": kwargs.get("domain", "")
            }
            return generate_questionnaire(example_input), None

        elif bot_id == "sample_size":
            from src.sample_sizeBot.sample_size import SampleSizeBot
            bot = SampleSizeBot()
            mode = kwargs.get("mode", "prevalence")
            if mode == "prevalence":
                p = float(kwargs.get("p", 0.5))
                d = float(kwargs.get("d", 0.05))
                pop = kwargs.get("population")
                pop = int(pop) if pop else None
                return f"Recommended sample size: {bot.prevalence(p=p, d=d, population=pop)}", None
            elif mode == "mean":
                sd = float(kwargs.get("std_dev", 1.0))
                d = float(kwargs.get("d", 1.0))
                return f"Recommended sample size: {bot.mean_estimation(std_dev=sd, d=d)}", None
            elif mode == "regression":
                predictors = int(kwargs.get("predictors", 3))
                return f"Recommended sample size (rule of thumb): {bot.regression(predictors=predictors)}", None

        elif bot_id == "statistical":
            from src.Statistical_test_selector.stat import StatisticalTestSelectorBot
            selector = StatisticalTestSelectorBot()
            iv = kwargs.get("iv_type", "categorical")
            dv = kwargs.get("dv_type", "continuous")
            groups = kwargs.get("groups")
            try:
                groups = int(groups) if groups else None
            except Exception:
                groups = None
            test = selector.select_test(iv_type=iv, dv_type=dv, groups=groups)
            assumptions = selector.assumptions(test)
            return f"Recommended test: {test}\nAssumptions:\n- " + "\n- ".join(assumptions), None

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

    # Extract additional form fields used by newly added bots
    population = form.get('population') or None
    p = form.get('p') or None
    d = form.get('d') or None
    std_dev = form.get('std_dev') or None
    predictors = form.get('predictors') or None
    mode = form.get('mode') or None
    iv_type = form.get('iv_type') or None
    dv_type = form.get('dv_type') or None
    groups = form.get('groups') or None
    variables = form.get('variables') or None
    culture = form.get('culture') or None
    language = form.get('language') or None
    scale = form.get('scale') or None
    domain = form.get('domain') or None

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
        "population": population,
        "p": p,
        "d": d,
        "std_dev": std_dev,
        "predictors": predictors,
        "mode": mode,
        "iv_type": iv_type,
        "dv_type": dv_type,
        "groups": groups,
        "variables": variables,
        "culture": culture,
        "language": language,
        "scale": scale,
        "domain": domain,
    }

    # If PDF / document provided but no question, build an index and/or run automatic analysis
    if bot_id in ("reviewer", "analyst", "conference") and (paper_text or pdf_path) and not question:
        try:
            if bot_id == "reviewer":
                from src.paperReviewerBot.bot import build_index as reviewer_build
                msg = reviewer_build(paper_text or pdf_path)
                # for reviewer we only index and return a readiness message
                return templates.TemplateResponse("bot.html", {
                    "request": request,
                    "bot": bot,
                    "result": msg,
                    "error": None,
                    "last_values": last_values
                })

            elif bot_id == "analyst":
                # For analyst: index and then run full automatic analysis and show the result
                from src.Reseach_AnalysisBot.bot import build_index as analyst_build, Research_paper_analyst
                _ = analyst_build(paper_text or pdf_path)
                analysis = Research_paper_analyst(paper_text or pdf_path)
                return templates.TemplateResponse("bot.html", {
                    "request": request,
                    "bot": bot,
                    "result": analysis,
                    "error": None,
                    "last_values": last_values
                })

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
        input_text=input_text,
        population=population,
        p=p,
        d=d,
        std_dev=std_dev,
        predictors=predictors,
        mode=mode,
        iv_type=iv_type,
        dv_type=dv_type,
        groups=groups,
        variables=variables,
        culture=culture,
        language=language,
        scale=scale,
        domain=domain
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
    # additional fields for sample size / questionnaire / statistical bots
    population = form.get('population')
    p = form.get('p')
    d = form.get('d')
    std_dev = form.get('std_dev')
    predictors = form.get('predictors')
    mode = form.get('mode')
    iv_type = form.get('iv_type')
    dv_type = form.get('dv_type')
    groups = form.get('groups')
    variables = form.get('variables')
    culture = form.get('culture')
    language = form.get('language')
    scale = form.get('scale')
    domain = form.get('domain')

    # Handle uploaded file if provided
    uploaded = form.get('pdf_file')
    if uploaded is not None and getattr(uploaded, 'filename', ''):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        content = await uploaded.read()
        tmp.write(content)
        tmp.flush()
        tmp.close()
        pdf_path = tmp.name

    # If PDF/doc provided but no question - build an index and stream a readiness message OR run analysis for analyst
    if bot_id in ("reviewer", "analyst", "conference") and (paper_text or pdf_path) and not question:
        try:
            if bot_id == "reviewer":
                from src.paperReviewerBot.bot import build_index as reviewer_build
                msg = reviewer_build(paper_text or pdf_path, background=True)
                async def idx_gen():
                    yield msg
                return StreamingResponse(idx_gen(), media_type='text/plain; charset=utf-8')

            elif bot_id == "analyst":
                # For analyst: build index then run automatic analysis and stream the output (synchronous to get immediate analysis)
                from src.Reseach_AnalysisBot.bot import build_index as analyst_build, Research_paper_analyst
                # start background index for persistence and speed next time
                _ = analyst_build(paper_text or pdf_path, background=True)
                # run immediate analysis and stream result
                analysis = Research_paper_analyst(paper_text or pdf_path)
                async def analysis_gen():
                    yield analysis
                return StreamingResponse(analysis_gen(), media_type='text/plain; charset=utf-8')

            else:
                from src.conferencebot.bot import build_index as conf_build
                msg = conf_build(paper_text or pdf_path, background=True)
                async def idx_gen():
                    yield msg
                return StreamingResponse(idx_gen(), media_type='text/plain; charset=utf-8')
        except Exception as e:
            pass

    # Attempt to use streaming generator from the bot module (if implemented)
    try:
        if bot_id == 'conference':
            from src.conferencebot.bot import conference_bot_stream
            return StreamingResponse(conference_bot_stream(question or '', source=paper_text or pdf_path), media_type='text/plain; charset=utf-8')
        elif bot_id == 'reviewer':
            from src.paperReviewerBot.bot import paper_reviewer_rag_stream
            return StreamingResponse(paper_reviewer_rag_stream(paper_text or pdf_path, question or ''), media_type='text/plain; charset=utf-8')
        elif bot_id == 'analyst':
            from src.Reseach_AnalysisBot.bot import Research_paper_analyst_stream
            return StreamingResponse(Research_paper_analyst_stream(paper_text or pdf_path), media_type='text/plain; charset=utf-8')
    except Exception:
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
        input_text=input_text,
        population=population,
        p=p,
        d=d,
        std_dev=std_dev,
        predictors=predictors,
        mode=mode,
        iv_type=iv_type,
        dv_type=dv_type,
        groups=groups,
        variables=variables,
        culture=culture,
        language=language,
        scale=scale,
        domain=domain
    )

    # Post-process formatting for nicer UI output
    try:
        from src.utils.formatter import format_for_bot
        if result:
            result = format_for_bot(bot_id, result)
    except Exception:
        pass
    if error:
        async def error_gen():
            yield f"Error: {error}"
        return StreamingResponse(error_gen(), media_type='text/plain; charset=utf-8')

    text = result or "(no result)"

    async def stream_gen():
        # Chunk at sentence boundaries for cleaner streaming
        from src.utils.formatter import chunk_text_for_stream
        for chunk in chunk_text_for_stream(text, max_chars=240):
            yield chunk
        # final newline to signal completion
        yield '\n'
    return StreamingResponse(stream_gen(), media_type='text/plain; charset=utf-8')


@app.post('/render_markdown')
async def render_markdown(request: Request):
    """Simple endpoint that accepts raw markdown (form field 'md') and returns sanitized HTML."""
    form = await request.form()
    md = form.get('md') or ''
    from src.utils.formatter import safe_markdown_to_html
    html_out = safe_markdown_to_html(md)
    return HTMLResponse(content=html_out)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)