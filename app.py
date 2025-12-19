import streamlit as st
import base64
import os
import re
import json
import fitz  # PyMuPDF
from dotenv import load_dotenv
from groq import Groq
import textwrap
import io

# --- CONFIGURATION ---
APP_TITLE = "CV.AUDIT"
st.set_page_config(layout="wide", page_title=APP_TITLE, page_icon="⚡", initial_sidebar_state="collapsed")

# --- API ---
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("GROQ_API_KEY") or os.getenv("GOOGLE_API_KEY") 
if not api_key: st.stop()
client = Groq(api_key=api_key)

# --- PDF GENERATOR ---
def create_pdf(data):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, height - 50, APP_TITLE)
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, "Automated AI Analysis Report")
        y = height - 120
        
        # Score Section
        score = data.get('score', 'N/A')
        c.setFont("Helvetica-Bold", 40)
        c.setFillColor(colors.black)
        c.drawString(50, y, f"{score}%")
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.purple)
        c.drawString(180, y + 10, f"VERDICT: {data.get('verdict', 'N/A')}")
        y -= 60
        
        def draw_section(title, items, color):
            nonlocal y
            if y < 100: c.showPage(); y = height - 50
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(colors.black)
            c.drawString(50, y, title)
            y -= 20
            c.setFont("Helvetica", 10)
            c.setFillColor(color)
            for item in items:
                if y < 50: c.showPage(); y = height - 50
                c.drawString(60, y, f"• {item}")
                y -= 15
            y -= 20

        match = data.get('match', []) or data.get('strengths', []) or []
        missing = data.get('missing', []) or data.get('weaknesses', []) or data.get('critical_missing', []) or []
        
        if match: draw_section("MATCHED / STRENGTHS", match, colors.green)
        if missing: draw_section("MISSING / GAPS", missing, colors.red)
        
        txt = data.get('analysis', '') or data.get('summary', '') or "No detail provided."
        
        if y < 200: c.showPage(); y = height - 50
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.black)
        c.drawString(50, y, "ANALYSIS NOTE")
        y -= 25
        
        c.setFont("Helvetica", 10)
        text_object = c.beginText(50, y)
        words = txt.split()
        line = ""
        for w in words:
            if c.stringWidth(line + w) < 500:
                line += w + " "
            else:
                text_object.textLine(line)
                line = w + " "
        text_object.textLine(line)
        c.drawText(text_object)
        
        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        return None

# --- CSS: NEO-BRUTALISM ---
NEO_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Archivo:wght@100;400;700;900&display=swap');

