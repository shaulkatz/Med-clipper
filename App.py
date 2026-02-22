import streamlit as st
import json, urllib.request, re
import pandas as pd
from pypdf import PdfReader

st.set_page_config(page_title="Nelson Lecture Architect", page_icon="🧬", layout="wide")
st.title("🧬 Nelson AI: אדריכל ההרצאות המעמיק")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ חסר מפתח API ב-Secrets!")
    st.stop()

# ממשק משתמש
col_a, col_b = st.columns([1, 2])
with col_a:
    uploaded_files = st.file_uploader("העלה את חלקי הספר (PDF)", type="pdf", accept_multiple_files=True)
with col_b:
    topic = st.text_input("הזן נושא להרצאה מקיפה ומעמיקה:", placeholder="למשל: Comprehensive review of Kawasaki Disease")

def call_gemini(prompt):
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

if st.button("בנה מפת הרצאה מקיפה") and uploaded_files and topic:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 1. בניית "מפת הקשר" (Context Mapping)
    all_files_info = ""
    for idx, f in enumerate(uploaded_files):
        status_text.info(f"סורק ובודק הקשרים בקובץ: {f.name}...")
        reader = PdfReader(f)
        # דגימה רחבה יותר (התחלה, אמצע וסוף של כל קובץ)
        sample_pages = [0, 1, len(reader.pages)//2, len(reader.pages)-1]
        sample_text = ""
        for p_idx in sample_pages:
            try:
                sample_text += reader.pages[p_idx].extract_text()[:800]
            except: pass
        all_files_info += f"\n--- FILENAME: {f.name} (Total: {len(reader.pages)} pages) ---\nSample Content: {sample_text}\n"
        progress_bar.progress((idx + 1) / len(uploaded_files))

    # 2. הפרומפט המורכב למחקר עומק
    deep_research_prompt = f"""
    You are a Senior Pediatric Professor preparing a high-level, comprehensive lecture for medical residents.
    The topic is: '{topic}'.
    
    Based on the following files context from Nelson Textbook of Pediatrics:
    {all_files_info}
    
    YOUR MISSION:
    1. Analyze which chapters across ALL files are essential for a DEEP understanding of {topic} (include pathophysiology, clinical manifestation, and complications).
    2. Create a detailed syllabus for a 60-minute lecture.
    3. Map the EXACT files and page ranges for extraction.
    
    YOU MUST RETURN A MARKDOWN TABLE with these exact columns:
    | File Name | Start Page | End Page | Topic Covered | Depth Level |
    
    Followed by a brief explanation of why you chose these sections.
    """
    
    status_text.info("גמיני מבצע כעת מחקר עומק ובונה את הטבלה...")
    research_results = call_gemini(deep_research_prompt)
    
    # 3. תצוגת תוצאות
    st.markdown("---")
    st.header(f"📋 תוכנית מחקר להרצאה: {topic}")
    
    # הצגת הטבלה והניתוח
    st.markdown(research_results)
    
    status_text.success("המחקר הושלם בהצלחה!")
    st.balloons()
else:
    if not uploaded_files:
        st.info("אנא העלה את חמשת הקבצים כדי להתחיל במחקר.")
