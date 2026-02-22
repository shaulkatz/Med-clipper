import streamlit as st
import requests
import json
import os
import re
from pypdf import PdfReader

st.set_page_config(page_title="Nelson Smart Mapper", page_icon="🔬", layout="wide")
st.title("🔬 Nelson AI: מיפוי עמודים חכם (כיול אוטומטי)")

DRIVE_FILES = {
    "Part 1": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa",
    "Part 2": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6",
    "Part 3": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx",
    "Part 4": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt",
    "Part 5": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v",
}

def download_file(f_id, name):
    path = f"{name}.pdf"
    if not os.path.exists(path):
        url = f'https://drive.google.com/uc?id={f_id}&export=download'
        r = requests.get(url)
        with open(path, 'wb') as f:
            f.write(r.content)
    return path

# פונקציה שמזהה איזה עמוד מודפס מופיע בתחילת כל קובץ
@st.cache_data
def calibrate_offsets():
    offsets = {}
    for name, f_id in DRIVE_FILES.items():
        try:
            path = download_file(f_id, name)
            reader = PdfReader(path)
            # קורא את הטקסט מהעמוד הראשון כדי למצוא את מספר העמוד המודפס
            first_page_text = reader.pages[0].extract_text()
            # מחפש מספרים בני 1-4 ספרות (מספרי עמודים טיפוסיים)
            found_numbers = re.findall(r'\b\d{1,4}\b', first_page_text)
            # לוקח את המספר האחרון שנמצא (בדרך כלל מספר העמוד בפינה)
            start_page = int(found_numbers[-1]) if found_numbers else 1
            offsets[name] = {
                "start_printed": start_page,
                "total_pages": len(reader.pages),
                "pdf_name": name
            }
        except:
            offsets[name] = {"start_printed": 1, "total_pages": 0}
    return offsets

def run_research_with_calibration(topic, offsets):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # בניית מפת הכיול עבור גמיני
    offset_context = "\n".join([f"{k}: Starts at printed page {v['start_printed']}, has {v['total_pages']} pages." for k,v in offsets.items()])
    
    prompt = f"""
    You are a pediatric expert researcher. 
    The Nelson Textbook of Pediatrics 22nd Ed is split into 5 PDF files. Here is the mapping:
    {offset_context}
    
    TOPIC: {topic}
    
    TASK:
    1. Provide a comprehensive medical review.
    2. List all relevant chapters.
    3. FOR THE TABLE:
       - Chapter Name | Chapter Number
       - Printed Page: The page number written on the book's leaf.
       - PDF File: Which Part (1-5) it is in.
       - PDF Page Index: Calculate this! (Printed Page - File Start Page + 1).
    
    Answer in Hebrew, medical terms in English. Be precise.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    res = requests.post(url, json=payload)
    return res.json()['candidates'][0]['content']['parts'][0]['text']

# --- ממשק משתמש ---
if st.button("בצע כיול קבצים (סריקת עמודי פתיחה)"):
    with st.spinner("מזהה את נקודות החיתוך של חמשת החלקים..."):
        st.session_state['offsets'] = calibrate_offsets()
        st.success("הכיול הושלם!")
        for name, data in st.session_state['offsets'].items():
            st.write(f"📍 **{name}** מתחיל בעמוד מודפס: {data['start_printed']}")

st.markdown("---")

topic = st.text_input("הזן נושא למחקר מקיף:")

if st.button("בצע מחקר ומיפוי"):
    if 'offsets' not in st.session_state:
        st.error("אנא בצע 'כיול קבצים' קודם.")
    elif topic:
        with st.spinner("הפרופסור סורק ומחשב עמודים..."):
            answer = run_research_with_calibration(topic, st.session_state['offsets'])
            st.markdown(answer)
