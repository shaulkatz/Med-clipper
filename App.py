import streamlit as st
import json, urllib.request

st.title("🔍 בדיקת שגיאת תקשורת")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ המפתח לא נמצא בסיקרטס!")
else:
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    st.write(f"מפתח מתחיל ב: {api_key[:5]}...") # בדיקה שהמפתח נטען

    if st.button("נסה לדבר עם גמיני"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        data = json.dumps({"contents": [{"parts": [{"text": "Hello, are you there?"}]}]}).encode()
        
        try:
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as res:
                st.success("🎉 הצלחה! גמיני ענה.")
                st.write(json.loads(res.read())['candidates'][0]['content']['parts'][0]['text'])
        except urllib.error.HTTPError as e:
            st.error(f"❌ שגיאת שרת (HTTP Error): {e.code}")
            st.write(f"הסבר השגיאה: {e.read().decode()}")
        except Exception as e:
            st.error(f"❌ שגיאה כללית: {str(e)}")