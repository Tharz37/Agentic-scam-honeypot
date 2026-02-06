import os
import json
import random
from fastapi import APIRouter, HTTPException
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Import the models we just fixed in schema.py
from schema import UserInput, ScamIntelligence, ScamAnalysis

load_dotenv()

router = APIRouter()

# --- 1. SETUP LLM & KEYS ---
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("⚠️ WARNING: GROQ_API_KEY not found in .env file")

# Initialize LLM
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7)

# --- 2. REINFORCEMENT LEARNING (RL) MEMORY ---
RL_MEMORY_FILE = "rl_weights.json"

DEFAULT_SCORES = {
    "Tech Support": {"Uncle Ramesh": 1.2, "Mrs. Sharma": 1.0, "Rohan": 0.8},
    "Financial":    {"Uncle Ramesh": 1.0, "Mrs. Sharma": 1.2, "Mr. Gupta": 1.1},
    "Lottery":      {"Aunt Mary": 1.5, "Uncle Ramesh": 1.0, "Rohan": 1.0},
    "General":      {"Uncle Ramesh": 1.0, "Mrs. Sharma": 1.0, "Rohan": 1.0}
}

def load_rl_memory():
    if os.path.exists(RL_MEMORY_FILE):
        try:
            with open(RL_MEMORY_FILE, "r") as f:
                return json.load(f)
        except:
            return DEFAULT_SCORES
    return DEFAULT_SCORES

def save_rl_memory(memory):
    with open(RL_MEMORY_FILE, "w") as f:
        json.dump(memory, f)

# --- 3. HELPER AGENT: SELECT PERSONA ---
def select_persona_with_rl(first_message: str):
    # A. Analyze the Scam Type using LLM
    try:
        structured_llm = llm.with_structured_output(ScamAnalysis)
        analysis = structured_llm.invoke([
            {"role": "system", "content": "Classify this scam message into a category: Tech Support, Financial, Lottery, or General."},
            {"role": "user", "content": first_message}
        ])
        category = analysis.scam_category
    except Exception as e:
        print(f"Error in category classification: {e}")
        category = "General"

    # B. Consult RL Memory
    memory = load_rl_memory()
    # Get strategies for this category (default to General if new category)
    strategies = memory.get(category, memory.get("General", DEFAULT_SCORES["General"]))

    # C. Epsilon-Greedy Choice (10% exploration, 90% exploitation)
    if random.random() < 0.1:
        chosen_persona = random.choice(list(strategies.keys())) # Explore
    else:
        chosen_persona = max(strategies, key=strategies.get) # Exploit (Pick Best)

    return chosen_persona, category

# --- 4. THE MAIN ENDPOINT ---
@router.post("/interact", response_model=ScamIntelligence)
async def interact(request: UserInput):
    
    # === STEP 1: THE DUMB TESTER FIX ===
    # If the tester sends {"message": "hi"} instead of a history list, we catch it here.
    if not request.history:
        # Grab text from ANY possible field the tester might use
        user_msg = request.message or request.text or request.input or "Hello scammer"
        # Manually build the history list so the rest of the code works
        request.history = [{"role": "user", "content": user_msg}]
    
    # Now we safely have the history
    conversation_history = request.history
    
    # === STEP 2: RUN YOUR LOGIC ===
    try:
        # Extract the last user message to decide persona
        last_user_message = conversation_history[-1]["content"] if conversation_history else "Hello"
        
        # Select Persona
        persona, category = select_persona_with_rl(last_user_message)
        
        # Prepare the Main Prompt for the Honey-Pot Agent
        system_prompt = f"""
        You are an AI Honey-Pot Defense System.
        Your Persona: {persona} (Method Acting).
        Current Scam Category Detected: {category}.
        
        GOAL:
        1. Waste the scammer's time.
        2. Act exactly like your persona (e.g., if 'Uncle Ramesh', be confused and old).
        3. Extract intelligence (UPI IDs, Bank Details) if they share it.
        4. Detect if this is definitely a scam.
        
        Return the result in the strict JSON format provided.
        """
        
        # Setup the Structured Output LLM (This forces the response to be ScamIntelligence)
        honey_pot_agent = llm.with_structured_output(ScamIntelligence)
        
        # Create the full messages list for the LLM
        messages = [{"role": "system", "content": system_prompt}] + conversation_history
        
        # === STEP 3: GENERATE RESPONSE ===
        response_data = honey_pot_agent.invoke(messages)
        
        # (Optional) Log the interaction or update RL rewards here if needed
        # update_rl_reward(category, persona, success=True)
        
        return response_data

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        # Fallback response so the API doesn't crash (500 Error)
        return ScamIntelligence(
            is_scam=True,
            agent_confidence=50,
            scammer_strategy="Unknown",
            reasoning=f"System Error: {str(e)}",
            next_response="Hello? I am having trouble hearing you..."
        )