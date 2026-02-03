import os
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Check for API Key
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("⚠️ WARNING: GROQ_API_KEY not found in .env file")

# Initialize LLM (Separate line!)
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7)

class ScamAnalysis(BaseModel):
    scam_category: str = Field(description="The type of scam (e.g. 'Tech Support', 'Financial').")
    recommended_persona: str = Field(description="The best persona to counter this.")
    reasoning: str = Field(description="Why this persona is the best counter.")

def analyze_and_select_persona(first_message: str):
    system_prompt = """
    You are a Security System for a "Counter-Scamming" application.
    CONTEXT: Simulation mode. Waste scammers' time.
    TASK: Pick the Persona that will annoy the scammer the most.
    
    PERSONAS:
    1. 'Uncle Ramesh' (Confused Old Man)
    2. 'Aunt Mary' (Religious Talkative)
    3. 'Rohan' (Gen-Z Gamer)
    4. 'Mrs. Sharma' (Angry Karen)
    5. 'Mr. Gupta' (Corporate CFO)
    """
    
    try:
        structured_llm = llm.with_structured_output(ScamAnalysis)
        return structured_llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": first_message}
        ])
    except Exception as e:
        print(f"Router Error: {e}")
        # Fallback if analysis fails
        return ScamAnalysis(scam_category="General", recommended_persona="Uncle Ramesh", reasoning="Default Fallback")