import streamlit as st
import json, urllib.request, time, io, re

# בדיקה שהספרייה מותקנת (Streamlit Cloud מתקין אוטומטית מ-requirements.txt)
try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    st.error("Missing pypdf. Please make sure requirements.txt has 'pypdf'")
    st.stop()

st.set_page_config(page_title="Med Clipper High-Res", page_icon="🔬")
st.title("🔬 Med Clipper High-Res")
st.info("מערכת חילוץ חכמה - המפתח נמשך מהכספת.")

# משיכת המפתח מהכספת
try:
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
except:
    st.error("שגיאה: לא נמצא מפתח ב-Secrets. וודא שהגדרת GOOGLE_API_KEY ב-Streamlit Cloud Settings.")
    st.stop()

uploaded_file = st.file_uploader("העלה קטע מהספר (PDF)", type="pdf")
topic = st.text_input("מה הנושא לחיפוש? (למשל: Rheumatic fever)")

def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read())
            return result['candidates'][0]['content']['parts'][0]['text']
    except urllib.error.HTTPError as e:
        if e.code == 429: return "ERROR_QUOTA"
        if e.code == 403: return "ERROR_KEY"
        return f"ERROR_{e.code}"
    except Exception as e:
        return f"ERROR_UNKNOWN: {str(e)}"

if st.button("התחל חילוץ"):
    if not uploaded_file or not topic:
        st.warning("אנא העלה קובץ והזן נושא.")
    else:
        reader = PdfReader(uploaded_file)
        total_pages = len(reader.pages)
        
        with st.spinner("סורק את הקובץ ומנתח הקשרים..."):
            map_text = ""
            # דגימה כל 15 עמודים כדי לא להעמיס על המכסה החינמית
            step = 15 
            for i in range(0, total_pages, step):
                try:
                    page_text = reader.pages[i].extract_text()
                    if page_text:
                        map_text += f"\n[P_{i+1}] {page_text[:600]}\n"
                except: continue

            prompt = f"I am looking for the chapter about '{topic}' in this PDF. Use this map (snippet every {step} pages): {map_text[:30000]}. Return ONLY the page range as 'start-end'. If not in this file, return 'None'."
            
            res = ask_gemini(prompt).strip()
            
            if "ERROR_QUOTA" in res:
                st.error("עומס על השרת של גוגל (429). המתן דקה ונסה שוב.")
            elif "ERROR_KEY" in res:
                st.error("מפתח ה-API לא תקין. וודא שהעתקת אותו נכון ל-Secrets.")
            elif "None" in res or len(re.findall(r'\d+', res)) < 2:
                st.warning(f"הנושא '{topic}' לא נמצא בקובץ שהעלית. וודא שהפרק קיים בטווח העמודים הזה.")
            else:
                nums = re.findall(r'\d+', res)
                start_p, end_p = int(nums[0]), int(nums[1])
                # שולי ביטחון
                start_p, end_p = max(1, start_p - 2), min(total_pages, end_p + 2)
                
                st.success(f"אותר טווח עמודים: {start_p} עד {end_p}")
                writer = PdfWriter()
                for p in range(start_p - 1, end_p):
                    writer.add_page(reader.pages[p])
                
                output = io.BytesIO()
                writer.write(output)
                st.download_button(f"📥 הורד פרק: {topic}", output.getvalue(), f"{topic}.pdf")
