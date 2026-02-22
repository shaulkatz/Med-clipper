import streamlit as st
import json, urllib.request, time, io, re
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="Nelson AI Lesson Planner", page_icon="🎓", layout="wide")
st.title("🎓 Nelson AI Lesson Planner")
st.markdown("### הכנת מערך שיעור מקיף וחילוץ פרקים אוטומטי")

try:
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
except:
    st.error("שגיאה: וודא שהגדרת GOOGLE_API_KEY ב-Secrets.")
    st.stop()

uploaded_files = st.file_uploader("העלה את חמשת חלקי הספר (PDF)", type="pdf", accept_multiple_files=True)
topic = st.text_input("על איזה נושא נכין מערך שיעור מקיף?")

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())['candidates'][0]['content']['parts'][0]['text']
    except: return "None"

if st.button("בנה מערך שיעור וחלץ חומרים"):
    if not uploaded_files or not topic:
        st.warning("אנא העלה את קבצי הספר והזן נושא.")
    else:
        # שלב א': מחקר ותכנון מערך השיעור
        with st.spinner("ה-AI חוקר את הנושא ובונה סילבוס מקיף..."):
            plan_prompt = f"""
            I want to create a comprehensive, serious medical lesson plan on '{topic}' based on Nelson Textbook of Pediatrics.
            1. What are the essential clinical aspects to cover (Pathophysiology, Symptoms, Diagnosis, Treatment)?
            2. What systemic involvements or complications should be included (e.g. if topic is Rheumatic Fever, include cardiology and nephrology)?
            3. List 3-5 specific keywords or chapter titles I should look for in the textbook.
            
            Return a brief summary of the lesson plan first.
            """
            lesson_plan = call_gemini(plan_prompt)
            st.markdown("---")
            st.subheader("📋 מתווה השיעור שהוכן:")
            st.write(lesson_plan)
        
        # שלב ב': מיפוי וחילוץ מכל הקבצים
        with st.spinner("סורק את חמשת הקבצים לאיתור כל הפרקים הרלוונטיים..."):
            final_writer = PdfWriter()
            found_ranges = []
            
            # בניית מפה גלובלית (דגימה מכל הקבצים)
            global_map = ""
            for file in uploaded_files:
                reader = PdfReader(file)
                # דגימה רחבה יותר בגלל חשיבות המשימה
                for i in range(0, len(reader.pages), 15):
                    text = reader.pages[i].extract_text()
                    if text: global_map += f"\n[FILE:{file.name}][PAGE:{i+1}] {text[:600]}\n"

            extraction_prompt = f"""
            Based on the lesson plan for '{topic}', identify ALL full chapters across these files.
            You must find:
            1. The main chapter.
            2. Related chapters (complications, systemic effects).
            
            Global Map: {global_map[:50000]}
            
            Return the results ONLY in this format: 
            FILENAME: START_PAGE-END_PAGE, FILENAME: START_PAGE-END_PAGE
            """
            
            res = call_gemini(extraction_prompt).strip()
            # חילוץ הוראות החיתוך
            matches = re.findall(r'([\w.-]+):\s*(\d+-\d+)', res)
            
            if matches:
                st.subheader("📂 פרקים שנבחרו לחילוץ:")
                for filename, page_range in matches:
                    st.write(f"- קובץ: **{filename}**, עמודים: **{page_range}**")
                    
                    # ביצוע החיתוך בפועל
                    target_file = next((f for f in uploaded_files if f.name == filename), None)
                    if target_file:
                        target_reader = PdfReader(target_file)
                        s, e = map(int, page_range.split('-'))
                        for p in range(max(0, s-1), min(e, len(target_reader.pages))):
                            final_writer.add_page(target_reader.pages[p])
                
                output = io.BytesIO()
                final_writer.write(output)
                st.success("מערך השיעור והחומרים המקצועיים מוכנים!")
                st.download_button(f"📥 הורד מארז שיעור מלא: {topic}", output.getvalue(), f"{topic}_Full_Lesson_Pack.pdf")
            else:
                st.error("ה-AI לא הצליח לאתר פרקים תואמים לסילבוס שבנה. נסה נושא רחב יותר.")
