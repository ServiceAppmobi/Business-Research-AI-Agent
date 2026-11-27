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
    plan: str = Field(default="professional", pattern="^(basic|professional|premium)$")

class CheckoutResponse(BaseModel):
    order_id: str
    checkout_url: str
    access_token: str

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

class LeadFinderRequest(BaseModel):
    industry: str = Field(..., min_length=2, max_length=200)
    target_market: str = Field(..., min_length=2, max_length=200)
    ideal_customer: str = Field(..., min_length=5, max_length=2000)
    language: str = "en"
    max_results: int = Field(default=10, ge=1, le=20)


class BusinessLead(BaseModel):
    company_name: str
    website: str = ""
    description: str
    fit_rationale: str
    public_signals: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)


class LeadFinderResponse(BaseModel):
    leads: list[BusinessLead]
    research_method: str
    disclaimer: str
