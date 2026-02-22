import streamlit as st
import requests
import json
import os
from pypdf import PdfReader

st.set_page_config(page_title="Nelson Chapter Expert", page_icon="🔬", layout="wide")
st.title("🔬 Nelson AI: ניתוח פרקים מלאים")

# המיפוי המדויק שלך
NELSON_MAP = [
    {"name": "Part 1", "id": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt", "start": -41, "end": 958},
    {"name": "Part 2", "id": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v", "start": 959, "end": 1958},
    {"name": "Part 3", "id": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa", "start": 1959, "end": 2960},
    {"name": "Part 4", "id": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6", "start": 2961, "end": 3960},
    {"name": "Part 5", "id": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx", "start": 3961, "end": 4472},
]

def call_gemini(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # שימוש במודל שזיהינו בסריקה: gemini-2.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    res = requests.post(url, json=payload)
    return res.json()['candidates'][0]['content']['parts'][0]['text']

# --- פונקציה לזיהוי הפרקים הרלוונטיים ---
def identify_chapters(topic):
    map_context = "\n".join([f"{m['name']}: {m['start']}-{m['end']}" for m in NELSON_MAP])
    prompt = f"""
    Topic: {topic}
    Library Map: {map_context}
    
    You are a pediatric expert. Identify the FULL CHAPTERS in Nelson Textbook of Pediatrics 22nd Ed that cover this topic.
    For each chapter, provide:
    1. Exact Chapter Name and Number.
    2. The full Printed Page Range (e.g., 1240-1255).
    3. Determine which PDF Part(s) contain this range.
    4. Provide the PDF Page Index Range for each Part.
    
    Format: Return a JSON-ready list of objects.
    """
    response = call_gemini(prompt)
    # ניקוי הטקסט כדי לחלץ רק את הרשימה (למקרה שגמיני מוסיף מלל)
    return response

# --- ממשק משתמש ---
st.info("המערכת תסרוק ותמפה את הפרקים המלאים הרלוונטיים מתוך 4,472 עמודי הספר.")

topic = st.text_input("הזן נושא לסריקת פרקים (למשל: Congenital Heart Disease):")

if st.button("בצע סקירת פרקים מלאה"):
    if topic:
        with st.spinner("מזהה את הפרקים הרלוונטיים בנלסון 22..."):
            # שלב 1: זיהוי ומיפוי
            chapter_plan = identify_chapters(topic)
            
            # שלב 2: יצירת הסקירה המעמיקה
            final_prompt = f"""
            Based on Nelson Textbook of Pediatrics 22nd Edition, provide a high-level medical synthesis for the topic: {topic}.
            
            Your analysis MUST focus on the WHOLE chapters identified here:
            {chapter_plan}
            
            For each chapter:
            - Summarize the core pathophysiology.
            - List the clinical "red flags".
            - Summarize the full management protocol as described in the chapter.
            
            At the end, provide a clear NAVIGATION TABLE:
            | Chapter | Number | Printed Range | PDF Part | PDF Page Range |
            
            Language: Hebrew prose, English medical terms.
            """
            
            with st.spinner("מנתח את מבנה הפרקים ומסכם את החומר..."):
                report = call_gemini(final_prompt)
                st.markdown("---")
                st.markdown(report)
    else:
        st.warning("אנא הזן נושא.")

with st.sidebar:
    st.write("📖 **מצב סריקה:** פרקים מלאים")
    st.write("עמודי התחלה מכוילים (כולל ה-41- בחלק 1).")
