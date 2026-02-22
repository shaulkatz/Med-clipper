import streamlit as st
import json, urllib.request, os, requests, re
from pypdf import PdfReader

# --- הגדרות דף ---
st.set_page_config(page_title="Nelson Senior Expert", page_icon="🔬", layout="wide")

# ה-IDs שסיפקת
DRIVE_FILES = {
    "Nelson Part 1": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa",
    "Nelson Part 2": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6",
    "Nelson Part 3": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx",
    "Nelson Part 4": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt",
    "Nelson Part 5": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v",
}

# --- פונקציית הורדה חכמה ---
def download_with_progress(url, local_path, display_name):
    if os.path.exists(local_path):
        return True
    status_container = st.empty()
    progress_bar = st.progress(0)
    try:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0)) or 150*1024*1024
        downloaded_size = 0
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    progress = min(downloaded_size / total_size, 1.0)
                    progress_bar.progress(progress)
                    status_container.text(f"📥 מוריד: {display_name} ({downloaded_size // (1024*1024)}MB)")
        status_container.empty()
        progress_bar.empty()
        return True
    except:
        return False

@st.cache_resource
def setup_library():
    lib = []
    for name, f_id in DRIVE_FILES.items():
        url = f'https://drive.google.com/uc?id={f_id}&export=download'
        path = f"{name.replace(' ', '_')}.pdf"
        if download_with_progress(url, path, name):
            lib.append({"name": name, "path": path})
    return lib

# --- פונקציית Gemini ---
def call_gemini(prompt):
    if "GOOGLE_API_KEY" not in st.secrets:
        return "שגיאה: מפתח API חסר ב-Secrets"
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Error: {str(e)}"

# --- ממשק משתמש ---
st.title("🔬 Nelson AI: Senior Medical Expert Researcher")

library_data = setup_library()
if library_data:
    st.success(f"✅ הספרייה מוכנה! {len(library_data)} קבצים זוהו.")

with st.sidebar:
    st.header("⏱️ הגדרות")
    duration = st.text_input("זמן הרצאה מוקצב:", placeholder="למשל: 40 minutes")
    if st.button("רענן ספרייה"):
        st.cache_resource.clear()
        st.rerun()

topic = st.text_input("הזן נושא למחקר (למשל: Childhood Asthma Management):")

if st.button("בצע מחקר מעמיק"):
    if not duration:
        st.warning("⚠️ אנא הזן את משך הזמן המוקצב להרצאה.")
    elif not topic:
        st.error("אנא הזן נושא.")
    else:
        with st.spinner("הפרופסור מנתח את כל חמשת חלקי הספר..."):
            # יצירת מפת עמודים לכיול (Calibration)
            calibration_map = ""
            for b in library_data:
                try:
                    reader = PdfReader(b["path"])
                    calibration_map += f"\nFILE: {b['name']} | Pages: {len(reader.pages)} | Sample: {reader.pages[0].extract_text()[:500]}"
                except: continue

            # הפרומפט המקצועי שלך
            expert_prompt = f"""
You are a world-renowned medical expert and researcher, with a deep clinical and academic understanding of all fields of medicine, anatomy, and physiology. 
I have attached files containing Nelson Textbook of Pediatrics, 22nd Edition.

The topic I am focusing on is: {topic}.
Lecture duration: {duration}.

Your task is to conduct a comprehensive, broad, and in-depth review of the book content, locating all chapters, sub-chapters, and paragraphs relevant to this topic. Use your medical knowledge to identify indirect contexts, mechanisms of action, differential diagnoses, or systemic effects.

**CRITICAL AND STRICT RESTRICTION:** You are strictly forbidden from hallucinating. Base your response 100% on the attached files.

CALIBRATION DATA:
{calibration_map}

For each relevant chapter or section:
1. Explain professionally why it is related (based ONLY on the files).
2. Detail which aspects (pathology, treatment, diagnosis) are covered.

Summary Table:
- Chapter Name
- Chapter Number
- Printed Page Range (from actual page)
- File Index Page Range (PDF page number)

Output in HEBREW, but maintain professional English medical terms.
Conclude by asking if the user wants a Case Study or MCQs.
"""
            report = call_gemini(expert_prompt)
            st.markdown("---")
            st.markdown(report)
