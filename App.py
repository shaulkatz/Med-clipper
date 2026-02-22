import streamlit as st
import io, re
from pypdf import PdfReader, PdfWriter
import google.generativeai as genai

# הגדרות תצוגת הדף
st.set_page_config(page_title="Nelson Deep-Lesson Architect", page_icon="🎓", layout="wide")
st.title("🎓 Nelson AI Deep-Lesson Architect")
st.markdown("### בניית מערך שיעור רפואי וחילוץ פרקים חכם מחמישה קבצים")

# וידוא מפתח מהכספת (Secrets) של Streamlit
try:
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    genai.configure(api_key=api_key)
    # הגדרת המודל
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    st.error("שגיאה: וודא שהגדרת GOOGLE_API_KEY ב-Secrets של Streamlit.")
    st.stop()

# העלאת קבצים
uploaded_files = st.file_uploader("העלה את כל חלקי הספר (PDF)", type="pdf", accept_multiple_files=True)
topic = st.text_input("מה הנושא למחקר עומק? (למשל: Rheumatic fever / T-cell deficiency)")

def call_gemini(prompt):
    """קריאה ל-Gemini באמצעות ה-SDK הרשמי במקום בקשת HTTP ישירה"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"ERROR: {str(e)}"

if st.button("התחל מחקר עומק וחילוץ"):
    if len(uploaded_files) < 1 or not topic:
        st.warning("אנא העלה קבצים והזן נושא.")
    else:
        final_writer = PdfWriter()
        
        with st.spinner("מבצע סריקה ראשונית לאיתור אזכורים בקבצים..."):
            global_context = ""
            for file in uploaded_files:
                reader = PdfReader(file)
                # דגימה כל 10 עמודים לזיהוי מבנה - הגבלת אורך למניעת עומס
                for i in range(0, len(reader.pages), 10):
                    text = reader.pages[i].extract_text()
                    if text and topic.lower()[:5] in text.lower():
                        # הוספת תזכורת לשם הקובץ והעמוד
                        global_context += f"\n[FILE: {file.name}][PAGE: {i+1}] {text[:800]}\n"

        # שלב א': מחקר עומק ותכנון סילבוס
        with st.spinner("ה-AI מבצע כעת מחקר עומק לבניית מערך שיעור מקיף..."):
            research_prompt = f"""
            As a Senior Medical Professor, your task is to design a high-level, comprehensive lesson plan for '{topic}' using the Nelson Textbook of Pediatrics.
            
            Based on the detected snippets in the uploaded files:
            {global_context[:40000]}
            
            YOUR MISSION:
            1. Research the scope: What chapters must a student read to master '{topic}'? 
            Include the primary disease chapter, but also systemic involvements.
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
                # ביטוי רגולרי גמיש יותר שמאפשר רווחים בשמות קבצים
                extractions = re.findall(r'([^:,]+):\s*(\d+)-(\d+)', raw_extract)
                
                files_found = False
                for filename, start_p, end_p in extractions:
                    filename = filename.strip()
                    target_file = next((f for f in uploaded_files if f.name.strip() == filename), None)
                    if target_file:
                        files_found = True
                        st.write(f"✂️ מחלץ פרק מקובץ: **{filename}** (עמודים {start_p}-{end_p})")
                        target_reader = PdfReader(target_file)
                        
                        start_idx = max(0, int(start_p) - 1)
                        end_idx = min(int(end_p), len(target_reader.pages))
                        
                        for p in range(start_idx, end_idx):
                            final_writer.add_page(target_reader.pages[p])
                
                if files_found:
                    output = io.BytesIO()
                    final_writer.write(output)
                    st.success("מערך השיעור המקיף והפרקים הרלוונטיים מוכנים להורדה!")
                    st.download_button(
                        label=f"📥 הורד מארז שיעור מקיף: {topic}", 
                        data=output.getvalue(), 
                        file_name=f"{topic}_Deep_Lesson.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("ה-AI ייצר את התוכנית, אך שמות הקבצים שחזר לא תאמו בדיוק לקבצים שהועלו. אנא בדוק את הפלט למעלה.")
            else:
                st.error("ה-AI לא הצליח לגבש מערך שיעור לפי הפורמט הנדרש. שגיאה בפלט:")
                st.code(full_res)
