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
    
    # === STEP 1: NORMALIZE THE INPUT ===
    # Initialize an empty history
    final_history = []

    # Check what kind of mess the tester sent us
    if request.history:
        if isinstance(request.history, list):
            # Perfect, it's already a list
            final_history = request.history
        elif isinstance(request.history, str):
            # It sent "history": "Hello", so we convert it to a list
            final_history = [{"role": "user", "content": request.history}]
        else:
            # It sent some weird object, just cast it to string
            final_history = [{"role": "user", "content": str(request.history)}]
    
    # If history was empty/missing, look for other keys
    if not final_history:
        user_msg = request.message or request.text or request.input or "Hello scammer"
        final_history = [{"role": "user", "content": user_msg}]

    # Now we have a clean list, guaranteed.
    conversation_history = final_history

    # === STEP 2: RUN YOUR LOGIC (Same as before) ===
    try:
        last_user_message = conversation_history[-1]["content"] if conversation_history else "Hello"
        
        # ... (Rest of your existing logic) ...
        persona, category = select_persona_with_rl(last_user_message)
        
        system_prompt = f"""
        You are an AI Honey-Pot Defense System.
        Persona: {persona}. Category: {category}.
        Respond in JSON.
        """
        
        honey_pot_agent = llm.with_structured_output(ScamIntelligence)
        messages = [{"role": "system", "content": system_prompt}] + conversation_history
        
        response_data = honey_pot_agent.invoke(messages)
        return response_data

    except Exception as e:
        print(f"ERROR: {e}")
        # Emergency fallback response
        return ScamIntelligence(
            is_scam=True, agent_confidence=50, scammer_strategy="Unknown",
            reasoning="Error recovery", next_response="Hello?"
        )