import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# הגדרות תצוגת הדף
st.set_page_config(page_title="Gemini PDF Interface", page_icon="🧠", layout="wide")
st.title("🧠 ממשק העברת קבצים ל-Gemini")
st.markdown("העלה קבצי PDF, הזן פרומפט, וגמיני יעשה את כל העבודה.")

# וידוא מפתח מהכספת
try:
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    genai.configure(api_key=api_key)
    # שימוש במודל ה-Pro שמתאים למסמכים ארוכים מאוד (עד 2 מיליון טוקנים)
    model = genai.GenerativeModel("gemini-1.5-pro")
except Exception as e:
    st.error("שגיאה: וודא שהגדרת GOOGLE_API_KEY ב-Secrets של Streamlit.")
    st.stop()

# העלאת קבצים
uploaded_files = st.file_uploader("העלה את קבצי ה-PDF", type="pdf", accept_multiple_files=True)

# אזור טקסט חופשי לפרומפט
default_prompt = """## Operational Rules (Strict)
- **Language:** Output in HEBREW, but all professional medical terms, diagnoses, and drug names MUST remain in ENGLISH.
- **Grounding:** Use ONLY the uploaded Nelson files. No external knowledge or hallucinations. If the topic isn't found, state that.
- **Accuracy:** Never guess a page or chapter number. Always verify by scanning the PDF text headers/footers."""

user_prompt = st.text_area("הכנס את הפרומפט שיועבר לגמיני:", value=default_prompt, height=200)

if st.button("שלח לגמיני"):
    if len(uploaded_files) < 1 or not user_prompt:
        st.warning("אנא העלה לפחות קובץ אחד והזן פרומפט.")
    else:
        with st.spinner("מעלה קבצים וממתין לעיבוד בשרתי גוגל (לקבצים גדולים זה עשוי לקחת קצת זמן)..."):
            try:
                gemini_files = []
                
                # 1. העלאת הקבצים
                for uploaded_file in uploaded_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                        temp_file.write(uploaded_file.read())
                        temp_path = temp_file.name
                    
                    g_file = genai.upload_file(path=temp_path, display_name=uploaded_file.name)
                    
                    # 2. המתנה קריטית לעיבוד הקובץ בשרת (החלק שמונע את שגיאת ה-400)
                    while g_file.state.name == "PROCESSING":
                        time.sleep(3) # ממתין 3 שניות ובודק שוב
                        g_file = genai.get_file(g_file.name)
                        
                    if g_file.state.name == "FAILED":
                        st.error(f"אירעה שגיאה בעיבוד הקובץ {uploaded_file.name} בשרתי גוגל.")
                        continue
                        
                    gemini_files.append(g_file)
                    os.remove(temp_path)
                
                # 3. שליחה למודל
                request_content = [user_prompt] + gemini_files
                response = model.generate_content(request_content)
                
                # 4. הצגת התוצאה
                st.markdown("---")
                st.subheader("🤖 הפלט של Gemini:")
                st.write(response.text)
                
                # ניקוי הקבצים מהשרתים בסיום
                for f in gemini_files:
                    genai.delete_file(f.name)
                    
            except Exception as e:
                st.error(f"אירעה שגיאה בתקשורת מול גמיני: {str(e)}")
