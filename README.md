# 🛡️ Agentic Scam-Honeypot: Autonomous Cyber Defense System

> **Submission for India AI Impact Buildathon**

## 🚨 The Problem
Digital fraud in India is skyrocketing, with scammers using social engineering to target vulnerable populations. Tracking these burner accounts manually is slow and reactive. We needed a proactive defense system that doesn't just block scams, but **fights back**.

## 💡 The Solution
**Agentic Scam-Honeypot** is an autonomous AI agent that turns the tables on scammers. Instead of blocking the threat, it detects the scam type, adopts a counter-persona (e.g., a confused elderly person or an angry customer), and engages the attacker in a realistic conversation.

The system's primary goal is **Intelligence Gathering**: it lures the scammer into revealing their "drop" accounts (UPI IDs, Bank Numbers) and logs them for Cyber Cells to take action.

## ⚡ Key Features

### 🎭 Dynamic Persona Engine ("Method Acting")
The AI doesn't just chat; it *acts*. It selects the best persona to frustrate the specific scammer:
- **Uncle Ramesh:** 72yo, tech-illiterate (Good for stalling Tech Support scams).
- **Mrs. Sharma:** Angry, high-status (Good for stalling Service/Bill scams).
- **Rohan:** Apathetic Gen-Z gamer (Good for trolling).

### 🕵️ Zero-Shot Intelligence Extraction
We don't rely on the LLM alone. The system uses a **Hybrid Extraction Layer** (LLM + Python Regex) to scan every message for financial identifiers. It captures:
- UPI IDs (`boss@scam`, `paytm@...`)
- Bank Account Numbers
- IFSC Codes

### 🧠 Adaptive Adversarial Logic
- **Crash-Proof Architecture:** Self-healing JSON parsers ensure the agent never breaks character.
- **Human-Like Latency:** Simulates typing speeds and errors to bypass scammer suspicion.
- **Trap Triggers:** Autonomously detects when a scammer is hooked and forces a "Leak" scenario.

## 🛠️ Tech Stack
- **Core Brain:** Llama-3-8B-Instant (via Groq) for sub-second latency.
- **Orchestration:** LangChain & Python.
- **Frontend:** Streamlit (Real-time "WhatsApp-style" interface).
- **Backend:** FastAPI.
- **Security:** Python-Dotenv for key management.

## 🚀 How to Run Locally

1. **Clone the Repository**
   ```bash
   git clone [https://github.com/Tharz37/Agentic-scam-honeypot.git](https://github.com/Tharz37/Agentic-scam-honeypot.git)
   cd Agentic-scam-honeypot 
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt 
   ```

3. **Clone the Repository**
   
   Set up Environment Create a .env file and add your Groq API keys:
   ```bash
   GROQ_API_KEY=your_key_here
   GROQ_API_KEY_SCAMMER=your_key_here 
   ```

4. **Launch the System**
   
# Terminal 1: Start the Backend
```bash
python main.py
```

# Terminal 2: Start the Dashboard
```bash
streamlit run dashboard.py
```