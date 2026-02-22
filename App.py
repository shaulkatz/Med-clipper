import streamlit as st
import json, urllib.request

st.title("🎯 חיבור סופי: שימוש במודל 2.0")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ המפתח לא נמצא ב-Secrets!")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip()

if st.button("בדיקת חיבור למודל 2.0"):
    # שימוש בכתובת v1beta ובשם המדויק מהרשימה שלך
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    payload = {"contents": [{"parts": [{"text": "Confirm connection to Gemini 2.0"}]}]}
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode('utf-8'))
            answer = result['candidates'][0]['content']['parts'][0]['text']
            st.success(f"🎉 בינגו! גמיני 2.0 עונה: {answer}")
            st.balloons()
    except urllib.error.HTTPError as e:
        st.error(f"❌ שגיאת שרת {e.code}")
        st.code(e.read().decode())
    except Exception as e:
        st.error(f"❌ שגיאה כללית: {str(e)}")
