import streamlit as st
import json, urllib.request

st.title("🛠️ בדיקת תקשורת סופית")

# 1. בדיקת קיום המפתח
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ המפתח GOOGLE_API_KEY לא נמצא ב-Secrets!")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip()

if st.button("בדוק חיבור לגמיני"):
    # הכתובת לדיבור עם המודל
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": "Connected?"}]}]}
    data = json.dumps(payload).encode()
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as res:
            response = json.loads(res.read())
            st.success(f"🎉 הצלחנו! גמיני עונה: {response['candidates'][0]['content']['parts'][0]['text']}")
    except urllib.error.HTTPError as e:
        # כאן אנחנו שולפים את השגיאה האמיתית
        error_body = e.read().decode()
        st.error(f"❌ שגיאת שרת גוגל: {e.code}")
        st.json(json.loads(error_body)) # זה יסביר לנו בדיוק למה זה נכשל
    except Exception as e:
        st.error(f"❌ שגיאה כללית: {str(e)}")
