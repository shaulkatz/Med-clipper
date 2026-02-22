import streamlit as st
import requests
import json
import os
import re
from pypdf import PdfReader

st.set_page_config(page_title="Nelson Auto-Expert", page_icon="🧬", layout="wide")
st.title("🧬 Nelson AI: סורק וממפה אוטומטי")

# ה-IDs שלך
RAW_FILES = {
    "Part A": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa",
    "Part B": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6",
    "Part C": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx",
    "Part D": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt",
    "Part E": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v",
}

def download_file(f_id, name):
    path = f"{name}.pdf"
    if not os.path.exists(path):
        url = f'https://drive.google.com/uc?id={f_id}&export=download'
        r = requests.get(url)
        with open(path, 'wb') as f:
            f.write(r.content)
    return path

# --- פונקציית הקסם: סריקה, זיהוי וסידור ---
@st.cache_resource
def get_sorted_library():
    library = []
    status_text = st.empty()
    
    for label, f_id in RAW_FILES.items():
        status_text.text(f"🔍 סורק את {label}...")
        path = download_file(f_id, label)
        reader = PdfReader(path)
        
        # מחפש מספר עמוד מודפס בעמוד הראשון (בדרך כלל למעלה או למטה)
        first_page_text = reader.pages[0].extract_text()
        found_numbers = re.findall(r'\b\d{1,4}\b', first_page_text)
        # לוקח את המספר שהכי סביר שהוא מספר עמוד
        detected_page = int(found_numbers[-1]) if found_numbers else 1
        
        library.append({
            "original_label": label,
            "path": path,
            "start_page": detected_page,
            "total_pages": len(reader.pages)
        })
    
    # מיון כרונולוגי לפי מספר העמוד שנמצא
    sorted_lib = sorted(library, key=lambda x: x['start_page'])
    
    # עדכון שמות ל-Part 1, Part 2 וכו'
    for i, item in enumerate(sorted_lib):
        item['final_name'] = f"Part {i+1}"
        
    status_text.empty()
    return sorted_lib

# --- פונקציית Gemini ---
def ask_nelson(topic, lib_context):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    You are a Senior Pediatric Researcher. I have a library of Nelson 22nd Ed divided into 5 PDFs.
    Here is the mapping of my files:
    {lib_context}
    
    TOPIC: {topic}
    
    TASK:
    1. Conduct a deep medical review of this topic.
    2. Provide a mapping table:
       - Chapter Name | Chapter Number
       - Printed Page: The actual number on the book page.
       - PDF Location: Which 'Part X' and what is the 'PDF Page Index' (Printed Page - File Start Page + 1).
    
    Language: Hebrew prose, English medical terms.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    res = requests.post(url, json=payload)
    return res.json()['candidates'][0]['content']['parts'][0]['text']

# --- ממשק משתמש ---
if 'library' not in st.session_state:
    if st.button("🚀 הפעל סריקה וסידור ספרייה (בצע פעם אחת)"):
        st.session_state['library'] = get_sorted_library()
        st.success("הספרייה סודרה כרונולוגית!")

if 'library' in st.session_state:
    st.sidebar.header("📚 סדר הספרים (כרונולוגי):")
    lib_summary = ""
    for item in st.session_state['library']:
        st.sidebar.write(f"**{item['final_name']}**: עמודים {item['start_page']} עד {item['start_page'] + item['total_pages']}")
        lib_summary += f"{item['final_name']} (File: {item['path']}) starts at page {item['start_page']}. "

    topic = st.text_input("הזן נושא למחקר (למשל: Bronchiolitis):")
    if st.button("בצע מחקר מעמיק"):
        with st.spinner("הפרופסור סורק את המידע..."):
            result = ask_nelson(topic, lib_summary)
            st.markdown("---")
            st.markdown(result)
