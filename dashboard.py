import streamlit as st
import requests
import time
import os
import random
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
scammer_api_key = os.environ.get("GROQ_API_KEY_SCAMMER")
if not scammer_api_key:
    st.error("🚨 CRITICAL ERROR: GROQ_API_KEY_SCAMMER missing!")
    st.stop()

# Import the NEW RL functions
from router import select_persona_with_rl, update_rl_reward
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

# --- CONFIG ---
HONEYPOT_API_URL = "https://agentic-scam-honeypot-j8mq.onrender.com"

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
    # FORCE LEAK if victim asks for it
    last_message = history[-1]["content"].lower()
    triggers = ["upi", "account", "pay", "send", "details", "number", "how"]
    
    if any(keyword in last_message for keyword in triggers):
        return ScammerThought(
            internal_thought="Hooked. Giving details.",
            scammer_confidence=100,
            dialogue_message="Send money to UPI: boss@scam or Bank: 8822334455. Send screenshot."
        )

    system_prompt = f"ROLE: Scammer. VICTIM: {persona}. GOAL: Pressure them."
    try:
        structured = scammer_llm.with_structured_output(ScammerThought)
        msgs = [{"role": "system", "content": system_prompt}] + \
               [{"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]} for m in history]
        return structured.invoke(msgs)
    except:
        return ScammerThought(internal_thought="Fallback", scammer_confidence=80, dialogue_message="Pay now.")

# --- UI SETUP ---
st.set_page_config(page_title="Agentic Honeypot", layout="wide")
st.markdown("""<style>.stApp { background-color: #0e1117; }</style>""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

if "messages" not in st.session_state: st.session_state.messages = []
if "running" not in st.session_state: st.session_state.running = False
if "persona" not in st.session_state: st.session_state.persona = "Auto"
if "scam_category" not in st.session_state: st.session_state.scam_category = "General"
if "json_log" not in st.session_state: st.session_state.json_log = []
if "reward_given" not in st.session_state: st.session_state.reward_given = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎮 Cyber Control")
    mode = st.radio("Mode", ["Auto-Pilot", "Manual"])
    
    if mode == "Auto-Pilot":
        if st.button("🎲 Random Threat"):
            st.session_state.messages = []
            st.session_state.json_log = []
            st.session_state.reward_given = False
            
            threat = random.choice(["Netflix Payment Failed", "Customs Duty Unpaid", "Lottery Winner"])
            
            # --- RL SELECTION ---
            with st.spinner("RL Brain selecting best persona..."):
                p, cat = select_persona_with_rl(threat)
                st.session_state.persona = p
                st.session_state.scam_category = cat
                st.toast(f"Brain selected: {p} for {cat} Scam")
            
            st.session_state.messages.append({"role": "user", "content": threat, "conf": 100})
            st.session_state.running = True
            st.rerun()

    # DATA EXPORT BUTTON
    if st.button("💾 Export Intel (CSV)"):
        if st.session_state.json_log:
            df = pd.DataFrame(st.session_state.json_log)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download CSV", csv, "scam_data.csv", "text/csv")
            st.success("Exported!")
        else:
            st.warning("No intel yet.")
            
    if st.button("🛑 STOP"):
        st.session_state.running = False
        st.rerun()

# --- MAIN LOOP ---
with col1:
    st.subheader("🔴 Live Feed")
    for msg in st.session_state.messages:
        role = "😈 Target" if msg["role"] == "user" else f"🛡️ {st.session_state.persona}"
        with st.chat_message(role):
            if msg.get("thought"): st.caption(f"💭 {msg['thought']}")
            st.write(msg["content"])

    # INFINITE LOOP LOGIC
    if mode == "Auto-Pilot" and st.session_state.running:
        last_msg = st.session_state.messages[-1]
        
        # CHECK FOR INTEL
        has_upi = any(log.get("extracted_upi_ids") for log in st.session_state.json_log)
        
        # IF INTEL FOUND -> GIVE REWARD (ONCE) -> BUT DO NOT STOP!
        if has_upi and not st.session_state.reward_given:
            st.toast("✅ INTEL CAPTURED! RL Model Rewarded (+0.5). Continuing...")
            update_rl_reward(st.session_state.scam_category, st.session_state.persona, True)
            st.session_state.reward_given = True

        if last_msg["role"] == "user": # Agent Turn
            with st.spinner(f"{st.session_state.persona} stalling..."):
                time.sleep(1)
                try:
                    ctx = {"has_upi": has_upi}
                    hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    res = requests.post(HONEYPOT_API_URL, json={"history": hist, "persona": st.session_state.persona, "context": ctx}, timeout=15)
                    
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.messages.append({"role": "assistant", "content": data.get("next_response", "..."), "conf": 0})
                        # Log if intel found
                        if data.get("extracted_upi_ids") or data.get("extracted_bank_details"):
                            st.session_state.json_log.append(data)
                        st.rerun()
                    else:
                        # --- THIS WAS MISSING ---
                        st.error(f"⚠️ SERVER ERROR {res.status_code}: {res.text}")
                        st.session_state.running = False
                except Exception as e:
                    st.error(f"⚠️ CONNECTION ERROR: {e}")
                    st.session_state.running = False
        
        elif last_msg["role"] == "assistant": # Scammer Turn
            with st.spinner("😈 Scammer..."):
                time.sleep(1.5)
                hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                move = get_scammer_move(hist, st.session_state.persona)
                st.session_state.messages.append({"role": "user", "content": move.dialogue_message, "thought": move.internal_thought, "conf": move.scammer_confidence})
                st.rerun()

with col2:
    st.header("🕵️ Evidence")
    all_upi = {u for log in st.session_state.json_log for u in log.get("extracted_upi_ids", [])}
    if all_upi: 
        st.success(f"✅ UPI: {list(all_upi)}")
        st.info("Agent is now wasting scammer's time...")
    else: 
        st.warning("Scanning for details...")