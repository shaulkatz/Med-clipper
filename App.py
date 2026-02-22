import streamlit as st
import json, urllib.request, time

st.title("🛠️ בדיקת חיבור חכמה (Rate Limit Protected)")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ המפתח לא נמצא ב-Secrets!")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip()

if st.button("בדוק חיבור לגמיני"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": "Say: System Online"}]}]}
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode('utf-8'))
            answer = result['candidates'][0]['content']['parts'][0]['text']
            st.success(f"✅ גמיני עונה: {answer}")
    except urllib.error.HTTPError as e:
        if e.code == 429:
            st.warning("⏳ הגענו למכסה המותרת לדקה. אנא המתן 60 שניות לפני הלחיצה הבאה.")
        else:
            st.error(f"❌ שגיאה {e.code}: {e.read().decode()}")
    except Exception as e:
        st.error(f"❌ שגיאה כללית: {str(e)}")
