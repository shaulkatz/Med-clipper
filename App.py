import streamlit as st
import json, urllib.request

st.title("🚀 בדיקת חיבור יציב ל-Gemini")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ המפתח לא נמצא ב-Secrets!")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip()

if st.button("נסה להתחבר עכשיו"):
    # שינוי הכתובת לגרסה v1 היציבה
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {"contents": [{"parts": [{"text": "Connected successfully?"}]}]}
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode('utf-8'))
            answer = result['candidates'][0]['content']['parts'][0]['text']
            st.success(f"🎉 הצלחנו! גמיני מחובר ועונה: {answer}")
            st.balloons()
    except urllib.error.HTTPError as e:
        st.error(f"❌ שגיאת שרת {e.code}")
        st.code(e.read().decode())
    except Exception as e:
        st.error(f"❌ שגיאה כללית: {str(e)}")
