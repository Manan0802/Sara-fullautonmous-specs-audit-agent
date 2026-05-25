import streamlit as st
import json
import re
import os
from data_fetchers import fetch_ds0
from agent_langgraph import run_agent

# ── Page config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Spec Audit Agent",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg:        #fafaf9;
    --surface:   #ffffff;
    --border:    #e5e7eb;
    --border2:   #d1d5db;
    --accent:    #2563eb;
    --accent2:   #0891b2;
    --text:      #111827;
    --muted:     #6b7280;
    --light:     #f3f4f6;
    --success:   #16a34a;
    --warn:      #d97706;
    --error:     #dc2626;
    --mono:      'JetBrains Mono', monospace;
    --sans:      'Inter', sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--sans);
    background-color: var(--bg);
    color: var(--text);
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2.5rem 4rem 4rem; max-width: 1300px; }

/* Header */
.agent-header {
    display: flex; align-items: center; gap: 18px;
    padding: 32px 0 28px;
    border-bottom: 2px solid var(--border);
    margin-bottom: 36px;
}
.agent-logo {
    width: 52px; height: 52px;
    background: linear-gradient(135deg, #2563eb, #0891b2);
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; flex-shrink: 0;
}
.agent-title { font-size: 26px; font-weight: 700; color: var(--text); letter-spacing: -0.5px; }
.agent-subtitle { font-size: 14px; color: var(--muted); margin-top: 3px; }

/* Input card */
.input-card {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 14px;
    padding: 28px 32px;
    margin-bottom: 28px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

/* Input fields */
.stTextInput > div > div > input {
    background: var(--bg) !important;
    border: 1.5px solid var(--border2) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
}
.stTextInput label {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    letter-spacing: 0.1px !important;
}

/* Button */
.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: var(--sans) !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 12px 32px !important;
    width: 100% !important;
    transition: all 0.15s !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.25) !important;
}
.stButton > button:hover {
    background: #1d4ed8 !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.35) !important;
    transform: translateY(-1px) !important;
}

/* Status bar */
.status-bar {
    display: flex; align-items: center; gap: 12px;
    background: #f0fdf4;
    border: 1.5px solid #bbf7d0;
    border-radius: 10px;
    padding: 14px 20px;
    margin-bottom: 28px;
    font-size: 14px; color: #15803d;
}
.status-dot {
    width: 9px; height: 9px; border-radius: 50%;
    background: var(--success);
    flex-shrink: 0;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid var(--border) !important;
    gap: 4px !important; padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    font-family: var(--sans) !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 14px 24px !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 28px 0 0 !important; }

