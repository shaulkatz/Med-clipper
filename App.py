import streamlit as st
import json, urllib.request, time, io, re
from pypdf import PdfReader, PdfWriter

# הגדרות דף
st.set_page_config(page_title="Med Clipper High-Res", page_icon="🔬")
st.title("🔬 Med Clipper High-Res")
st.info("חילוץ פרקים רפואיים חכם - המפתח נמשך אוטומטית מהכספת.")

# משיכת המפתח מהכספת (Secrets) - כאן אין תיבת טקסט!
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("שגיאה: לא נמצא מפתח בכספת (Secrets) של Streamlit Cloud.")
    st.stop()

uploaded_file = st.file_uploader("העלה ספר PDF (נלסון או אחר)", type="pdf")
topic = st.text_input("מה הנושא לחיפוש? (למשל: Rheumatic fever)")

def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read())
        return result['candidates'][0]['content']['parts'][0]['text']

if st.button("התחל חילוץ"):
    if not uploaded_file or not topic:
        st.warning("אנא העלה קובץ והזן נושא.")
    else:
        reader = PdfReader(uploaded_file)
        total_pages = len(reader.pages)
        
        with st.spinner("סורק את הספר ברזולוציה גבוהה..."):
            map_text = ""
            step = 8 # דגימה כל 8 עמודים
            for i in range(0, total_pages, step):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    map_text += f"\n[PAGE_{i+1}] {page_text[:1000]}\n"

            prompt = f"""
            Identify the exact page range (start-end) for the topic '{topic}'.
            Use the map provided: {map_text[:50000]}
            Return ONLY the range: start-end.
            """
            
            try:
                res = ask_gemini(prompt).strip()
                nums = re.findall(r'\d+', res)
                if len(nums) >= 2:
                    start_p, end_p = int(nums[0]), int(nums[1])
                    start_p = max(1, start_p - 4)
                    end_p = min(total_pages, end_p + 4)
                    
                    st.success(f"אותר טווח עמודים: {start_p} עד {end_p}")
                    writer = PdfWriter()
                    for p in range(start_p - 1, end_p):
                        writer.add_page(reader.pages[p])
                    
                    output = io.BytesIO()
                    writer.write(output)
                    st.download_button(f"📥 הורד פרק: {topic}", output.getvalue(), f"{topic}.pdf")
                else:
                    st.error("ה-AI לא הצליח להגדיר טווח עמודים מדויק.")
            except Exception as e:
                st.error("חלה שגיאה בעיבוד. וודא שהמפתח בכספת תקין.")
