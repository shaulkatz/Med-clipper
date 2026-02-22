import streamlit as st
import json, urllib.request, re
from pypdf import PdfReader

st.set_page_config(page_title="Nelson Senior Educator", page_icon="🎓", layout="wide")
st.title("🎓 Nelson AI: Senior Medical Educator")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ חסר מפתח API ב-Secrets!")
    st.stop()

# ממשק משתמש משופר
with st.sidebar:
    st.header("⚙️ הגדרות הרצאה")
    duration = st.text_input("משך זמן ההרצאה (למשל: 20 minutes):", placeholder="חובה להזין זמן")
    uploaded_files = st.file_uploader("העלה את חלקי הספר (PDF)", type="pdf", accept_multiple_files=True)

topic = st.text_input("הזן נושא להרצאה (STRICTLY Nelson 22nd Edition):")

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

if st.button("התחל תכנון הרצאה מבוסס מקורות"):
    # בדיקת Guardrail: האם הוזן זמן?
    if not duration:
        st.warning("⚠️ מה משך הזמן המוקצב להרצאה?")
    elif not uploaded_files or not topic:
        st.error("אנא וודא שהעלית קבצים והזנת נושא.")
    else:
        status = st.empty()
        
        # שלב א': איסוף נתוני "עוגן" מהקבצים
        status.info("🔍 מבצע Anchor Check ואימות מספרי עמודים...")
        anchors_info = ""
        for f in uploaded_files:
            reader = PdfReader(f)
            # קריאת העמוד הראשון של כל קובץ כדי למצוא את העמוד המודפס (עוגן)
            first_page_text = reader.pages[0].extract_text()[:1500]
            anchors_info += f"File: {f.name} | First Page Preview: {first_page_text}\n"

        # שלב ב': בניית הפרומפט המורכב שסיפקת
        full_system_prompt = f"""
        Role: Senior Pediatric Medical Educator & Nelson Expert
        
        USER TOPIC: {topic}
        LECTURE DURATION: {duration}
        
        FILES CONTEXT (ANCHOR DATA):
        {anchors_info}
        
        Use the instructions below to execute the task:
        1. Perform 'Step 1: Verified Source Mapping'.
        2. Create 'Step 2: Customized Lecture Structure' for {duration}.
        3. Generate 'Step 3: Learning & Mastery Chat Prompt'.
        4. Generate 'Step 4: Presentation Architect Prompt'.
        
        Operational Rules:
        - Output in HEBREW, professional terms in ENGLISH.
        - Grounding: ONLY uploaded files.
        - Accuracy: Never guess page numbers.
        """
        
        result = call_gemini(full_system_prompt)
        
        st.markdown("---")
        st.markdown(result)
        
        # הוספת הסיומת המחייבת
        st.markdown("---")
        st.info("האם תרצה שאבנה עבורך תיאור מקרה קליני (Clinical Case Study) או שאלות אמריקאיות (MCQs) לבחינת השליטה בחומר?")
