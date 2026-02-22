import streamlit as st
import json, urllib.request, os, gdown, re
import pandas as pd
from pypdf import PdfReader

# --- הגדרות דף ---
st.set_page_config(page_title="Nelson Senior Expert", page_icon="🔬", layout="wide")

# --- הזן כאן את ה-IDs שחילצת מהאייפד ---
DRIVE_FILES = {
    "Nelson Part 1": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa",
    "Nelson Part 2": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6",
    "Nelson Part 3": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx",
    "Nelson Part 4": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt",
    "Nelson Part 5": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v",
}

# --- פונקציות תשתית ---

@st.cache_resource
def setup_library():
    """מוריד את הספרים מהדרייב לשרת פעם אחת בלבד"""
    local_files = []
    for name, f_id in DRIVE_FILES.items():
        url = f'https://drive.google.com/uc?id={f_id}'
        path = f"{name.replace(' ', '_')}.pdf"
        if not os.path.exists(path):
            gdown.download(url, path, quiet=True)
        local_files.append({"name": name, "path": path})
    return local_files

def call_gemini(prompt):
    """פנייה ל-API של גוגל"""
    if "GOOGLE_API_KEY" not in st.secrets:
        return "Error: Missing API Key"
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
st.markdown("### מערכת מחקר ותכנון הרצאות מבוססת Nelson Textbook (22nd Ed)")

with st.sidebar:
    st.header("⏱️ הגדרות זמן")
    duration = st.text_input("מה משך הזמן המוקצב להרצאה?", placeholder="למשל: 30 minutes")
    st.markdown("---")
    if st.button("רענן ספרייה"):
        st.cache_resource.clear()
        st.rerun()

topic = st.text_input("הזן נושא למחקר מקיף ומעמיק:")

# --- לוגיקת המחקר ---
if st.button("בצע מחקר עומק ואימות מקורות"):
    # 1. בדיקת ה-Guardrail (זמן ההרצאה)
    if not duration:
        st.warning("⚠️ מה משך הזמן המוקצב להרצאה?")
    elif not topic:
        st.error("אנא הזן נושא למחקר.")
    else:
        with st.spinner("טוען את הספרייה ומכייל עמודים..."):
            library = setup_library()
            
            # 2. בניית Calibration Map (עוגנים לדיוק עמודים)
            calibration_data = ""
            for book in library:
                reader = PdfReader(book["path"])
                # דגימת עמוד ראשון ואמצע למניעת סטיות
                mid_page = len(reader.pages) // 2
                sample_1 = reader.pages[0].extract_text()[:800]
                sample_2 = reader.pages[mid_page].extract_text()[:800]
                calibration_data += f"\nFILE: {book['name']}\n[PDF Page 1]: {sample_1}\n[PDF Page {mid_page}]: {sample_2}\n"

        # 3. בניית הפרומפט המומחה שלך
        full_expert_prompt = f"""
You are a world-renowned medical expert and researcher, with a deep clinical and academic understanding of all fields of medicine, anatomy, and physiology. I have attached files containing a professional medical textbook (Nelson Textbook of Pediatrics, 22nd Edition).

The topic I am focusing on is: {topic}.
The lecture duration is: {duration}.

Your task is to conduct a comprehensive, broad, and in-depth review of the attached book context, locating all chapters, sub-chapters, and paragraphs relevant to this topic. Use your medical knowledge to identify chapters dealing with indirect contexts, mechanisms of action, underlying diseases, differential diagnoses, systemic effects, or any other relevant clinical context.

**CRITICAL AND STRICT RESTRICTION:** You are strictly forbidden from hallucinating or inventing any information, contexts, chapters, or page numbers. You must base your response entirely and exclusively (100%) on the exact content found within the attached files. Use the following context samples for calibration:
{calibration_data}

For each relevant chapter or section:
1. Explain professionally why it is related to the topic (based only on the text in the files).
2. Detail which aspects of the topic (pathology, treatment, etc.) are covered.

After the review, summarize in an organized table:
- Chapter Name
- Chapter Number
- Printed Page Range (from the actual page)
- File Index Page Range (PDF page number)

Language: Output in HEBREW, but all medical terms, diagnoses, and drug names MUST be in ENGLISH.
Conclude by asking: "האם תרצה שאבנה עבורך תיאור מקרה קליני (Clinical Case Study) או שאלות אמריקאיות (MCQs) לבחינת השליטה בחומר?"
"""

        with st.spinner("הפרופסור מנתח את הספרייה... זה עשוי לקחת רגע..."):
            response = call_gemini(full_expert_prompt)
            st.markdown("---")
            st.markdown(response)
            st.success("המחקר הושלם בהצלחה!")
