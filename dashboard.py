import streamlit as st
import requests
import time
import os
import random
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

# 2. Retrieve the Scammer API Key
scammer_api_key = os.environ.get("GROQ_API_KEY_SCAMMER")

# 3. Safety Check
if not scammer_api_key:
    st.error("🚨 CRITICAL ERROR: GROQ_API_KEY_SCAMMER is missing from .env file!")
    st.stop()

# Ensure router.py exists
from router import analyze_and_select_persona 
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

# --- CONFIG ---
HONEYPOT_API_URL = "http://localhost:8000/interact"

scammer_llm = ChatGroq(
    api_key=scammer_api_key,
    model="llama-3.1-8b-instant",
    temperature=0.8
)

class ScammerThought(BaseModel):
    internal_thought: str = Field(description="Tactical reasoning.")
    scammer_confidence: int = Field(description="0-100.")
    dialogue_message: str = Field(description="Message to victim.")

def get_scammer_move(history, persona):
    # --- THE FIX: FORCED TRIGGER LOGIC ---
    # Look at the last message from the Victim (User role in history)
    last_message = history[-1]["content"].lower()
    
    # Keywords that indicate the Victim is ready to pay
    triggers = ["upi", "account", "pay", "send", "details", "number", "how", "amount"]
    
    if any(keyword in last_message for keyword in triggers):
        # BYPASS THE AI -> FORCE THE LEAK
        return ScammerThought(
            internal_thought="The victim is hooked! Giving them the details now.",
            scammer_confidence=100,
            dialogue_message="Okay, listen carefully. Send the money immediately to UPI: boss@scam or Bank Account: 8822334455 (IFSC: SCAM001). Send me the screenshot once done."
        )

    # --- NORMAL AI LOGIC (Only runs if no trigger found) ---
    system_prompt = f"""
    ROLE: You are 'Vikram', a Scammer.
    VICTIM: {persona}.
    GOAL: Pressure them to pay.
    INSTRUCTIONS: 
    1. Threaten them with legal action or loss of service.
    2. Keep your messages short and urgent.
    """
    try:
        structured_scammer = scammer_llm.with_structured_output(ScammerThought)
        msgs = [{"role": "system", "content": system_prompt}] + \
               [{"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]} for m in history]
        return structured_scammer.invoke(msgs)
    except:
        return ScammerThought(internal_thought="Fallback", scammer_confidence=80, dialogue_message="Pay the duty immediately to avoid arrest.")

# --- UI SETUP ---
st.set_page_config(page_title="Cyber Defense Simulator", layout="wide")
st.markdown("""<style>.stApp { background-color: #0e1117; }</style>""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

if "messages" not in st.session_state: st.session_state.messages = []
if "running" not in st.session_state: st.session_state.running = False
if "persona" not in st.session_state: st.session_state.persona = "Auto"
if "scam_analysis" not in st.session_state: st.session_state.scam_analysis = None
if "json_log" not in st.session_state: st.session_state.json_log = []

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎮 Controls")
    mode = st.radio("Mode", ["Auto-Pilot (AI vs AI)", "Manual (Human vs AI)"])
    
    if mode == "Auto-Pilot (AI vs AI)":
        if st.button("🎲 Random Threat"):
            st.session_state.messages = []
            st.session_state.json_log = []
            scams = [
                "Netflix: Payment Declined. Update now.", 
                "Customs: Package held. Pay duty.", 
                "CBI: Warrant issued. Pay fine."
            ]
            threat = random.choice(scams)
            
            with st.spinner("Analyzing..."):
                analysis = analyze_and_select_persona(threat)
                st.session_state.persona = analysis.recommended_persona
            
            st.session_state.messages.append({"role": "user", "content": threat, "conf": 100})
            st.session_state.running = True
            st.rerun()

    else:
        st.session_state.persona = st.selectbox("Defender", ["Auto-Detect", "Uncle Ramesh", "Aunt Mary", "Rohan", "Mrs. Sharma", "Mr. Gupta"])
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.session_state.json_log = []
            st.rerun()
            
    if st.button("🛑 STOP"):
        st.session_state.running = False
        st.rerun()

# --- MAIN FEED ---
with col1:
    st.subheader("🔴 Live Feed")
    
    for msg in st.session_state.messages:
        role = "😈 Target" if msg["role"] == "user" else f"🛡️ {st.session_state.persona}"
        with st.chat_message(role):
            if msg.get("thought"): st.caption(f"💭 {msg['thought']}")
            st.write(msg["content"])

    # MANUAL INPUT
    if mode == "Manual (Human vs AI)":
        if user_in := st.chat_input("Scam message..."):
            if not st.session_state.messages and st.session_state.persona == "Auto-Detect":
                with st.spinner("Profiling..."):
                    analysis = analyze_and_select_persona(user_in)
                    st.session_state.persona = analysis.recommended_persona
            
            st.session_state.messages.append({"role": "user", "content": user_in, "thought": "Manual"})
            
            with st.spinner(f"{st.session_state.persona} thinking..."):
                has_upi = any(log.get("extracted_upi_ids") for log in st.session_state.json_log)
                has_bank = any(log.get("extracted_bank_details") for log in st.session_state.json_log)
                ctx = {"has_upi": has_upi, "has_bank": has_bank}
                hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                
                try:
                    res = requests.post(HONEYPOT_API_URL, json={"history": hist, "persona": st.session_state.persona, "context": ctx}, timeout=15)
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.messages.append({"role": "assistant", "content": data.get("next_response", "..."), "conf": data.get("agent_confidence", 0)})
                        st.session_state.json_log.append(data)
                        st.rerun()
                    else:
                        st.error(f"API Error {res.status_code}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")

    # AUTO LOOP
    if mode == "Auto-Pilot (AI vs AI)" and st.session_state.running:
        last_msg = st.session_state.messages[-1]
        
        has_upi = any(log.get("extracted_upi_ids") for log in st.session_state.json_log)
        has_bank = any(log.get("extracted_bank_details") for log in st.session_state.json_log)
        if has_upi and has_bank:
            st.success("✅ MISSION COMPLETE")
            st.stop()

        if last_msg["role"] == "user":
            with st.spinner(f"{st.session_state.persona}..."):
                time.sleep(1)
                try:
                    ctx = {"has_upi": has_upi, "has_bank": has_bank}
                    hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    res = requests.post(HONEYPOT_API_URL, json={"history": hist, "persona": st.session_state.persona, "context": ctx}, timeout=15)
                    
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.messages.append({"role": "assistant", "content": data.get("next_response", "..."), "conf": data.get("agent_confidence", 0)})
                        st.session_state.json_log.append(data)
                        st.rerun()
                    else:
                        st.error(f"⚠️ API Error {res.status_code}: {res.text}")
                        st.session_state.running = False
                except Exception as e:
                    st.error(f"⚠️ Connection Error: {e}")
                    st.info("Check if main.py is running!")
                    st.session_state.running = False
        
        elif last_msg["role"] == "assistant":
            with st.spinner("😈 Scammer..."):
                time.sleep(1.5)
                hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                move = get_scammer_move(hist, st.session_state.persona)
                st.session_state.messages.append({"role": "user", "content": move.dialogue_message, "thought": move.internal_thought, "conf": move.scammer_confidence})
                st.rerun()

with col2:
    st.header("🕵️ Evidence")
    all_upi = {u for log in st.session_state.json_log for u in log.get("extracted_upi_ids", [])}
    all_bank = {b for log in st.session_state.json_log for b in log.get("extracted_bank_details", [])}
    if all_upi: st.success(f"✅ UPI: {list(all_upi)}")
    else: st.warning("⬜ UPI: Scanning...")
    if all_bank: st.success(f"✅ Bank: {list(all_bank)}")
    else: st.warning("⬜ Bank: Scanning...")