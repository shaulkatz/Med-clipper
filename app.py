import streamlit as st
import requests
import json
import os
from pypdf import PdfReader

st.set_page_config(page_title="Nelson Deep Indexer", page_icon="🔬", layout="wide")
st.title("🔬 Nelson AI: מיפוי עמודים ופרקים")

DRIVE_FILES = {
    "Part 1": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa",
    "Part 2": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6",
    "Part 3": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx",
    "Part 4": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt",
    "Part 5": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v",
}

# פונקציה להורדת קבצים (רק אם הם לא קיימים)
def download_file(f_id, name):
    path = f"{name}.pdf"
    if not os.path.exists(path):
        url = f'https://drive.google.com/uc?id={f_id}&export=download'
        r = requests.get(url)
        with open(path, 'wb') as f:
            f.write(r.content)
    return path

# פונקציה שקוראת רק את ההתחלה של כל קובץ (תוכן העניינים)
@st.cache_data
def extract_indices():
    full_index = ""
    for name, f_id in DRIVE_FILES.items():
        try:
            path = download_file(f_id, name)
            reader = PdfReader(path)
            # אנחנו קוראים רק את 15 העמודים הראשונים של כל חלק (שם נמצא האינדקס)
            text = ""
            for i in range(min(15, len(reader.pages))):
                text += reader.pages[i].extract_text()
            full_index += f"\n--- INDEX DATA FOR {name} ---\n{text}\n"
        except: continue
    return full_index

def ask_nelson_with_index(topic, index_data):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    model_name = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    prompt = f"""
    You are a medical researcher. I have provided you with index data from Nelson Textbook of Pediatrics 22nd Edition.
    INDEX DATA: {index_data}
    
    TOPIC: {topic}
    
    YOUR TASK:
    1. Map every relevant chapter for this topic.
    2. Provide a table with: Chapter Name, Chapter Number, Printed Page (from book), and PDF Page Index.
    3. Use the provided index data to be 100% accurate with page numbers.
    4. Response in Hebrew, medical terms in English.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    res = requests.post(url, json=payload)
    return res.json()['candidates'][0]['content']['parts'][0]['text']

# --- ממשק משתמש ---
if st.button("טען אינדקס מהספרים (בצע פעם אחת)"):
    with st.spinner("סורק את דפי האינדקס מחמשת חלקי הספר..."):
        st.session_state['nelson_index'] = extract_indices()
    st.success("האינדקס נטען בהצלחה!")

topic = st.text_input("הזן נושא למחקר (למשל: Rheumatic Fever):")

if st.button("בצע מיפוי עמודים מדויק"):
    if 'nelson_index' not in st.session_state:
        st.error("אנא לחץ קודם על 'טען אינדקס'")
    elif topic:
        with st.spinner("מצליב נתונים בין האינדקס לשאלה..."):
            answer = ask_nelson_with_index(topic, st.session_state['nelson_index'])
            st.markdown(answer)
