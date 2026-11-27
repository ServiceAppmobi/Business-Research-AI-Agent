from fastapi import FastAPI, HTTPException
from app.agent import generate_report
from app.languages import SUPPORTED_LANGUAGES
from app.schemas import ResearchRequest, ResearchReport

app = FastAPI(
    title="AI Business Research Agent",
    description="Multilingual AI-assisted business research report API.",
    version="0.1.0",
)

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-business-research-agent"}

@app.get("/api/v1/languages")
def languages():
    return SUPPORTED_LANGUAGES

@app.post("/api/v1/research", response_model=ResearchReport)
def research(request: ResearchRequest):
    if request.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="Unsupported language code")
    try:
        return generate_report(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Report generation failed: {exc}")
