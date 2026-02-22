import streamlit as st
import google.generativeai as genai
import tempfile
import os

# הגדרות תצוגת הדף
st.set_page_config(page_title="Gemini PDF Interface", page_icon="🧠", layout="wide")
st.title("🧠 ממשק העברת קבצים ל-Gemini")
st.markdown("העלה קבצי PDF, הזן פרומפט, וגמיני יעשה את כל העבודה.")

# וידוא מפתח מהכספת (Secrets) של Streamlit
try:
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    genai.configure(api_key=api_key)
    # שימוש במודל העדכני שתומך בקבצים גדולים
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    st.error("שגיאה: וודא שהגדרת GOOGLE_API_KEY ב-Secrets של Streamlit.")
    st.stop()

# העלאת קבצים
uploaded_files = st.file_uploader("העלה את קבצי ה-PDF", type="pdf", accept_multiple_files=True)

# אזור טקסט חופשי לפרומפט
default_prompt = """As a Senior Medical Professor, your task is to design a high-level, comprehensive lesson plan using the attached textbook files.
...
(הכנס לכאן את הפרומפט שלך)"""

user_prompt = st.text_area("הכנס את הפרומפט שיועבר לגמיני:", value=default_prompt, height=200)

if st.button("שלח לגמיני"):
    if len(uploaded_files) < 1 or not user_prompt:
        st.warning("אנא העלה לפחות קובץ אחד והזן פרומפט.")
    else:
        with st.spinner("מעלה קבצים לשרתי גוגל וממתין לניתוח של Gemini... (עשוי לקחת קצת זמן)"):
            try:
                gemini_files = []
                
                # 1. העלאת הקבצים ל-Gemini File API
                for uploaded_file in uploaded_files:
                    # יצירת קובץ זמני כי ה-API של גוגל דורש נתיב לקובץ פיזי
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                        temp_file.write(uploaded_file.read())
                        temp_path = temp_file.name
                    
                    # העלאה לגוגל
                    g_file = genai.upload_file(path=temp_path, display_name=uploaded_file.name)
                    gemini_files.append(g_file)
                    
                    # מחיקת הקובץ הזמני מהשרת של Streamlit
                    os.remove(temp_path)
                
                # 2. שליחת הפרומפט + הקבצים לגמיני
                # אנחנו מעבירים לו רשימה שמכילה קודם את הטקסט, ואז את כל הקבצים
                request_content = [user_prompt] + gemini_files
                response = model.generate_content(request_content)
                
                # 3. הצגת הפלט
                st.markdown("---")
                st.subheader("🤖 הפלט של Gemini:")
                st.write(response.text)
                
                # ניקוי הקבצים מהשרתים של גוגל בסיום התהליך (מומלץ כדי לא לחרוג ממגבלת האחסון החינמית)
                for f in gemini_files:
                    genai.delete_file(f.name)
                    
            except Exception as e:
                st.error(f"אירעה שגיאה בתקשורת מול גמיני: {str(e)}")
