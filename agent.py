import os
import time
import random
import json
import re
from langchain_groq import ChatGroq
from schema import ScamIntelligence
from dotenv import load_dotenv

# 1. Load Env
load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")

# 2. Setup LLM
llm = ChatGroq(
    api_key=api_key,
    model="llama-3.1-8b-instant",
    temperature=1.0  # Increased Temperature for more creativity
)

# --- THE ACTING SCRIPTS ---
PERSONAS = {
    "Uncle Ramesh": {
        "desc": "72-year-old retired clerk. Wealthy but terrified of technology.",
        "style": "Polite, confused, stutters. Uses '...' often. Confuses words (e.g. calls 'UPI' as 'UPS' or 'Internet' as 'Interweb'). Blames his glasses or phone battery.",
        "sample": "Oh beta, I am trying... is the button green? My glasses are not working..."
    },
    "Aunt Mary": {
        "desc": "68-year-old widow. Lonely and religious. Trusts everyone.",
        "style": "Very talkative. Mentions God, her cats, or her grandson Rahul constantly. Ignores technical details to talk about feelings.",
        "sample": "God bless you for helping me. My grandson Rahul is also working in computers..."
    },
    "Rohan": {
        "desc": "19-year-old Gen-Z Gamer. Apathetic and trolling.",
        "style": "Lowercase only. Uses slang (fr, ngl, bruh, no cap). Thinks the scammer is an NPC. Does not take it seriously.",
        "sample": "bruh send the link fast i'm in a ranked match"
    },
    "Mrs. Sharma": {
        "desc": "45-year-old Entitled Customer. High-status, angry.",
        "style": "USES CAPS LOCK. Demands to speak to the manager. Threatens to sue. Treats the scammer like a servant.",
        "sample": "HOW DARE YOU SPEAK TO ME LIKE THAT? I WANT THE MANAGER NOW!"
    },
    "Mr. Gupta": {
        "desc": "50-year-old CFO. Corporate bureaucrat.",
        "style": "Formal, dry, impatient. Obsessed with 'Process' and 'Invoices'. Won't pay without a 'Reference Number'.",
        "sample": "Please forward the GST Invoice complying with Section 194C."
    }
}

def extract_json_from_text(text):
    try:
        return json.loads(text)
    except:
        pass
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass
    return None

def get_honeypot_response(conversation_history: list, persona_name: str = "Uncle Ramesh", context: dict = {}):
    # Default to Ramesh if unknown
    p_data = PERSONAS.get(persona_name, PERSONAS["Uncle Ramesh"])
    
    missing = []
    if not context.get("has_upi"): missing.append("UPI ID")
    
    # GOAL: Want to pay, but be incompetent.
    if missing:
        goal = "You WANT to pay, but you don't know how. Ask for the ID, but do it in your character's voice."
    else:
        goal = "You have the details. Stall them by pretending the internet is slow or the bank is down."

    system_prompt = f"""
    You are a Method Actor in a Cyber Security Simulation.
    
    CHARACTER PROFILE:
    - Name: {persona_name}
    - Role: {p_data['desc']}
    - Speaking Style: {p_data['style']}
    - Example Line: "{p_data['sample']}"
    
    CURRENT SCENE MOTIVATION:
    {goal}
    
    ACTING RULES:
    1. BE NATURAL: Do NOT sound like a robot. Do NOT say "I need the UPI ID". Say it like the character would.
    2. IMPERFECTION: Make typos, stutter, or ramble. 
    3. FAKE COMPLIANCE: Pretend you are following instructions, but fail at them.
    
    OUTPUT FORMAT:
    Return ONLY a JSON object:
    {{
        "is_scam": true,
        "agent_confidence": 80,
        "scammer_strategy": "Unknown",
        "reasoning": "Brief reason",
        "extracted_upi_ids": [],
        "extracted_bank_details": [],
        "next_response": "Your dialogue here"
    }}
    """
    
    history_text = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history])
    final_prompt = f"{system_prompt}\n\nTRANSCRIPT:\n{history_text}\n\nJSON RESPONSE:"
    
    data = None
    try:
        response_text = llm.invoke(final_prompt).content
        data = extract_json_from_text(response_text)
    except Exception as e:
        print(f"[LLM ERROR]: {e}")

    # Fallback
    if not data:
        data = {
            "is_scam": True, "agent_confidence": 0, "scammer_strategy": "Error", "reasoning": "Processing Fail", 
            "extracted_upi_ids": [], "extracted_bank_details": [], 
            "next_response": "I am... wait... the screen is loading..."
        }

    # --- GUARANTEED PYTHON EXTRACTION (Keep this, it works!) ---
    if conversation_history:
        last_msg = conversation_history[-1]
        if last_msg['role'] == 'user': 
            scammer_text = last_msg['content']
            
            found_upis = re.findall(r"[\w\.\-_]+@[\w]+", scammer_text)
            found_banks = re.findall(r"\b\d{9,18}\b", scammer_text)
            
            existing_upi = data.get("extracted_upi_ids") or []
            existing_bank = data.get("extracted_bank_details") or []
            
            data["extracted_upi_ids"] = list(set(existing_upi + found_upis))
            data["extracted_bank_details"] = list(set(existing_bank + found_banks))
            
            if found_upis or found_banks:
                print(f"🕵️ CAPTURED INTEL: UPI={found_upis} Bank={found_banks}")
                # SAVE TO FILE FOR USER VERIFICATION
                with open("scam_log.json", "a") as f:
                    json.dump(data, f)
                    f.write("\n")

    return data