/* Thinking blocks */
.thinking-block {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 10px;
    padding: 22px 28px;
    margin-bottom: 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.thinking-turn-header {
    font-family: var(--mono);
    font-size: 12px; color: var(--accent);
    font-weight: 500; letter-spacing: 0.5px;
    margin-bottom: 14px; text-transform: uppercase;
}
.thinking-section {
    font-size: 12px; color: var(--muted);
    font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.6px; margin-bottom: 8px;
}
.thinking-text {
    font-size: 15px; line-height: 1.75;
    color: #374151; white-space: pre-wrap;
}
.response-text {
    font-size: 15px; line-height: 1.75;
    color: var(--muted); white-space: pre-wrap;
    margin-top: 14px; padding-top: 14px;
    border-top: 1px solid var(--border);
}

/* Metrics */
.metrics-row {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 14px; margin-bottom: 28px;
}
.metric-card {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 12px; padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.metric-value {
    font-size: 32px; font-weight: 700;
    font-family: var(--mono); color: var(--text);
}
.metric-label {
    font-size: 12px; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.6px; margin-top: 4px;
}

/* Tier section */
.tier-section {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 12px; padding: 22px 26px;
    margin-bottom: 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.tier-header {
    display: flex; align-items: center; gap: 10px; margin-bottom: 18px;
}
.tier-badge {
    font-size: 11px; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase;
    padding: 4px 12px; border-radius: 6px;
}
.tier-primary   { background: #dbeafe; color: #1d4ed8; border: 1.5px solid #bfdbfe; }
.tier-secondary { background: #cffafe; color: #0e7490; border: 1.5px solid #a5f3fc; }
.tier-tertiary  { background: #f3f4f6; color: #374151; border: 1.5px solid #d1d5db; }
.tier-count { font-size: 13px; color: var(--muted); margin-left: auto; font-family: var(--mono); }

/* Spec card */
.spec-card {
    background: var(--bg);
    border: 1.5px solid var(--border);
    border-radius: 10px; padding: 16px 20px;
    margin-bottom: 10px;
}
.spec-name {
    font-weight: 600; font-size: 15px;
    color: var(--text); margin-bottom: 8px;
    display: flex; align-items: center; gap: 10px;
}
.spec-type {
    font-family: var(--mono); font-size: 11px;
    color: var(--muted); background: #f3f4f6;
    border: 1px solid var(--border);
    padding: 2px 8px; border-radius: 4px;
    font-weight: 400;
}
.spec-options { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.option-chip {
    font-size: 12px; font-family: var(--mono);
    background: #f9fafb; border: 1px solid var(--border);
    color: #374151; padding: 3px 10px; border-radius: 5px;
}
.text-type-badge {
    font-size: 12px; font-family: var(--mono);
    color: var(--warn); background: #fffbeb;
    border: 1px solid #fde68a; padding: 3px 10px; border-radius: 5px;
}

/* Log sections */
.log-section {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 12px; padding: 24px 28px;
    margin-bottom: 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.log-section-title {
    font-size: 13px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.8px;
    color: var(--accent2); margin-bottom: 16px;
}
.log-content {
    font-size: 14px; line-height: 1.8;
    color: #374151; white-space: pre-wrap;
}
</style>
""", unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:48px 0 36px;">
    <div style="display:flex;align-items:flex-start;gap:20px;margin-bottom:32px;">
        <div style="width:56px;height:56px;background:linear-gradient(135deg,#2563eb,#0891b2);
            border-radius:16px;display:flex;align-items:center;justify-content:center;
            font-size:26px;flex-shrink:0;box-shadow:0 4px 14px rgba(37,99,235,0.3);">⚙️</div>
        <div>
            <div style="font-size:30px;font-weight:700;color:#111827;letter-spacing:-0.6px;
                line-height:1.2;">Spec Audit Agent</div>
            <div style="font-size:15px;color:#6b7280;margin-top:5px;">
                Intelligent category spec correction for Indian B2B Marketplace
            </div>
        </div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:40px;">
        <div style="background:#eff6ff;border:1.5px solid #bfdbfe;border-radius:12px;padding:20px 24px;">
            <div style="font-size:22px;font-weight:700;color:#1d4ed8;font-family:'JetBrains Mono',monospace;">5</div>
            <div style="font-size:13px;color:#3b82f6;margin-top:3px;font-weight:500;">Data Sources Analysed</div>
        </div>
        <div style="background:#f0fdf4;border:1.5px solid #bbf7d0;border-radius:12px;padding:20px 24px;">
            <div style="font-size:22px;font-weight:700;color:#16a34a;font-family:'JetBrains Mono',monospace;">8</div>
            <div style="font-size:13px;color:#22c55e;margin-top:3px;font-weight:500;">Reasoning Skills Available</div>
        </div>
        <div style="background:#fefce8;border:1.5px solid #fde68a;border-radius:12px;padding:20px 24px;">
            <div style="font-size:22px;font-weight:700;color:#d97706;font-family:'JetBrains Mono',monospace;">AI</div>
            <div style="font-size:13px;color:#f59e0b;margin-top:3px;font-weight:500;">Gemini 2.5 Pro Powered</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Parse output.md ────────────────────────────────────────────────────
def parse_output_file(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()
    return parse_output(raw)


def parse_output(raw: str) -> dict:
    turns = []
    # Split by TURN headers
    parts = re.split(r"\n={50}\nTURN \d+\n={50}\n", raw)
    headers = re.findall(r"TURN \d+", raw)

    for i, block in enumerate(parts[1:], 0):
        thinking = ""
        response = ""
        t = re.search(r"--- RAW THINKING ---\n(.*?)\n--- END THINKING ---", block, re.DOTALL)
        if t:
            thinking = t.group(1).strip()
        r = re.search(r"--- RESPONSE ---\n(.*?)$", block, re.DOTALL)
        if r:
            resp_text = r.group(1).strip()
            # Cut off everything from the corrected specs JSON onwards
            cutoff = re.search(
                r'(?:###\s*[456]\.|```json|\*\*Corrected Specs JSON\*\*)',
                resp_text
            )
            response = resp_text[:cutoff.start()].strip() if cutoff else resp_text

        turns.append({
            "header": headers[i] if i < len(headers) else f"TURN {i+1}",
            "thinking": thinking,
            "response": response,
        })

    # Parse corrected specs JSON — get the LAST occurrence (most complete)
    specs = None
    all_matches = list(re.finditer(
        r'```json\s*(\{[^`]*?"generated_by"[^`]*?\})\s*```', raw, re.DOTALL
    ))
    if all_matches:
        try:
            specs = json.loads(all_matches[-1].group(1))
        except:
            try:
                text = re.sub(r',\s*([}\]])', r'\1', all_matches[-1].group(1))
                specs = json.loads(text)
            except:
                specs = None

    # Parse additional log sections
    sections = {}
    section_map = {
        "investigation_plan": r"###?\s*1\.\s*Investigation Plan(.*?)(?=###?\s*\d+\.|$)",
        "investigation_log":  r"###?\s*2\.\s*Investigation Log(.*?)(?=###?\s*\d+\.|$)",
        "skipped_gaps":       r"###?\s*3\.\s*Skipped Gaps(.*?)(?=###?\s*\d+\.|$)",
        "action_table":       r"###?\s*5\.\s*Action Summary Table(.*?)(?=###?\s*\d+\.|$)",
        "self_reflection":    r"###?\s*(?:6|7)\.\s*Self.Reflection(.*?)(?=###?\s*\d+\.|$)",
        "option_changes":     r"###?\s*6\.\s*Option Changes(.*?)(?=###?\s*\d+\.|$)",
    }
    for key, pattern in section_map.items():
        found = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
        sections[key] = found.group(1).strip() if found else ""

    return {"turns": turns, "specs": specs, "sections": sections, "raw": raw}


def render_specs(specs: dict):
    if not specs:
        st.warning("No corrected specs JSON found in output.")
        return

    st.markdown("#### Raw JSON")
    st.code(json.dumps(specs, indent=2), language="json")


def render_thinking(turns: list):
    if not turns:
        st.info("No thinking blocks found.")
        return
    for t in turns:
        with st.expander(f"⬡ {t['header']}", expanded=True):
            if t["thinking"]:
                st.markdown("**Thinking**")
                st.markdown(f"""<div style="
                    background:#f8fafc;border-left:3px solid #2563eb;
                    padding:16px 20px;border-radius:6px;
                    font-size:14px;line-height:1.75;color:#374151;
                    white-space:pre-wrap;font-family:Inter,sans-serif;
                    margin-bottom:12px;">{t["thinking"]}</div>""",
                unsafe_allow_html=True)
            if t["response"]:
                st.markdown("**Response**")
                st.markdown(f"""<div style="
                    background:#f0f9ff;border-left:3px solid #0891b2;
                    padding:16px 20px;border-radius:6px;
                    font-size:14px;line-height:1.75;color:#374151;
                    white-space:pre-wrap;font-family:Inter,sans-serif;">{t["response"]}</div>""",
                unsafe_allow_html=True)


def render_logs(sections: dict):
    order = [
        ("investigation_plan", "📋 Investigation Plan"),
        ("investigation_log",  "🔍 Investigation Log"),
        ("skipped_gaps",       "⏭ Skipped Gaps"),
        ("action_table",       "📊 Action Summary Table"),
        ("option_changes",     "🔧 Option Changes"),
        ("self_reflection",    "💭 Self-Reflection"),
    ]
    for key, label in order:
        content = sections.get(key, "")
        if not content:
            continue
        with st.expander(label, expanded=True):
            st.markdown(content)


# ── Input panel ────────────────────────────────────────────────────────
st.markdown('<div class="input-card">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([2, 3, 1])
with col1:
    category_id = st.text_input("Category ID", placeholder="e.g. 179097", label_visibility="visible")
with col2:
    category_name = st.text_input("Category Name", placeholder="e.g. TSC Barcode & Label Printers", label_visibility="visible")
with col3:
    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
    run_btn = st.button("Run Audit →", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# ── Run agent ──────────────────────────────────────────────────────────
if run_btn:
    if not category_id or not category_name:
        st.error("Please enter both Category ID and Category Name.")
    else:
        with st.spinner("Audit in progress — this may take a few minutes..."):
            try:
                mcat_id = int(category_id)
                ds0 = fetch_ds0(mcat_id)
                run_agent(mcat_id, category_name, ds0)

                output_path = os.path.join("output", f"output_{mcat_id}.md")
                if os.path.exists(output_path):
                    parsed = parse_output_file(output_path)
                    st.session_state["parsed"]   = parsed
                    st.session_state["mcat_id"]  = mcat_id
                    st.session_state["cat_name"] = category_name
                    st.session_state["done"]     = True
                    st.success("Audit complete!")
                else:
                    st.error(f"Output file not found: {output_path}")

            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())


# ── Results ────────────────────────────────────────────────────────────
if st.session_state.get("done"):
    parsed   = st.session_state["parsed"]
    mcat_id  = st.session_state["mcat_id"]
    cat_name = st.session_state["cat_name"]

    st.markdown(f"""
    <div class="status-bar">
        <div class="status-dot"></div>
        <span>Audit complete — <strong>{cat_name}</strong> &nbsp;·&nbsp; mcat_id: <code style="font-family:var(--mono);font-size:12px;background:var(--bg);padding:1px 6px;border-radius:3px;">{mcat_id}</code></span>
        <span style="margin-left:auto;color:var(--muted);font-size:12px">{len(parsed["turns"])} turns</span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["💭  Thinking", "✅  Corrected Specs", "📋  Additional Logs"])

    with tab1:
        render_thinking(parsed["turns"])

    with tab2:
        render_specs(parsed["specs"])

    with tab3:
        render_logs(parsed["sections"])