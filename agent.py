import os
import time
import random
import json
import re
from datetime import datetime
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# 1. Load Env
load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")

# 2. Setup LLM (High Temperature for Creativity)
llm = ChatGroq(
    api_key=api_key,
    model="llama-3.1-8b-instant",
    temperature=1.0 
)

PERSONAS = {
    "Uncle Ramesh": "72yo Retired Clerk. Confused, slow. Calls 'UPI' as 'UPS'. Blames his glasses.",
    "Aunt Mary": "68yo Widow. Religious, chatty. Talks about her grandson Rahul. Trusts blindly.",
    "Rohan": "19yo Gamer. Trolling. Uses slang (fr, ngl, bruh). Thinks scammer is an NPC.",
    "Mrs. Sharma": "45yo Karen. Angry. Demands manager. Threatens to sue.",
    "Mr. Gupta": "50yo CFO. Demands GST Invoice and Reference Numbers."
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
    p_data = PERSONAS.get(persona_name, PERSONAS["Uncle Ramesh"])
    
    missing = []
    if not context.get("has_upi"): missing.append("UPI ID")
    
    # GOAL: Infinite Stall
    if missing:
        goal = "You want to pay, but fail at the steps. Ask for the ID."
    else:
        goal = "INTEL CAPTURED. Now just waste their time. Pretend payment failed. Ask to try again."

    system_prompt = f"""
    You are a Method Actor in a Cyber Security Simulation.
    ROLE: {p_data}
    CURRENT GOAL: {goal}
    
    RULES:
    1. BE NATURAL: Use the specific speaking style of the persona.
    2. IMPERFECTION: Make typos, stutter.
    3. INFINITE LOOP: If you have the details, DO NOT STOP. Create new problems.
    
    OUTPUT FORMAT (JSON):
    {{
        "next_response": "Your dialogue here"
    }}
    """
    
    history_text = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history])
    final_prompt = f"{system_prompt}\n\nTRANSCRIPT:\n{history_text}\n\nJSON RESPONSE:"
    
    # Default State
    data = {"next_response": "..."}
    
    try:
        response_text = llm.invoke(final_prompt).content
        extracted = extract_json_from_text(response_text)
        if extracted: 
            data = extracted
        else:
            # Fallback if no JSON found, assume the whole text is dialogue
            data["next_response"] = response_text
    except Exception as e:
        print(f"[LLM ERROR]: {e}")

    # --- PYTHON INTEL EXTRACTION ---
    extracted_upis = []
    extracted_banks = []

    if conversation_history:
        last_msg = conversation_history[-1]
        if last_msg['role'] == 'user': 
            scammer_text = last_msg['content']
            
            extracted_upis = re.findall(r"[\w\.\-_]+@[\w]+", scammer_text)
            extracted_banks = re.findall(r"\b\d{9,18}\b", scammer_text)
            
            if extracted_upis or extracted_banks:
                print(f"🕵️ CAPTURED: UPI={extracted_upis} Bank={extracted_banks}")
                
                # LOGGING
                log_entry = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "scam_text": scammer_text[:100] + "...",
                    "extracted_upi": extracted_upis,
                    "extracted_bank": extracted_banks,
                    "persona": persona_name
                }
                
                with open("scam_log.json", "a") as f:
                    json.dump(log_entry, f)
                    f.write("\n")

    # --- FINAL SAFETY WRAPPER (THE FIX) ---
    # We force the data into the correct Schema structure so FastAPI doesn't crash.
    final_output = {
        "is_scam": True,
        "agent_confidence": 100,
        "scammer_strategy": "Active Engagement",
        "reasoning": "Persona Active",
        "extracted_upi_ids": extracted_upis,
        "extracted_bank_details": extracted_banks,
        "next_response": data.get("next_response", "I am confusing... please repeat.")
    }

    return final_output