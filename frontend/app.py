"""
app.py – FinBot Streamlit Frontend
Ultra-modern dark cyberpunk-finance aesthetic.
Run: streamlit run frontend/app.py
"""
import os
import time
import uuid
from pathlib import Path

import requests
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinBot — AI Banking Assistant",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
HEALTH_TIMEOUT = 8
CHAT_TIMEOUT = 180
UPLOAD_TIMEOUT = 180

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* ── CSS Variables ── */
:root {
  --bg-base:      #070B14;
  --bg-surface:   #0D1421;
  --bg-elevated:  #121C2E;
  --bg-card:      #0A1120;
  --accent-cyan:  #00D4FF;
  --accent-green: #00FF9D;
  --accent-gold:  #FFB800;
  --accent-pink:  #FF2D78;
  --text-primary: #E8F0FE;
  --text-muted:   #5A7090;
  --text-dim:     #2D4060;
  --border:       rgba(0,212,255,0.12);
  --border-bright:rgba(0,212,255,0.35);
  --glow-cyan:    0 0 20px rgba(0,212,255,0.25), 0 0 60px rgba(0,212,255,0.08);
  --glow-green:   0 0 20px rgba(0,255,157,0.25);
  --radius-sm:    6px;
  --radius-md:    12px;
  --radius-lg:    20px;
  --font-display: 'Syne', sans-serif;
  --font-mono:    'Space Mono', monospace;
  --font-body:    'DM Sans', sans-serif;
}

/* ── Reset & Base ── */
html, body, .stApp {
  background-color: var(--bg-base) !important;
  font-family: var(--font-body) !important;
  color: var(--text-primary) !important;
}

/* Animated grid background */
.stApp::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  z-index: 0;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: var(--bg-surface) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div {
  background: transparent !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }

/* ── Main content area ── */
.main .block-container {
  padding: 1rem 2rem 2rem !important;
  max-width: 1100px !important;
}

/* ── Typography ── */
h1, h2, h3 {
  font-family: var(--font-display) !important;
  letter-spacing: -0.02em;
}

/* ── Custom chat containers ── */
.finbot-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px 0 20px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 24px;
  position: relative;
}
.finbot-logo {
  width: 52px; height: 52px;
  background: linear-gradient(135deg, #00D4FF22, #00FF9D22);
  border: 1.5px solid var(--accent-cyan);
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  font-size: 24px;
  box-shadow: var(--glow-cyan);
  flex-shrink: 0;
}
.finbot-title {
  font-family: var(--font-display) !important;
  font-size: 1.8rem !important;
  font-weight: 800 !important;
  background: linear-gradient(90deg, #00D4FF, #00FF9D);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 !important;
  line-height: 1.1 !important;
}
.finbot-subtitle {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--text-muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.status-dot {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--accent-green);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-left: auto;
}
.status-dot::before {
  content: '';
  width: 7px; height: 7px;
  background: var(--accent-green);
  border-radius: 50%;
  box-shadow: var(--glow-green);
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.85); }
}

