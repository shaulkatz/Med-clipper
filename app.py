import streamlit as st
import requests
import json
import os
from pypdf import PdfReader

# --- הגדרות דף ---
st.set_page_config(page_title="Nelson Real-Text Expert", page_icon="🔬", layout="wide")
st.title("🔬 Nelson AI: המומחה שבאמת קורא")

# המיפוי המדויק שלך
NELSON_MAP = [
    {"name": "Part 1", "id": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt", "start": -41, "end": 958},
    {"name": "Part 2", "id": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v", "start": 959, "end": 1958},
    {"name": "Part 3", "id": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa", "start": 1959, "end": 2960},
    {"name": "Part 4", "id": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6", "start": 2961, "end": 3960},
    {"name": "Part 5", "id": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx", "start": 3961, "end": 4472},
]

def download_file(f_id, name):
    path = f"{name}.pdf"
    if not os.path.exists(path):
        url = f'https://drive.google.com/uc?id={f_id}&export=download'
        r = requests.get(url)
        with open(path, 'wb') as f:
            f.write(r.content)
    return path

# פונקציה שסורקת את ה-PDF ומחפשת את התוכן האמיתי
def search_actual_text(topic, part_data):
    path = download_file(part_data['id'], part_data['name'])
    reader = PdfReader(path)
    relevant_chunks = []
    
    # סריקה של כל 5 עמודים כדי למצוא את תחילת הפרק/נושא (למניעת איטיות)
    for i in range(0, len(reader.pages), 1):
        text = reader.pages[i].extract_text()
        if topic.lower() in text.lower():
            printed_page = i + part_data['start']
            # שואב את העמוד שנמצא ועוד 2 עמודים אחריו כדי לקבל הקשר של פרק
            context_text = ""
            for j in range(i, min(i + 3, len(reader.pages))):
                context_text += reader.pages[j].extract_text()
            
            relevant_chunks.append({
                "part": part_data['name'],
                "printed_page": printed_page,
                "text": context_text
            })
            if len(relevant_chunks) >= 2: break # מצאנו מספיק הקשר
            
    return relevant_chunks

def ask_gemini_with_real_text(topic, found_context):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # תיקון שם המודל לגרסה יציבה
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    context_str = "\n\n".join([f"SOURCE: {c['part']}, Page {c['printed_page']}:\n{c['text']}" for c in found_context])
    
    prompt = f"""
    You are a pediatric expert. I have extracted the following ACTUAL text from the Nelson Textbook 22nd Edition.
    
    TOPIC: {topic}
    EXTRACTED TEXT:
    {context_str}
    
    TASK:
    1. Summarize the chapter/section based ONLY on the extracted text above.
    2. Do not invent page numbers. Use only the ones provided in the source.
    3. If the text is about a different topic, state that you couldn't find a direct match.
    
    Language: Hebrew, medical terms in English.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    res = requests.post(url, json=payload)
    return res.json()['candidates'][0]['content']['parts'][0]['text']

# --- ממשק משתמש ---
topic = st.text_input("הזן נושא למחקר (באנגלית, למשל: Kawasaki disease):")

if st.button("בצע סריקת טקסט וניתוח פרקים"):
    if topic:
        all_context = []
        with st.spinner("מחפש את הטקסט האמיתי בתוך קבצי ה-PDF..."):
            for part in NELSON_MAP:
                found = search_actual_text(topic, part)
                if found:
                    all_context.extend(found)
                    st.write(f"✅ נמצא תוכן רלוונטי ב-{part['name']}")
        
        if all_context:
            with st.spinner("ג'מיני מנתח את הטקסטים שנמצאו..."):
                answer = ask_gemini_with_real_text(topic, all_context)
                st.markdown("---")
                st.markdown(answer)
        else:
            st.error("לא נמצא טקסט תואם בתוך הספר. נסה להשתמש במושג באנגלית.")
    else:
        st.warning("אנא הזן נושא.")
