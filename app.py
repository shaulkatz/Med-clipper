import streamlit as st
import requests
import os
from pypdf import PdfReader

st.set_page_config(page_title="Nelson Real-Reader", page_icon="🧬", layout="wide")
st.title("🧬 Nelson AI: קריאה ישירה מהספר (ללא ניחושים)")

# המפה המדויקת שלך
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

def call_gemini(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    res = requests.post(url, json=payload)
    return res.json()['candidates'][0]['content']['parts'][0]['text']

# --- ממשק משתמש ---
topic = st.text_input("הזן נושא רפואי (למשל: Heart Failure treatment):")

if st.button("בצע מחקר מבוסס טקסט אמיתי"):
    if topic:
        # שלב 1: זיהוי עמודים (מבוסס ידע AI)
        with st.spinner("מזהה את המיקום המשוער בספר..."):
            plan_prompt = f"Identify the exact printed page numbers in Nelson 22nd Ed for: {topic}. Return ONLY: 'Part X, Pages START-END'."
            location_plan = call_gemini(plan_prompt)
            st.write(f"🔍 AI מכוון ל: {location_plan}")

        # שלב 2: חילוץ טקסט אמיתי מה-PDF
        try:
            # פיענוח התוכנית (למשל "Part 2, Pages 1000-1010")
            part_num = int(location_plan.split("Part ")[1].split(",")[0]) - 1
            pages_str = location_plan.split("Pages ")[1]
            start_p = int(pages_str.split("-")[0])
            end_p = int(pages_str.split("-")[1])
            
            part_data = NELSON_MAP[part_num]
            path = download_file(part_data['id'], part_data['name'])
            
            with st.spinner(f"קורא פיזית את עמודים {start_p}-{end_p} מתוך {part_data['name']}..."):
                reader = PdfReader(path)
                extracted_text = ""
                # המרת עמוד מודפס לאינדקס PDF
                pdf_start = start_p - part_data['start']
                pdf_end = end_p - part_data['start']
                
                for i in range(max(0, pdf_start), min(pdf_end + 1, len(reader.pages))):
                    extracted_text += f"\n--- Page {i + part_data['start']} ---\n"
                    extracted_text += reader.pages[i].extract_text()

            # שלב 3: סיכום מבוסס "עובדות בלבד"
            if extracted_text:
                with st.spinner("גמיני מנתח את הטקסט שחולץ מהדפים..."):
                    final_prompt = f"""
                    You are a medical expert. Use ONLY the text below from Nelson 22nd Edition to answer.
                    If the text is NOT about {topic}, say 'The identified pages do not contain the topic'.
                    
                    TEXT FROM BOOK:
                    {extracted_text[:15000]}
                    
                    TASK: Summarize the findings, doses, and protocols found in THIS text.
                    Language: Hebrew, English medical terms.
                    """
                    report = call_gemini(final_prompt)
                    st.markdown("---")
                    st.markdown(report)
            else:
                st.error("לא הצלחתי לשלוף טקסט מהעמודים האלו.")
                
        except Exception as e:
            st.error(f"שגיאה בניתוח המיקום: {e}. נסה להזין נושא ספציפי יותר.")
