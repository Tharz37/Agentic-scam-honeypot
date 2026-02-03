from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from agent import get_honeypot_response
from schema import ScamIntelligence

app = FastAPI(title="HoneyPot Agent API")

class Message(BaseModel):
    role: str
    content: str

class ChatInput(BaseModel):
    history: List[Message]
    persona: str = "Uncle Ramesh"
    # ADDED: Context field to pass intelligence status
    context: Optional[Dict] = {}

@app.post("/interact", response_model=ScamIntelligence)
async def interact_endpoint(input_data: ChatInput):
    try:
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in input_data.history]
        
        # Pass context to the agent function
        result = get_honeypot_response(
            conversation_history=history_dicts, 
            persona_name=input_data.persona,
            context=input_data.context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)