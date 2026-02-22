import streamlit as st
import json, urllib.request, time, io, re
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="Nelson AI Deep-Research", page_icon="🎓", layout="wide")
st.title("🎓 Nelson AI: Deep-Research & Lesson Planner")
st.markdown("### מערכת למחקר עומק רפואי וחילוץ פרקים מערכתי")

# וידוא מפתח מהכספת
try:
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
except:
    st.error("שגיאה: לא נמצא מפתח ב-Secrets. וודא שהגדרת GOOGLE_API_KEY.")
    st.stop()

# העלאת 5 קבצים במקביל (0001-1000, 1001-2000, 2001-3000, 3001-4000, 4001-4529)
uploaded_files = st.file_uploader("העלה את חמשת חלקי הספר (PDF)", type="pdf", accept_multiple_files=True)
topic = st.text_input("הזן נושא למחקר עומק (למשל: Rheumatic fever / T-cell deficiency):")

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"ERROR: {str(e)}"

if st.button("בצע מחקר עומק והפק מארז לימוד"):
    if not uploaded_files or not topic:
        st.warning("אנא העלה את קבצי הספר והזן נושא לחיפוש.")
    else:
        # שלב 1: סריקה ראשונית ובניית מפה גלובלית
        with st.spinner("סורק את כל חמשת הקבצים ובונה מפת דרכים ל-AI..."):
            global_map = ""
            for file in uploaded_files:
                reader = PdfReader(file)
                # דגימה צפופה של כל 12 עמודים לזיהוי מבנה ופרקים
                for i in range(0, len(reader.pages), 12):
                    try:
                        text = reader.pages[i].extract_text()
                        if text:
                            global_map += f"\n[FILE: {file.name}][PDF_PAGE: {i+1}] {text[:900]}\n"
                    except:
                        continue

        # שלב 2: מחקר עומק של Gemini (הפרומפט שביקשת)
        with st.spinner("Gemini מבצע כעת מחקר עומק לבניית מערך שיעור מקיף..."):
            research_prompt = f"""
            You are a Senior Medical Professor and Expert Librarian for 'Nelson Textbook of Pediatrics'.
            The user wants to create a deep, comprehensive lesson plan on: '{topic}'.
            
            Based on the global map of the 5 uploaded files:
            {global_map[:50000]}
            
            YOUR RESEARCH MISSION:
            1. SCOPE: Identify the main clinical chapter for '{topic}'.
            2. SYSTEMIC LINKS: Find secondary chapters covering critical complications (e.g., if the topic is systemic, find chapters on affected organs like Heart, Kidneys, or Brain).
            3. ANALYSIS: Explain WHY these specific parts are necessary for a "serious and comprehensive" lesson.
            4. PRECISION: Identify exact FILENAMES and PDF_PAGE ranges for all required FULL chapters.
            
            OUTPUT FORMAT (Mandatory):
            RESEARCH_SUMMARY: [Write your clinical research and lesson plan here]
            EXTRACTION_LIST:
            [FILENAME]: [START_PAGE]-[END_PAGE]
            [FILENAME]: [START_PAGE]-[END_PAGE]
            """
            
            full_research_output = call_gemini(research_prompt)
            
            if "EXTRACTION_LIST:" in full_research_output:
                st.markdown("---")
                st.subheader("📋 מערך השיעור וממצאי המחקר:")
                research_text = full_research_output.split("EXTRACTION_LIST:")[0].replace("RESEARCH_SUMMARY:", "").strip()
                st.write(research_text)
                
                # שלב 3: חיתוך וייצוא אוטומטי
                st.markdown("---")
                st.subheader("📦 יוצר את מארז הלימוד המאוחד...")
                
                # שליפת הוראות החיתוך
                raw_list = full_research_output.split("EXTRACTION_LIST:")[-1].strip()
                extraction_commands = re.findall(r'([\w.-]+):\s*(\d+)-(\d+)', raw_list)
                
                final_writer = PdfWriter()
                
                for filename, start_p, end_p in extraction_commands:
                    target_file = next((f for f in uploaded_files if f.name == filename), None)
                    if target_file:
                        st.write(f"✂️ מחלץ פרק מקובץ **{filename}** (עמודים {start_p} עד {end_p})...")
                        target_reader = PdfReader(target_file)
                        for p in range(int(start_p)-1, min(int(end_p), len(target_reader.pages))):
                            final_writer.add_page(target_reader.pages[p])
                
                # ייצוא הקובץ הסופי
                output = io.BytesIO()
                final_writer.write(output)
                st.success("מארז הלימוד המקיף מוכן!")
                st.download_button(f"📥 הורד מארז שיעור: {topic}", output.getvalue(), f"{topic}_Deep_Lesson.pdf")
            else:
                st.error("ה-AI לא הצליח לגבש רשימת פרקים מדויקת. נסה להשתמש במונח רפואי רשמי.")