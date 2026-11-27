from pydantic import BaseModel, Field
from typing import Optional

class ResearchRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=200)
    target_market: str = Field(..., min_length=1, max_length=200)
    research_goal: str = Field(..., min_length=5, max_length=2000)
    language: str = "en"
    include_competitors: bool = True
    additional_context: Optional[str] = Field(default=None, max_length=5000)

class ResearchReport(BaseModel):
    executive_summary: str
    market_overview: str
    target_customers: list[str]
    opportunities: list[str]
    risks: list[str]
    competitor_landscape: list[str]
    recommended_next_steps: list[str]
    assumptions_and_limitations: list[str]
    disclaimer: str