body {
    background-color: #ffffcc;
    background-image: radial-gradient(#000 1px, transparent 1px);
    background-size: 20px 20px;
    color: #000;
    font-family: 'Archivo', sans-serif;
}
.stApp { background: transparent; }
.neo-card { background: #fff; border: 3px solid #000; box-shadow: 6px 6px 0px #000; padding: 25px; margin-bottom: 20px; }
[data-testid="stFileUploader"] { padding: 0; border: none; }
section[data-testid="stFileUploadDropzone"] { background-color: #fff !important; border: 3px dashed #000 !important; border-radius: 0 !important; padding: 30px !important; }
section[data-testid="stFileUploadDropzone"] button { border: 2px solid #000 !important; background: #fff !important; color: #000 !important; font-weight: 900 !important; box-shadow: 3px 3px 0px #000 !important; }
[data-testid="stFileUploader"] div[data-testid="stFileUploaderFile"] { background-color: #fef9c3 !important; border: 2px solid #000 !important; border-radius: 0 !important; margin-top: 10px !important; padding: 10px !important; }
.hero-title { font-family: 'Archivo', sans-serif; font-weight: 900; font-size: 4rem; background: #fff; border: 4px solid #000; display: inline-block; padding: 10px 40px; box-shadow: 10px 10px 0px #ff00ff; margin-bottom: 30px; transform: rotate(-1deg); }
.stButton>button { background: #fff; border: 3px solid #000; color: #000; font-weight: 800; text-transform: uppercase; height: 60px; box-shadow: 5px 5px 0px #000; transition: all 0.1s; }
.stButton>button:hover { transform: translate(2px, 2px); box-shadow: 3px 3px 0px #000; background: #e0f2fe; }
button[kind="primary"] { background: #4ade80 !important; }
.res-box { border: 4px solid #000; background: #fff; padding: 40px; box-shadow: 15px 15px 0px #3b82f6; margin-top: 20px; max-width: 900px; margin: 20px auto; }
.score-header { display: flex; align-items: center; gap: 20px; margin-bottom: 30px; border-bottom: 3px solid #000; padding-bottom: 20px; }
.big-score { font-size: 5rem; font-weight: 900; line-height: 1; color: #000; text-shadow: 4px 4px 0px #4ade80; }
.verdict-badge { background: #a855f7; color: #fff; font-family: 'Space Mono', monospace; padding: 8px 15px; font-weight: 700; font-size: 1.2rem; border: 2px solid #000; box-shadow: 4px 4px 0px #000; transform: rotate(2deg); display: inline-block; }
.analysis-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px; }
.grid-col { background: #fafafa; border: 2px solid #000; padding: 15px; box-shadow: 4px 4px 0px #000; }
.grid-col h4 { border-bottom: 2px solid #000; padding-bottom: 10px; margin-top: 0; margin-bottom: 15px; font-family: 'Space Mono', monospace; text-align: center; font-weight: 900; }
.check-item, .miss-item, .rec-item { border: 2px solid #000; padding: 8px 12px; margin-bottom: 8px; font-weight: 700; display: flex; align-items: center; gap: 10px; font-size: 0.9rem; }
.check-item { background: #dcfce7; } .check-item:before { content: "✅"; }
.miss-item { background: #fee2e2; } .miss-item:before { content: "🚧"; }
.rec-item { background: #e0e7ff; } .rec-item:before { content: "📘"; }
.deep-dive { font-family: 'Space Mono', monospace; font-size: 0.95rem; line-height: 1.6; background: #e0f2fe; padding: 25px; border: 3px solid #000; box-shadow: 8px 8px 0px #000; }
footer {display: none;}
"""
st.markdown(f"<style>{NEO_CSS}</style>", unsafe_allow_html=True)

# --- BACKEND ---
def get_groq(messages, json_mode=True):
    try: 
        format_type = {"type": "json_object"} if json_mode else None
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, response_format=format_type).choices[0].message.content
    except: return "{}" if json_mode else "Error"

def get_text(file):
    text = ""
    try:
        # METHOD 1: PyMuPDF (Fast)
        file.seek(0)
        pdf_bytes = file.read()
        file.seek(0)
        
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            text += page.get_text()
            
        # METHOD 2: pdfplumber (Fallback for weird encodings)
        if len(text.strip()) < 5:
            import pdfplumber
            file.seek(0)
            with pdfplumber.open(file) as pdf:
                text = "".join([page.extract_text() or "" for page in pdf.pages])

        return text
    except Exception as e:
        # If both fail, return what we have (empty)
        # st.error(f"Error: {e}") 
        return text

# --- UI ---
st.markdown(f"<center><div class='hero-title'>{APP_TITLE}</div></center>", unsafe_allow_html=True)

c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("<div class='neo-card'><h3>JOB DESCRIPTION</h3>", unsafe_allow_html=True)
    jd = st.text_area("jd", height=150, label_visibility="collapsed", placeholder="PASTE TEXT HERE")
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='neo-card'><h3>CV PDF</h3>", unsafe_allow_html=True)
    pdf = st.file_uploader("pdf", type="pdf", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

b1, b2, b3, b4 = st.columns(4, gap="medium")
with b1: btn_scan = st.button("ANALYZE")
with b2: btn_gap = st.button("SKILLS")
with b3: btn_fit = st.button("FIT SCORE", type="primary")
with b4: btn_chat = st.button("INTERVIEW")

if 'res' not in st.session_state: st.session_state.res = None
if 'mode' not in st.session_state: st.session_state.mode = None
if 'chat' not in st.session_state: st.session_state.chat = []

def run(m):
    if not pdf: return
    
    txt = get_text(pdf)
    
    if not jd:
        st.error("⚠️ JOB DESCRIPTION MISSING")
        return
        
    st.session_state.mode = m
    
    # ... (Rest of logic)
    
    # SYSTEM PROMPT FOR CLARITY
    sys_msg = "You are a specialized CV Parser. You will be provided with a JD (Requirements) and a CANDIDATE (Resume). Never confuse the two."
    
    # 1. FIT SCORES
    if m == "fit":
        prompt = f"""
        Compare <CANDIDATE> against <JOB_REQUIREMENTS>.
        
        <JOB_REQUIREMENTS>
        {jd}
        </JOB_REQUIREMENTS>
        
        <CANDIDATE>
        {txt}
        </CANDIDATE>
        
        Task: Identify how well the CANDIDATE matches the JOB.
        JSON format: {{ "score": int, "verdict": "str", "match": ["str"], "missing": ["str"], "analysis": "str" }}
        """
        st.session_state.res = json.loads(get_groq([{"role":"system","content":sys_msg}, {"role":"user","content":prompt}]))
        
    # 2. SKILL GAPS
    elif m == "gap":
        prompt = f"""
        Skill Gap Analysis.
        What key skills are in <JOB_REQUIREMENTS> but MISSING in <CANDIDATE>?
        
        <JOB_REQUIREMENTS>
        {jd}
        </JOB_REQUIREMENTS>
        
        <CANDIDATE>
        {txt}
        </CANDIDATE>
        
        JSON format: {{ "critical_missing": ["str"], "improvement": ["str"], "recommendations": ["str"] }}
        """
        st.session_state.res = json.loads(get_groq([{"role":"system","content":sys_msg}, {"role":"user","content":prompt}]))

    # 3. PROFILE SCAN
    elif m == "scan":
        prompt = f"""
        Audit the Candidate's Resume Quality in relation to the JD.
        
        <JOB_REQUIREMENTS>
        {jd}
        </JOB_REQUIREMENTS>
        
        <CANDIDATE>
        {txt}
        </CANDIDATE>
        
        JSON format: {{ "summary": "str", "strengths": ["str"], "weaknesses": ["str"] }}
        Guidelines:
        - Strengths: What parts of the CANDIDATE resume align perfectly?
        - Weaknesses: Where does the CANDIDATE fail to meet the bar?
        - Summary: Hiring recommendation.
        """
        st.session_state.res = json.loads(get_groq([{"role":"system","content":sys_msg}, {"role":"user","content":prompt}]))

    elif m == "chat":
        if not st.session_state.chat:
            st.session_state.chat.append({"role":"assistant", "content":get_groq([{"role":"user","content":f"Interview me.\n{jd}"}], json_mode=False)})

if btn_scan: run("scan")
if btn_gap: run("gap")
if btn_fit: run("fit")
if btn_chat: run("chat")

# RESULTS
if st.session_state.mode and st.session_state.mode != "chat":
    data = st.session_state.res
    html = ""
    
    if st.session_state.mode == "fit":
        m_list = "".join([f"<div class='check-item'>{x}</div>" for x in data.get('match', [])])
        mi_list = "".join([f"<div class='miss-item'>{x}</div>" for x in data.get('missing', [])])
        html = textwrap.dedent(f"""
            <div class='score-header'>
                <div class='big-score'>{data.get('score', 0)}%</div>
                <div><div style='font-weight:700;'>VERDICT</div><div class='verdict-badge'>{data.get('verdict', 'N/A')}</div></div>
            </div>
            <div class='analysis-grid'>
                <div class='grid-col'><h4 style='background:#4ade80;'>MATCHED SKILLS</h4>{m_list}</div>
                <div class='grid-col'><h4 style='background:#f43f5e; color:#fff;'>MISSING SKILLS</h4>{mi_list}</div>
            </div>
            <div class='deep-dive'><h4>TECHNICAL ANALYSIS</h4>{data.get('analysis', '').replace(chr(10), '<br>')}</div>
        """).strip()
    
    elif st.session_state.mode == "scan":
        s_list = "".join([f"<div class='check-item'>{x}</div>" for x in data.get('strengths', [])])
        w_list = "".join([f"<div class='miss-item'>{x}</div>" for x in data.get('weaknesses', [])])
        html = textwrap.dedent(f"""
             <div class='score-header'>
                <div class='big-score' style='font-size:3rem; text-shadow:3px 3px 0 #000;'>JD COMPARISON</div>
            </div>
            <div class='deep-dive' style='margin-bottom:30px; background:#fff;'>{data.get('summary', '')}</div>
            <div class='analysis-grid'>
                <div class='grid-col'><h4 style='background:#4ade80;'>REQUIREMENTS MET</h4>{s_list}</div>
                <div class='grid-col'><h4 style='background:#f43f5e; color:#fff;'>REQUIREMENTS FAILED</h4>{w_list}</div>
            </div>
        """).strip()
        
    elif st.session_state.mode == "gap":
        crit = "".join([f"<div class='miss-item'>{x}</div>" for x in data.get('critical_missing', [])])
        imp = "".join([f"<div class='check-item' style='background:#fef08a;'>{x}</div>" for x in data.get('improvement', [])])
        rec = "".join([f"<div class='rec-item'>{x}</div>" for x in data.get('recommendations', [])])
        html = textwrap.dedent(f"""
            <div class='score-header'><div class='big-score' style='font-size:3rem;'>SKILL AUDIT</div></div>
            <div class='analysis-grid'>
                <div class='grid-col'><h4 style='background:#f43f5e; color:#fff;'>CRITICAL GAPS</h4>{crit}</div>
                <div class='grid-col'><h4 style='background:#fcd34d;'>PARTIAL MATCH</h4>{imp}</div>
            </div>
            <div class='grid-col' style='background:#fff;'><h4 style='background:#818cf8; color:#fff;'>PROJECTS TO BUILD</h4>{rec}</div>
        """).strip()

    st.markdown(f"<div class='res-box'>{html}</div>", unsafe_allow_html=True)
    
    pdf_buffer = create_pdf(data)
    if pdf_buffer:
        st.download_button("⬇️ DOWNLOAD PDF REPORT", pdf_buffer, file_name="cv_audit_report.pdf", mime="application/pdf")
    else:
        st.warning("PDF Generation Failed. Reportlab not installed properly?")

if st.session_state.mode == "chat":
    c_html = ""
    for m in st.session_state.chat:
            bg = "background:#00ffff;" if m['role']=="assistant" else "background:#ff9900;margin-left:auto;"
            c_html += f"<div style='border:3px solid #000; padding:15px; margin-bottom:10px; max-width:80%; box-shadow:4px 4px 0 #000; font-weight:700; {bg}'>{m['content']}</div>"
    st.markdown(f"<div class='res-box'><h3>LIVE SESSION</h3>{c_html}</div>", unsafe_allow_html=True)
    if inp := st.chat_input("..."):
        st.session_state.chat.append({"role":"user", "content":inp})
        ans = get_groq([{"role":"user","content":f"Interview me: {inp}\nContext:{jd}"}], json_mode=False)
        st.session_state.chat.append({"role":"assistant", "content":ans})
        st.rerun()