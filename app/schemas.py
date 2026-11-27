from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class ResearchRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=200)
    target_market: str = Field(..., min_length=1, max_length=200)
    research_goal: str = Field(..., min_length=5, max_length=2000)
    language: str = "en"
    include_competitors: bool = True
    additional_context: Optional[str] = Field(default=None, max_length=5000)

class CheckoutRequest(BaseModel):
    customer_email: EmailStr
    research: ResearchRequest

class CheckoutResponse(BaseModel):
    order_id: str
    checkout_url: str

class SourceReference(BaseModel):
    title: str
    url: str
    snippet: str = ""

class ResearchReport(BaseModel):
    executive_summary: str
    market_overview: str
    target_customers: list[str]
    opportunities: list[str]
    risks: list[str]
    competitor_landscape: list[str]
    recommended_next_steps: list[str]
    assumptions_and_limitations: list[str]
    citations: list[SourceReference] = Field(default_factory=list)
    research_method: str
    disclaimer: str
