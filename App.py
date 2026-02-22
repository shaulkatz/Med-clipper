import streamlit as st
import json, urllib.request

st.title("🛡️ חיבור מבוסס מכסה פתוחה (1.5 Flash)")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ חסר מפתח API!")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip()

if st.button("בדיקת חיבור למודל 1.5"):
    # שימוש ב-v1beta ובדגם 1.5 שיש לו מכסה חינמית גדולה
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {"contents": [{"parts": [{"text": "Write: Connection Established"}]}]}
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode('utf-8'))
            answer = result['candidates'][0]['content']['parts'][0]['text']
            st.success(f"🎉 סוף סוף! זה עובד: {answer}")
            st.balloons()
    except urllib.error.HTTPError as e:
        st.error(f"שגיאה {e.code}")
        st.code(e.read().decode())
    except Exception as e:
        st.error(f"שגיאה כללית: {str(e)}")