/* ── Chat messages ── */
.msg-wrap {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  animation: fadeUp 0.3s ease;
}
.msg-wrap.user { flex-direction: row-reverse; }
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
.msg-avatar {
  width: 34px; height: 34px;
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
  margin-top: 2px;
}
.msg-avatar.bot {
  background: linear-gradient(135deg, #00D4FF20, #00FF9D20);
  border: 1px solid var(--accent-cyan);
}
.msg-avatar.user {
  background: linear-gradient(135deg, #FF2D7820, #FFB80020);
  border: 1px solid var(--accent-pink);
}
.msg-bubble {
  max-width: 75%;
  padding: 14px 18px;
  border-radius: var(--radius-md);
  font-size: 0.92rem;
  line-height: 1.65;
}
.msg-bubble.bot {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-top-left-radius: 4px;
  color: var(--text-primary);
}
.msg-bubble.bot:hover {
  border-color: var(--border-bright);
  box-shadow: var(--glow-cyan);
}
.msg-bubble.user {
  background: linear-gradient(135deg, #0D2040, #0A1830);
  border: 1px solid rgba(0,212,255,0.2);
  border-top-right-radius: 4px;
  color: var(--accent-cyan);
  font-family: var(--font-body);
}
.msg-time {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  color: var(--text-dim);
  margin-top: 4px;
  text-align: right;
}

/* ── Source chips ── */
.source-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}
.source-chip {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  color: var(--accent-green);
  background: rgba(0,255,157,0.06);
  border: 1px solid rgba(0,255,157,0.2);
  border-radius: 4px;
  padding: 2px 8px;
  letter-spacing: 0.06em;
  white-space: nowrap;
}
.source-score {
  color: var(--text-muted);
  margin-left: 4px;
}

/* ── Welcome card ── */
.welcome-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 32px;
  text-align: center;
  margin: 30px auto;
  max-width: 560px;
}
.welcome-card .icon-ring {
  width: 72px; height: 72px;
  border: 2px solid var(--accent-cyan);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 30px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #00D4FF10, #00FF9D10);
  box-shadow: var(--glow-cyan);
}
.welcome-card h3 {
  font-family: var(--font-display) !important;
  font-size: 1.35rem !important;
  font-weight: 700 !important;
  color: var(--text-primary) !important;
  margin-bottom: 8px !important;
}
.welcome-card p {
  color: var(--text-muted);
  font-size: 0.88rem;
  line-height: 1.6;
  margin-bottom: 24px;
}
.quick-btns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.quick-btn {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  font-size: 0.78rem;
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
  font-family: var(--font-body);
}
.quick-btn:hover {
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
  background: rgba(0,212,255,0.05);
}
.quick-btn .emoji { margin-right: 6px; }

/* ── Typing indicator ── */
.typing-wrap {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.typing-bubble {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  border-top-left-radius: 4px;
  padding: 14px 20px;
  display: flex;
  align-items: center;
  gap: 5px;
}
.typing-dot {
  width: 6px; height: 6px;
  background: var(--accent-cyan);
  border-radius: 50%;
  animation: typingBounce 1.2s ease-in-out infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.15s; }
.typing-dot:nth-child(3) { animation-delay: 0.3s;  }
@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30%           { transform: translateY(-8px); opacity: 1; }
}

/* ── Chat input area ── */
.stChatInput > div {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-bright) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: var(--glow-cyan) !important;
}
.stChatInput textarea {
  background: transparent !important;
  color: var(--text-primary) !important;
  font-family: var(--font-body) !important;
  font-size: 0.92rem !important;
}
.stChatInput textarea::placeholder {
  color: var(--text-muted) !important;
}
.stChatInput button {
  background: var(--accent-cyan) !important;
  color: var(--bg-base) !important;
  border-radius: 8px !important;
}

/* ── Sidebar elements ── */
.sidebar-logo {
  text-align: center;
  padding: 20px 0 28px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
}
.sidebar-logo .hex {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 8px;
}
.sidebar-logo h2 {
  font-family: var(--font-display) !important;
  font-size: 1.1rem !important;
  font-weight: 700 !important;
  background: linear-gradient(90deg, #00D4FF, #00FF9D);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 !important;
}
.sidebar-logo small {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  color: var(--text-dim);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.stat-label {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.stat-value {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  color: var(--accent-cyan);
  font-weight: 700;
}

/* ── File uploader ── */
.stFileUploader > div {
  background: var(--bg-elevated) !important;
  border: 1px dashed var(--border-bright) !important;
  border-radius: var(--radius-md) !important;
}
.stFileUploader label {
  color: var(--text-muted) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.75rem !important;
}

/* ── Buttons ── */
.stButton > button {
  background: linear-gradient(135deg, #00D4FF15, #00FF9D15) !important;
  border: 1px solid var(--border-bright) !important;
  color: var(--accent-cyan) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.72rem !important;
  letter-spacing: 0.08em !important;
  border-radius: var(--radius-sm) !important;
  transition: all 0.2s !important;
}
.stButton > button:hover {
  background: rgba(0,212,255,0.15) !important;
  box-shadow: var(--glow-cyan) !important;
  border-color: var(--accent-cyan) !important;
}

/* ── Success/error messages ── */
.stSuccess {
  background: rgba(0,255,157,0.08) !important;
  border: 1px solid rgba(0,255,157,0.3) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--accent-green) !important;
}
.stError {
  background: rgba(255,45,120,0.08) !important;
  border: 1px solid rgba(255,45,120,0.3) !important;
  border-radius: var(--radius-sm) !important;
}

/* ── Section headers in sidebar ── */
.sidebar-section {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.15em;
  padding: 16px 0 8px;
  border-top: 1px solid var(--border);
  margin-top: 8px;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-cyan); }

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 16px 0 !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
  font-family: var(--font-mono) !important;
  font-size: 0.7rem !important;
  color: var(--text-muted) !important;
  letter-spacing: 0.08em !important;
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
}
.streamlit-expanderContent {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
}

/* ── Toast-style info ── */
.info-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 0.62rem;
  color: var(--text-muted);
  letter-spacing: 0.06em;
}

