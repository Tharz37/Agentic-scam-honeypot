from pydantic import BaseModel, Field
from typing import List

class ScamIntelligence(BaseModel):
    is_scam: bool = Field(description="True if scam detected")
    agent_confidence: int = Field(description="0-100 score")
    scammer_strategy: str = Field(description="e.g. Job Scam, Lottery")
    reasoning: str = Field(description="Brief reason for the decision")
    extracted_upi_ids: List[str] = Field(default_factory=list)
    extracted_bank_details: List[str] = Field(default_factory=list)
    next_response: str = Field(description="Response to scammer")