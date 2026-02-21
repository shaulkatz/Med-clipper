import streamlit as st
import json, urllib.request, time, io, re
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="AI Chapter Extractor", page_icon="📚")
st.title("📚 AI Full Chapter Extractor")
st.markdown("### חילוץ פרקים מלאים בלבד - מבוסס ניתוח מבנה היררכי")

# משיכת המפתח מהכספת
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("לא נמצא מפתח ב-Secrets")
    st.stop()

uploaded_file = st.file_uploader("העלה ספר PDF", type="pdf")
topic = st.text_input("מה הנושא? (ה-Gem יחלץ את כל הפרק הרלוונטי)")

def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())['candidates'][0]['content']['parts'][0]['text']
    except: return "None"

if st.button("חלץ פרק מלא"):
    if uploaded_file and topic:
        reader = PdfReader(uploaded_file)
        total_pages = len(reader.pages)
        
        with st.spinner("ה-Gem מזהה כעת את גבולות הפרק המלא..."):
            # יצירת מפה רחבה לזיהוי מבנה
            map_data = ""
            step = 10 
            for i in range(0, total_pages, step):
                text = reader.pages[i].extract_text()
                if text:
                    map_data += f"\n[DOC_PAGE_{i+1}] {text[:1000]}\n"

            # פרומפט "בלש הפרקים"
            chapter_prompt = f"""
            You are a Medical Textbook Expert. Your goal is to extract a FULL CHAPTER.
            
            1. Find where '{topic}' is discussed in detail.
            2. Once found, look for the START of that chapter (marked by "Chapter X", a large title, or author names).
            3. Look for the END of that chapter (just before the next chapter begins).
            4. I want the ENTIRE chapter, from its first page to its last page.
            
            Map:
            {map_data[:45000]}
            
            Return ONLY the range: start-end.
            """
            
            decision = ask_gemini(chapter_prompt).strip()
            nums = re.findall(r'\d+', decision)
            
            if len(nums) >= 2:
                start_p, end_p = int(nums[0]), int(nums[1])
                
                # הרחבה קלה ליתר ביטחון (לפעמים הכותרת דף קודם)
                start_p = max(1, start_p)
                
                st.success(f"הפרק המלא אותר: עמודים {start_p} עד {end_p}")
                
                with st.expander("בדיקת תחילת פרק"):
                    st.write(f"**עמוד {start_p}:**")
                    st.write(reader.pages[start_p-1].extract_text()[:1000] + "...")

                # יצירת הקובץ
                writer = PdfWriter()
                for p in range(start_p - 1, min(end_p, total_pages)):
                    writer.add_page(reader.pages[p])
                
                output = io.BytesIO()
                writer.write(output)
                st.download_button(f"📥 הורד פרק מלא: {topic}", output.getvalue(), f"{topic}_Full_Chapter.pdf")
            else:
                st.error("לא הצלחתי לזהות פרק שלם עבור הנושא הזה.")
