import streamlit as st
import json, urllib.request, time, io, re
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="Med Clipper High-Res", page_icon="🔬")
st.title("🔬 Med Clipper High-Res")
st.write("סריקה בצפיפות גבוהה - נועד למצוא גם פרקים קצרים במיוחד ללא אינדקס.")

api_key = st.secrets["GOOGLE_API_KEY"]

uploaded_file = st.file_uploader("העלה ספר PDF", type="pdf")
topic = st.text_input("מה הנושא לחיפוש? (למשל: Rheumatic fever)")

def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read())
        return result['candidates'][0]['content']['parts'][0]['text']

if st.button("התחל חילוץ ברזולוציה גבוהה"):
    if not uploaded_file or not topic:
        st.warning("אנא העלה קובץ והזן נושא.")
    else:
        reader = PdfReader(uploaded_file)
        total_pages = len(reader.pages)
        
        with st.spinner("בונה מפת ספר צפופה... (תהליך יסודי יותר)"):
            map_text = ""
            # צפיפות גבוהה: דגימה כל 8 עמודים
            step = 8 
            for i in range(0, total_pages, step):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    # לוקח 1000 תווים כדי לתפוס כותרות ותוכן משמעותי
                    map_text += f"\n[PAGE_{i+1}] {page_text[:1000]}\n"

            prompt = f"""
            You are a professional medical librarian. I need to extract ALL pages related to '{topic}'.
            I am providing a DENSE sample map of the textbook (one snippet every {step} pages).
            
            Based on the snippets and your medical knowledge:
            1. Locate where the discussion of '{topic}' starts and ends.
            2. Even if a snippet doesn't mention it directly, infer the range based on surrounding chapters (e.g., if page 800 is 'Heart Failure' and page 850 is 'Valvular Disease', then 'Rheumatic Fever' is likely between them).
            3. Provide the MOST LIKELY page range.
            
            Map data:
            {map_text[:50000]}
            
            Return ONLY the range in format: start-end. If absolutely not found, return 'None'.
            """
            
            try:
                res = ask_gemini(prompt).strip()
                if "None" in res or "-" not in res:
                    st.error("הנושא לא אותר. נסה להשתמש במונח רפואי רחב יותר.")
                else:
                    # מוציא את המספרים מהתשובה (למשל מתוך "750-780")
                    nums = re.findall(r'\d+', res)
                    start_p, end_p = int(nums[0]), int(nums[1])
                    
                    # הרחבת טווח לביטחון
                    start_p = max(1, start_p - 4)
                    end_p = min(total_pages, end_p + 4)
                    
                    st.success(f"הנושא אותר בטווח עמודים: {start_p} עד {end_p}")
                    
                    writer = PdfWriter()
                    for p in range(start_p - 1, end_p):
                        writer.add_page(reader.pages[p])
                    
                    output = io.BytesIO()
                    writer.write(output)
                    st.download_button(f"📥 הורד פרק: {topic}", output.getvalue(), f"{topic}.pdf")
                    
            except Exception as e:
                st.error("שגיאה בניתוח המפה הצפופה. וודא שהמפתח תקין.")
