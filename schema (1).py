from pydantic import BaseModel, Field
from typing import List, Optional

# --- 1. THE INPUT MODEL (Flexible for Dumb Testers) ---
class UserInput(BaseModel):
    history: Optional[List[dict]] = None
    message: Optional[str] = None 
    text: Optional[str] = None
    input: Optional[str] = None

# --- 2. THE OUTPUT MODEL (Your Intelligence Response) ---
class ScamIntelligence(BaseModel):
    is_scam: bool = Field(description="True if scam detected")
    agent_confidence: int = Field(description="0-100 score")
    scammer_strategy: str = Field(description="e.g. Job Scam, Lottery")
    reasoning: str = Field(description="Brief reason for the decision")
    extracted_upi_ids: List[str] = Field(default_factory=list)
    extracted_bank_details: List[str] = Field(default_factory=list)
    extracted_phishing_links: List[str] = Field(default_factory=list)
    next_response: str = Field(description="Response to scammer")