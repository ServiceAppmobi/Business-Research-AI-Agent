# AI Business Research Agent

A multilingual MVP API for generating structured business research reports with Google Gemini.

## Current scope
- FastAPI REST API
- 11 output languages
- Structured research brief and report schema
- Gemini API integration
- Health endpoint and basic tests

## Important limitation
This MVP generates AI-assisted analysis from the information provided in the request. It does **not** yet perform live web research, verify facts, or attach source citations. Do not market its output as independently verified market intelligence until retrieval, source tracking, and human validation are implemented.

## Requirements
- Python 3.11+
- Google Gemini API key (API access and billing are separate from consumer Google AI subscriptions)

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add GEMINI_API_KEY to .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs.

## API
- `GET /health`
- `POST /api/v1/research`

Example request:
```json
{
  "company": "Example Ltd",
  "industry": "Residential property maintenance",
  "target_market": "Spain",
  "research_goal": "Assess market entry opportunities",
  "language": "en",
  "include_competitors": true,
  "additional_context": "Focus on small and medium-sized businesses"
}
```

## Roadmap
1. Live web retrieval and source citations
2. Evidence grading and fact-check workflow
3. Authentication, usage limits, and saved reports
4. Payments and customer portal
5. Production deployment, monitoring, and privacy controls
