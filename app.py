import streamlit as st
import requests
import json

st.set_page_config(page_title="Nelson Semantic Expert", page_icon="🧠", layout="wide")
st.title("🧠 Nelson AI: איתור פרקים חכם (Semantic)")

# המיפוי המדויק שלך (נשאר כבסיס לחישוב)
NELSON_MAP = [
    {"name": "Part 1", "id": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt", "start": -41, "end": 958},
    {"name": "Part 2", "id": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v", "start": 959, "end": 1958},
    {"name": "Part 3", "id": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa", "start": 1959, "end": 2960},
    {"name": "Part 4", "id": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6", "start": 2961, "end": 3960},
    {"name": "Part 5", "id": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx", "start": 3961, "end": 4472},
]

def call_gemini(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except: return "Error connecting to AI."

# --- המוח של המערכת: איתור פרקים מבוסס הבנה רפואית ---
def get_smart_chapter_map(topic):
    map_str = "\n".join([f"{m['name']}: Pages {m['start']}-{m['end']}" for m in NELSON_MAP])
    
    # הפרומפט הזה גורם ל-Gemini להשתמש בבינה שלו כדי למצוא פרקים בלי לחפש מילים
    prompt = f"""
    You are a Nelson Textbook Expert. 
    Topic: {topic}
    
    Based on your internal knowledge of Nelson Pediatrics 22nd Ed, identify the 3-5 most essential chapters.
    For each chapter, provide:
    1. Chapter Number and Full Name.
    2. The exact PRINTED page range.
    3. A brief explanation of WHY this chapter is relevant to the topic (the clinical connection).
    
    Use this library structure to tell me which PDF Part it's in:
    {map_str}
    
    Format the output as a clean Hebrew summary followed by a professional table.
    Calculate the 'PDF Page Index' for each range using: (Printed Page - Part Start Page + 1).
    """
    return call_gemini(prompt)

# --- ממשק משתמש ---
st.info("המערכת משתמשת בבינה מלאכותית כדי להבין את הקשרים הרפואיים ולמפות את הפרקים המתאימים.")

topic = st.text_input("הזן נושא רפואי (למשל: 'אי ספיקת לב' או 'הפרעות אלקטרוליטים'):")

if st.button("בצע איתור פרקים חכם"):
    if topic:
        with st.spinner("ה-AI מנתח את הקשרים הרפואיים של הנושא בתוך ה-Nelson..."):
            smart_analysis = get_smart_chapter_map(topic)
            st.markdown("---")
            st.markdown(smart_analysis)
            
            st.success("טיפ: כעת תוכל לפתוח את ה-PDF בעמוד המדויק שחושב בטבלה.")
    else:
        st.warning("אנא הזן נושא.")
