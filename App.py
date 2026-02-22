import streamlit as st
import json, urllib.request

st.title("🎯 חיבור סופי: Gemini Flash Latest")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ חסר מפתח API ב-Secrets!")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip()

if st.button("בדיקת חיבור סופית"):
    # שימוש בשם המדויק מהרשימה שלך: gemini-flash-latest
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
    payload = {"contents": [{"parts": [{"text": "Write: System Ready"}]}]}
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode('utf-8'))
            answer = result['candidates'][0]['content']['parts'][0]['text']
            st.success(f"🎉 הצלחנו! המודל מחובר: {answer}")
            st.balloons()
    except urllib.error.HTTPError as e:
        st.error(f"❌ שגיאה {e.code}")
        st.code(e.read().decode())
    except Exception as e:
        st.error(f"❌ שגיאה כללית: {str(e)}")
