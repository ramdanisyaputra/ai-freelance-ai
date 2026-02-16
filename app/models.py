from pydantic import BaseModel, Field
from typing import List, Optional


class FreelancerProfile(BaseModel):
    """Freelancer profile information."""
    stack: List[str]
    rate_type: str
    min_price: int
    currency: str


class ProposalRequest(BaseModel):
    """Request payload for proposal generation."""
    proposal_id: int
    brief: str
    user_brief: Optional[str] = None
    language: str = Field(default="id", description="Language code: 'en' or 'id'")
    freelancer_profile: FreelancerProfile
    callback_url: str


class ProposalScope(BaseModel):
    """Individual scope item."""
    title: str
    description: Optional[str] = None


class ProposalEstimation(BaseModel):
    """Estimation details."""
    duration_days: int
    price: int


class ProposalResponse(BaseModel):
    """Response payload for generated proposal."""
    proposal_id: int
    status: str = Field(default="completed")
    need_clarification: bool = False
    summary: str
    scope: List[str]
    estimation: ProposalEstimation
    content: str  # HTML content
    error: Optional[str] = None