</style>
""", unsafe_allow_html=True)


# ── Session State Init ────────────────────────────────────────────────────────
def init_session():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8].upper()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "doc_count" not in st.session_state:
        st.session_state.doc_count = 0
    if "msg_count" not in st.session_state:
        st.session_state.msg_count = 0
    if "quick_input" not in st.session_state:
        st.session_state.quick_input = None

init_session()


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_health():
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=HEALTH_TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def send_message(user_msg: str):
    history_payload = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]
    payload = {
        "session_id": st.session_state.session_id,
        "message":    user_msg,
        "history":    history_payload,
    }
    try:
        r = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=CHAT_TIMEOUT)
        if r.status_code == 200:
            return r.json()
        else:
            return {"answer": f"⚠ API error {r.status_code}: {r.text}", "sources": []}
    except requests.exceptions.Timeout:
        return {
            "answer": (
                "The backend is taking longer than expected. "
                "If this is the first request after inactivity, Render may still be waking up. "
                "Please try again in a minute."
            ),
            "sources": [],
        }
    except requests.exceptions.ConnectionError:
        return {"answer": "⚠ Cannot reach backend. Is the API server running?", "sources": []}
    except Exception as e:
        return {"answer": f"⚠ Unexpected error: {e}", "sources": []}


def upload_doc(file):
    try:
        r = requests.post(
            f"{BACKEND_URL}/upload",
            files={"file": (file.name, file.getvalue(), file.type)},
            timeout=UPLOAD_TIMEOUT,
        )
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def clear_session_api():
    try:
        requests.delete(f"{BACKEND_URL}/session/{st.session_state.session_id}", timeout=HEALTH_TIMEOUT)
    except Exception:
        pass


def format_time():
    return time.strftime("%H:%M")


def render_message(msg: dict):
    role     = msg["role"]
    content  = msg["content"]
    sources  = msg.get("sources", [])
    ts       = msg.get("time", "")
    is_user  = role == "user"

    avatar_cls  = "user" if is_user else "bot"
    bubble_cls  = "user" if is_user else "bot"
    wrap_cls    = "user" if is_user else ""
    avatar_icon = "◈" if is_user else "⬡"

    source_html = ""
    if sources:
        chips = "".join(
            f'<span class="source-chip">◎ {s["source"]}'
            f'<span class="source-score">{s["score"]:.2f}</span></span>'
            for s in sources[:3]
        )
        source_html = f'<div class="source-row">{chips}</div>'

    time_html = f'<div class="msg-time">{ts}</div>' if ts else ""

    st.markdown(f"""
    <div class="msg-wrap {wrap_cls}">
      <div class="msg-avatar {avatar_cls}">{avatar_icon}</div>
      <div>
        <div class="msg-bubble {bubble_cls}">{content}{source_html}</div>
        {time_html}
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_typing():
    st.markdown("""
    <div class="typing-wrap">
      <div class="msg-avatar bot">⬡</div>
      <div class="typing-bubble">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
      <span class="hex">⬡</span>
      <h2>FinBot</h2>
      <small>AI Banking Assistant v1.0</small>
    </div>
    """, unsafe_allow_html=True)

    # Health status
    health = get_health()
    if health:
        st.session_state.doc_count = health.get("vector_db_docs", 0)
        status_color = "#00FF9D"
        status_text  = "ONLINE"
    else:
        status_color = "#FF2D78"
        status_text  = "OFFLINE"

    st.markdown(f"""
    <div class="stat-card">
      <span class="stat-label">System Status</span>
      <span style="font-family:var(--font-mono);font-size:0.72rem;color:{status_color};letter-spacing:0.08em;">{status_text}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Session ID</span>
      <span class="stat-value">{st.session_state.session_id}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Vector Chunks</span>
      <span class="stat-value">{st.session_state.doc_count:,}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Messages</span>
      <span class="stat-value">{len(st.session_state.messages)}</span>
    </div>
    """, unsafe_allow_html=True)

    if health:
        st.markdown(f"""
        <div class="stat-card">
          <span class="stat-label">LLM Model</span>
          <span style="font-family:var(--font-mono);font-size:0.68rem;color:var(--accent-gold);">{health.get('model','—')}</span>
        </div>
        """, unsafe_allow_html=True)

    # Upload
    st.markdown('<div class="sidebar-section">Document Ingestion</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload PDF or TXT",
        type=["pdf", "txt", "md"],
        label_visibility="collapsed",
    )
    if uploaded:
        with st.spinner("Ingesting document …"):
            result = upload_doc(uploaded)
        if result:
            st.success(f"✓ {result['chunks_added']} chunks ingested")
        else:
            st.error("Upload failed — check backend logs.")

    # Actions
    st.markdown('<div class="sidebar-section">Session Controls</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⟳ Refresh", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("⌫ Clear", use_container_width=True):
            st.session_state.messages = []
            clear_session_api()
            st.rerun()

    # Info
    st.markdown("""
    <div class="sidebar-section">Capabilities</div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:var(--font-mono);font-size:0.62rem;color:var(--text-muted);line-height:2.2;">
      ◈ &nbsp;Loan queries & rates<br>
      ◈ &nbsp;Credit card policies<br>
      ◈ &nbsp;Banking FAQs<br>
      ◈ &nbsp;Document Q&A<br>
      ◈ &nbsp;Context-aware chat<br>
      ◈ &nbsp;Source attribution
    </div>
    """, unsafe_allow_html=True)


# ── Main Chat Area ────────────────────────────────────────────────────────────
st.markdown("""
<div class="finbot-header">
  <div class="finbot-logo">⬡</div>
  <div>
    <div class="finbot-title">FinBot</div>
    <div class="finbot-subtitle">Retrieval-Augmented Banking Intelligence</div>
  </div>
  <div class="status-dot">RAG · LIVE</div>
</div>
""", unsafe_allow_html=True)

# ── Quick-action handler ───────────────────────────────────────────────────────
QUICK_QUESTIONS = [
    ("💳", "What are the credit card eligibility criteria?"),
    ("🏦", "How do I apply for a personal loan?"),
    ("📋", "What documents are required for a home loan?"),
    ("💰", "What are the current loan interest rates?"),
]

# ── Welcome screen ────────────────────────────────────────────────────────────
if not st.session_state.messages:
    quick_html = "".join(
        f'<div class="quick-btn"><span class="emoji">{icon}</span>{q}</div>'
        for icon, q in QUICK_QUESTIONS
    )
    st.markdown(f"""
    <div class="welcome-card">
      <div class="icon-ring">⬡</div>
      <h3>Welcome to FinBot</h3>
      <p>Your AI-powered banking assistant. I can answer questions about loans,
         credit cards, account policies, and more — all grounded in your bank's
         actual documents.</p>
      <div class="quick-btns">{quick_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # Invisible buttons to capture quick-question clicks via Streamlit
    cols = st.columns(2)
    for idx, (icon, q) in enumerate(QUICK_QUESTIONS):
        with cols[idx % 2]:
            if st.button(f"{icon} {q[:35]}…", key=f"quick_{idx}", use_container_width=True):
                st.session_state.quick_input = q
                st.rerun()

# ── Render history ─────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    render_message(msg)

# ── Process quick-input ────────────────────────────────────────────────────────
if st.session_state.quick_input:
    prompt = st.session_state.quick_input
    st.session_state.quick_input = None

    st.session_state.messages.append({
        "role": "user", "content": prompt, "time": format_time()
    })
    render_message(st.session_state.messages[-1])

    typing_placeholder = st.empty()
    with typing_placeholder:
        render_typing()

    response = send_message(prompt)
    typing_placeholder.empty()

    bot_msg = {
        "role":    "assistant",
        "content": response.get("answer", "No response."),
        "sources": response.get("sources", []),
        "time":    format_time(),
    }
    st.session_state.messages.append(bot_msg)
    render_message(bot_msg)
    st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about loans, credit cards, banking policies …"):
    st.session_state.messages.append({
        "role": "user", "content": prompt, "time": format_time()
    })
    render_message(st.session_state.messages[-1])

    typing_placeholder = st.empty()
    with typing_placeholder:
        render_typing()

    response = send_message(prompt)
    typing_placeholder.empty()

    bot_msg = {
        "role":    "assistant",
        "content": response.get("answer", "No response."),
        "sources": response.get("sources", []),
        "time":    format_time(),
    }
    st.session_state.messages.append(bot_msg)
    render_message(bot_msg)
    st.rerun()
