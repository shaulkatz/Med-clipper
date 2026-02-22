import streamlit as st
import json, urllib.request, time, io, re
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="Nelson AI Teacher", page_icon="🧬", layout="wide")
st.title("🧬 Nelson AI: Deep-Research & Lesson Planner")
st.markdown("### בניית מערך שיעור רפואי וחילוץ פרקים מ-5 חלקי הספר")

# משיכת המפתח
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ חסר מפתח API ב-Secrets!")
    st.stop()

# ממשק העלאת 5 קבצים
uploaded_files = st.file_uploader("העלה את כל חמשת חלקי הספר (PDF)", type="pdf", accept_multiple_files=True)
topic = st.text_input("הזן נושא למחקר עומק (למשל: Rheumatic fever / T-cell deficiency):")

def call_gemini(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # שימוש במודל gemini-2.0-flash שמצאנו ברשימה שלך
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"ERROR: {str(e)}"

if st.button("בצע מחקר וחילוץ מארז לימוד"):
    if not uploaded_files or not topic:
        st.warning("אנא העלה את קבצי הספר והזן נושא.")
    else:
        status = st.empty()
        
        # שלב 1: מחקר עומק
        status.info("🧠 שלב 1: Gemini 2.0 מבצע מחקר עומק רפואי...")
        research_prompt = f"""
        You are a Senior Pediatrics Professor. Design a comprehensive lesson plan for '{topic}' using Nelson Textbook of Pediatrics.
        1. Identify the core pathophysiology and clinical signs.
        2. Identify essential related systems (e.g. cardiac, renal) that must be included for a serious lesson.
        Return a professional syllabus summary.
        """
        lesson_summary = call_gemini(research_prompt)
        st.markdown("---")
        st.subheader("📋 מערך השיעור שהוכן:")
        st.info(lesson_summary)

        # שלב 2: סריקה ומיפוי
        status.info("🔍 שלב 2: סורק את חמשת הקבצים לאיתור הפרקים...")
        global_map = ""
        for f in uploaded_files:
            reader = PdfReader(f)
            # דגימה חכמה של עמודי מפתח
            for i in range(0, len(reader.pages), 15):
                try:
                    text = reader.pages[i].extract_text()
                    if text:
                        global_map += f"\n[FILE: {f.name}][PAGE: {i+1}] {text[:700]}\n"
                except: continue

        # שלב 3: קביעת טווחי חיתוך
        status.info("✂️ שלב 3: Gemini קובע את טווחי החיתוך המדויקים...")
        extraction_prompt = f"""
        Based on the lesson plan for '{topic}' and these files:
        {global_map[:40000]}
        
        Identify the exact FILENAMES and PDF page ranges (START-END) for all relevant full chapters.
        Format: [FILENAME]: [START]-[END]
        """
        
        raw_cmds = call_gemini(extraction_prompt)
        commands = re.findall(r'([\w.-]+):\s*(\d+)-(\d+)', raw_cmds)
        
        if commands:
            final_writer = PdfWriter()
            st.subheader("📂 פרקים שנבחרו לחילוץ:")
            for fname, s, e in commands:
                target = next((f for f in uploaded_files if f.name == fname), None)
                if target:
                    st.write(f"✅ מחלץ מקובץ **{fname}**: עמודים {s} עד {e}")
                    target_reader = PdfReader(target)
                    for p in range(int(s)-1, min(int(e), len(target_reader.pages))):
                        final_writer.add_page(target_reader.pages[p])
            
            output = io.BytesIO()
            final_writer.write(output)
            status.success("🎉 מארז הלימוד מוכן להורדה!")
            st.download_button(f"📥 הורד מארז שיעור מלא: {topic}", output.getvalue(), f"{topic}_Deep_Lesson.pdf")
        else:
            st.error("ה-AI לא הצליח לגבש פקודות חיתוך. וודא ששמות הקבצים ברורים.")
