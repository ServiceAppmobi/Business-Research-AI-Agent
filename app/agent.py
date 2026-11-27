import json
from google import genai
from app.config import settings
from app.languages import SUPPORTED_LANGUAGES
from app.schemas import ResearchRequest, ResearchReport

def generate_report(request: ResearchRequest) -> ResearchReport:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    language_name = SUPPORTED_LANGUAGES[request.language]
    client = genai.Client(api_key=settings.gemini_api_key)

    prompt = f"""
You are an analytical business research assistant.
Prepare a structured, decision-support report in {language_name}.
Be explicit about uncertainty. Do not invent statistics, named competitors,
market shares, citations, or facts. If information is missing, state that
it must be researched and verified. Distinguish assumptions from facts.

Company/context: {request.company}
Industry: {request.industry}
Target market: {request.target_market}
Research goal: {request.research_goal}
Include competitor landscape: {request.include_competitors}
Additional context: {request.additional_context or "None"}

Return ONLY valid JSON with these keys:
executive_summary (string), market_overview (string),
target_customers (array of strings), opportunities (array of strings),
risks (array of strings), competitor_landscape (array of strings),
recommended_next_steps (array of strings),
assumptions_and_limitations (array of strings), disclaimer (string).
The competitor_landscape must be empty if competitor analysis is disabled.
"""

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    data = json.loads(response.text)
    return ResearchReport.model_validate(data)
