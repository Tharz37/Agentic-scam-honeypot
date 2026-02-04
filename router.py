import os
import json
import random
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Check for API Key
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("⚠️ WARNING: GROQ_API_KEY not found in .env file")

# Initialize LLM
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7)

# --- REINFORCEMENT LEARNING MEMORY ---
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

# --- SMART SELECTION AGENT ---
class ScamAnalysis(BaseModel):
    scam_category: str = Field(description="The type of scam (e.g. 'Tech Support', 'Financial', 'Lottery').")

def select_persona_with_rl(first_message: str):
    # 1. Analyze the Scam Type using LLM
    try:
        structured_llm = llm.with_structured_output(ScamAnalysis)
        analysis = structured_llm.invoke([
            {"role": "system", "content": "Classify this scam message into a category: Tech Support, Financial, Lottery, or General."},
            {"role": "user", "content": first_message}
        ])
        category = analysis.scam_category
    except:
        category = "General"

    # 2. Consult RL Memory
    memory = load_rl_memory()
    strategies = memory.get(category, DEFAULT_SCORES["General"])

    # 3. Epsilon-Greedy Choice (10% exploration, 90% exploitation)
    if random.random() < 0.1:
        chosen_persona = random.choice(list(strategies.keys())) # Explore
    else:
        chosen_persona = max(strategies, key=strategies.get) # Exploit (Pick Best)

    return chosen_persona, category

def update_rl_reward(scam_category, persona_used, success):
    """
    Called when we capture Intel. Rewards the persona.
    """
    memory = load_rl_memory()
    
    if scam_category not in memory:
        memory[scam_category] = DEFAULT_SCORES.get(scam_category, DEFAULT_SCORES["General"])
    
    current_score = memory[scam_category].get(persona_used, 1.0)
    
    if success:
        # Reward: Increase score
        memory[scam_category][persona_used] = current_score + 0.5
        print(f"🚀 RL UPDATE: {persona_used} rewarded! New Score: {memory[scam_category][persona_used]}")
    else:
        # Penalty (Optional, usually we just don't reward)
        pass
        
    save_rl_memory(memory)