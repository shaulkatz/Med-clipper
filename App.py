import streamlit as st
import json, urllib.request, io

# בדיקה 1: האם הספרייה מותקנת?
try:
    from pypdf import PdfReader
    st.success("✅ ספריית pypdf נמצאה")
except ImportError:
    st.error("❌ ספריית pypdf חסרה! וודא שיש לך קובץ requirements.txt עם המילה pypdf")
    st.stop()

st.title("🛠️ אבחון תקלות - שלב אחר שלב")

# בדיקה 2: האם המפתח קיים?
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ המפתח GOOGLE_API_KEY לא נמצא ב-Secrets של Streamlit")
    st.stop()
else:
    st.success("✅ מפתח API נמצא בכספת")

uploaded_files = st.file_uploader("העלה קובץ אחד לבדיקה", type="pdf", accept_multiple_files=True)

if st.button("הפעל בדיקת מערכת"):
    if not uploaded_files:
        st.warning("אנא העלה קובץ")
    else:
        # בדיקה 3: האם ניתן לקרוא את ה-PDF?
        st.write("---")
        st.write("🔍 מנסה לקרוא את הקבצים...")
        
        combined_text = ""
        for f in uploaded_files:
            try:
                reader = PdfReader(f)
                first_page = reader.pages[0].extract_text()
                if first_page:
                    st.write(f"✅ הצלחתי לקרוא את עמוד 1 מקובץ: {f.name}")
                    combined_text += first_page[:500]
                else:
                    st.warning(f"⚠️ הקובץ {f.name} נקרא, אבל לא נמצא בו טקסט (אולי סרוק כתמונה?)")
            except Exception as e:
                st.error(f"❌ שגיאה בקריאת {f.name}: {str(e)}")

        # בדיקה 4: האם Gemini עונה?
        if combined_text:
            st.write("---")
            st.write("📡 שולח בקשה ל-Gemini...")
            
            api_key = st.secrets["GOOGLE_API_KEY"].strip()
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            
            prompt = f"Identify the book from this text: {combined_text}"
            data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
            
            try:
                req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req) as res:
                    raw_res = json.loads(res.read())
                    answer = raw_res['candidates'][0]['content']['parts'][0]['text']
                    st.success("🎉 Gemini ענה בהצלחה!")
                    st.info(f"התשובה שלו: {answer}")
            except Exception as e:
                st.error(f"❌ שגיאה בפנייה ל-Gemini: {str(e)}")
