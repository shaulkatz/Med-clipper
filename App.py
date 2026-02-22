import streamlit as st
import json, urllib.request, time, io, re
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="Nelson Deep-Lesson Architect", page_icon="🎓", layout="wide")
st.title("🎓 Nelson AI Deep-Lesson Architect")
st.markdown("### בניית מערך שיעור רפואי וחילוץ פרקים חכם מחמישה קבצים")

# וידוא מפתח מהכספת
try:
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
except:
    st.error("שגיאה: וודא שהגדרת GOOGLE_API_KEY ב-Secrets של Streamlit.")
    st.stop()

# העלאת 5 קבצים במקביל
uploaded_files = st.file_uploader("העלה את כל חמשת חלקי הספר (PDF)", type="pdf", accept_multiple_files=True)
topic = st.text_input("מה הנושא למחקר עומק? (למשל: Rheumatic fever / T-cell deficiency)")

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"ERROR: {str(e)}"

if st.button("התחל מחקר עומק וחילוץ"):
    if len(uploaded_files) < 1 or not topic:
        st.warning("אנא העלה קבצים והזן נושא.")
    else:
        all_matches = []
        final_writer = PdfWriter()
        
        with st.spinner("מבצע סריקה ראשונית לאיתור אזכורים בכל חמשת הקבצים..."):
            global_context = ""
            for file in uploaded_files:
                reader = PdfReader(file)
                # דגימה כל 10 עמודים לזיהוי מבנה
                for i in range(0, len(reader.pages), 10):
                    text = reader.pages[i].extract_text()
                    if text and topic.lower()[:5] in text.lower(): # חיפוש התחלתי גמיש
                        global_context += f"\n[FILE: {file.name}][PAGE: {i+1}] {text[:800]}\n"

        # שלב א': מחקר עומק ותכנון סילבוס
        with st.spinner("ה-AI מבצע כעת מחקר עומק לבניית מערך שיעור מקיף..."):
            research_prompt = f"""
            As a Senior Medical Professor, your task is to design a high-level, comprehensive lesson plan for '{topic}' using the Nelson Textbook of Pediatrics.
            
            Based on the detected snippets in the uploaded files:
            {global_context[:40000]}
            
            YOUR MISSION:
            1. Research the scope: What chapters must a student read to master '{topic}'? 
            Include the primary disease chapter, but also systemic involvements (e.g. cardiac, renal, or neurological chapters if they cover important complications of '{topic}').
            2. Build a Syllabus: Break down the lesson into 'Pathophysiology', 'Clinical Manifestations', and 'Organ-Specific Complications'.
            3. Chapter Mapping: List the exact filenames and page ranges (START-END) for EACH full chapter needed for this deep lesson.
            
            Return the output in this strict format for the app:
            PLAN: [A brief summary of your clinical research and why you chose these chapters]
            EXTRACT: [FILENAME]: [START]-[END], [FILENAME]: [START]-[END]
            """
            
            full_res = call_gemini(research_prompt)
            
            if "EXTRACT:" in full_res:
                st.markdown("---")
                st.subheader("📑 תוצאות מחקר העומק ומערך השיעור:")
                plan_part = full_res.split("EXTRACT:")[0].replace("PLAN:", "").strip()
                st.write(plan_part)
                
                # שלב ב': חיתוך וייצוא
                st.markdown("---")
                st.subheader("📦 מכין את מארז הלימוד המלא...")
                
                raw_extract = full_res.split("EXTRACT:")[-1].strip()
                extractions = re.findall(r'([\w.-]+):\s*(\d+)-(\d+)', raw_extract)
                
                for filename, start_p, end_p in extractions:
                    target_file = next((f for f in uploaded_files if f.name == filename), None)
                    if target_file:
                        st.write(f"✂️ מחלץ פרק מקובץ: **{filename}** (עמודים {start_p}-{end_p})")
                        target_reader = PdfReader(target_file)
                        for p in range(int(start_p)-1, min(int(end_p), len(target_reader.pages))):
                            final_writer.add_page(target_reader.pages[p])
                
                output = io.BytesIO()
                final_writer.write(output)
                st.success("מערך השיעור המקיף והפרקים הרלוונטיים מוכנים להורדה!")
                st.download_button(f"📥 הורד מארז שיעור מקיף: {topic}", output.getvalue(), f"{topic}_Deep_Lesson.pdf")
            else:
                st.error("ה-AI לא הצליח לגבש מערך שיעור מבוסס על הקבצים הקיימים. נסה נושא רחב יותר.")
