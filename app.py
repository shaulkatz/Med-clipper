import streamlit as st
import json, urllib.request, os, requests, time
from pypdf import PdfReader

# --- הגדרות דף ---
st.set_page_config(page_title="Nelson Full Expert", page_icon="🔬", layout="wide")

DRIVE_FILES = {
    "Nelson Part 1": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa",
    "Nelson Part 2": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6",
    "Nelson Part 3": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx",
    "Nelson Part 4": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt",
    "Nelson Part 5": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v",
}

def download_with_progress(url, local_path):
    if os.path.exists(local_path): return True
    try:
        response = requests.get(url, stream=True)
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk: f.write(chunk)
        return True
    except: return False

@st.cache_resource
def setup_library():
    lib = []
    for name, f_id in DRIVE_FILES.items():
        url = f'https://drive.google.com/uc?id={f_id}&export=download'
        path = f"{name.replace(' ', '_')}.pdf"
        if download_with_progress(url, path):
            lib.append({"name": name, "path": path})
    return lib

@st.cache_data
def get_calibration_data(_library_data):
    cal_map = ""
    for b in _library_data:
        try:
            reader = PdfReader(b["path"])
            sample = reader.pages[0].extract_text()[:300].replace('\n', ' ')
            cal_map += f"\nFILE: {b['name']} | Total Pages: {len(reader.pages)} | Sample: {sample}"
        except: continue
    return cal_map

def call_gemini(prompt):
    if "GOOGLE_API_KEY" not in st.secrets: return "Error: API Key missing"
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text']
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return "⚠️ **עומס יתר:** המכסה לדקה זו הסתיימה. אנא המתן כ-60 שניות ונסה שוב."
        return f"שגיאה {e.code}"
    except Exception as e:
        return f"שגיאה: {str(e)}"

# --- ממשק משתמש ---
st.title("🔬 Nelson AI: Comprehensive Researcher")
st.caption("מערכת מחקר מבוססת Nelson Textbook of Pediatrics, 22nd Edition")

library_data = setup_library()

with st.sidebar:
    st.header("ניהול מערכת")
    if st.button("נקה זיכרון מטמון"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.write("הספרייה טעונה במלואה.")

topic = st.text_input("הזן נושא למחקר מקיף (ללא הגבלת זמן):", placeholder="למשל: Tetralogy of Fallot")

if st.button("בצע מחקר טוטאלי"):
    if not topic:
        st.error("אנא הזן נושא לחיפוש.")
    else:
        with st.spinner("מבצע סריקה רוחבית של כל חמשת חלקי הספר..."):
            calibration_map = get_calibration_data(library_data)
            
            # פרומפט שדורש את כל החומר הרלוונטי
            expert_prompt = f"""
            You are a world-leading medical expert. I want a COMPREHENSIVE and TOTAL review of the topic: {topic}.
            Do not limit the output for a specific duration. Locate EVERY relevant chapter, sub-chapter, and paragraph in the Nelson Textbook of Pediatrics 22nd Edition.
            
            Include:
            - Pathophysiology and mechanisms.
            - Clinical manifestations and complications.
            - Diagnostic criteria and differential diagnosis.
            - Full treatment protocols and latest updates.
            
            **STRICT RULE:** Base everything 100% on the attached textbook content only. Do not hallucinate.
            
            CALIBRATION INFO:
            {calibration_map}
            
            Format your response in Hebrew prose with English medical terms.
            Provide a summary table: Chapter Name, Chapter Number, Printed Page Range, PDF Page Index.
            Conclude by asking if I want a clinical case study or exam questions (MCQs).
            """
            
            report = call_gemini(expert_prompt)
            st.markdown("---")
            st.markdown(report)
