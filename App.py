import streamlit as st
import json, urllib.request, io
from pypdf import PdfReader

st.set_page_config(page_title="Gemini Connectivity Test", page_icon="🔍")
st.title("🔍 בדיקת תקשורת וזיהוי תוכן")

# וידוא מפתח מהכספת
try:
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
except:
    st.error("שגיאה: לא נמצא מפתח ב-Secrets. וודא שהגדרת GOOGLE_API_KEY.")
    st.stop()

# העלאת קבצים
uploaded_files = st.file_uploader("העלה את הקבצים לבדיקה", type="pdf", accept_multiple_files=True)

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"שגיאת תקשורת: {str(e)}"

if st.button("בדוק מה הנושא הכללי"):
    if not uploaded_files:
        st.warning("אנא העלה לפחות קובץ אחד.")
    else:
        combined_samples = ""
        
        with st.spinner("דוגם טקסט ושולח לבדיקה..."):
            for file in uploaded_files:
                try:
                    reader = PdfReader(file)
                    # לוקח דגימה קטנה מהעמוד הראשון של כל קובץ
                    sample_text = reader.pages[0].extract_text()[:1000]
                    combined_samples += f"\n--- תוכן מקובץ {file.name} ---\n{sample_text}\n"
                except Exception as e:
                    st.error(f"שגיאה בקריאת הקובץ {file.name}: {e}")

            # הפרומפט הכי פשוט שיש
            test_prompt = f"""
            Identify the general topic of these file samples and tell me what book or document this is:
            {combined_samples}
            """
            
            response = call_gemini(test_prompt)
            
            st.markdown("---")
            st.subheader("תשובת Gemini:")
            st.info(response)
