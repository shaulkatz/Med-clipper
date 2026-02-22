import streamlit as st
import requests
import json
import os
from pypdf import PdfReader

st.set_page_config(page_title="Nelson Chapter Expert", page_icon="📖", layout="wide")
st.title("📖 Nelson AI: ניתוח פרקים מלאים (מבוסס טקסט)")

# המיפוי המדויק שלך (כולל ה-IDs הנכונים)
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
        with open(path, 'wb') as f: f.write(r.content)
    return path

# פונקציה לחיפוש פרק וקריאת טקסט אמיתי
def find_chapter_content(query, part_data):
    path = download_file(part_data['id'], part_data['name'])
    reader = PdfReader(path)
    full_chapter_text = ""
    start_found = False
    
    # סריקת הקובץ למציאת תחילת הפרק
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        # מחפש את שם הנושא בצירוף המילה Chapter או בכותרת גדולה
        if query.lower() in text.lower():
            start_found = True
            # אם מצאנו, אנחנו לוקחים את 15 העמודים הבאים (כדי לכסות פרק שלם)
            for j in range(i, min(i + 15, len(reader.pages))):
                full_chapter_text += f"\n[Page {j + part_data['start']}]\n" + reader.pages[j].extract_text()
            break
            
    return full_chapter_text, (i + part_data['start'] if start_found else None)

def ask_gemini_safe(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # שימוש במודל 2.5 פלאש שעבד בתמונות שלך
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload)
        data = res.json()
        if 'candidates' in data:
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"⚠️ שגיאת API: {data.get('error', {}).get('message', 'לא התקבלה תשובה תקינה')}"
    except Exception as e:
        return f"❌ תקלה בתקשורת: {str(e)}"

# --- ממשק משתמש ---
topic = st.text_input("הזן שם פרק או נושא רפואי (באנגלית, למשל: Rheumatic Fever):")

if st.button("בצע ניתוח פרק מלא"):
    if topic:
        chapter_content = ""
        found_at = None
        
        with st.spinner("סורק את הספרייה לזיהוי הפרק המלא..."):
            for part in NELSON_MAP:
                content, page_num = find_chapter_content(topic, part)
                if content:
                    chapter_content = content
                    found_at = f"{part['name']}, עמוד {page_num}"
                    break # מצאנו את הפרק, אפשר לעצור
        
        if chapter_content:
            st.success(f"הפרק נמצא ב-{found_at}! מנתח כעת את כל התוכן...")
            
            final_prompt = f"""
            You are a pediatric expert. I have provided the actual text of a WHOLE CHAPTER from Nelson 22nd Ed.
            
            TOPIC: {topic}
            ACTUAL TEXT FROM BOOK:
            {chapter_content[:15000]} # מגבלה כדי לא לחרוג מה-Context
            
            TASK:
            1. Summarize the ENTIRE chapter in a structured medical way (Physiology, Clinical, Diagnosis, Treatment).
            2. Use ONLY the provided text.
            3. Provide a navigation table for this chapter:
               | Section | Printed Page (based on the text [Page X] markers) |
            
            Language: Hebrew (prose), English (medical terms).
            """
            
            answer = ask_gemini_safe(final_prompt)
            st.markdown("---")
            st.markdown(answer)
        else:
            st.error("לא הצלחתי למצוא פרק שתואם בדיוק לנושא הזה. נסה שם פרק מדויק יותר.")
    else:
        st.warning("אנא הזן נושא.")
