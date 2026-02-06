from pydantic import BaseModel, Field
from typing import List, Optional, Union, Any

# --- 1. THE INVINCIBLE INPUT MODEL ---
class UserInput(BaseModel):
    # Accept List OR String (prevents "Input should be a valid list" error)
    history: Optional[Union[List[dict], str, Any]] = None
    
    # Accept other fields just in case
    message: Optional[str] = None 
    text: Optional[str] = None
    input: Optional[str] = None

# --- 2. THE OUTPUT MODEL (Keep this same) ---
class ScamIntelligence(BaseModel):
    is_scam: bool = Field(description="True if scam detected")
    agent_confidence: int = Field(description="0-100 score")
    scammer_strategy: str = Field(description="e.g. Job Scam, Lottery")
    reasoning: str = Field(description="Brief reason for the decision")
    extracted_upi_ids: List[str] = Field(default_factory=list)
    extracted_bank_details: List[str] = Field(default_factory=list)
    extracted_phishing_links: List[str] = Field(default_factory=list)
    next_response: str = Field(description="Response to scammer")