import streamlit as st
import json, urllib.request

st.title("🛠️ בדיקת תקשורת סופית")

# בדיקת קיום המפתח ב-Secrets
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ המפתח 'GOOGLE_API_KEY' לא נמצא ב-Secrets של Streamlit!")
    st.info("וודא שבחלון ה-Secrets כתוב: GOOGLE_API_KEY = 'המפתח_שלך'")
else:
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    st.write(f"🔍 בודק מפתח שמתחיל ב: `{api_key[:8]}...`")

    if st.button("לחץ כאן לבדיקת חיבור"):
        # שימוש בכתובת המדויקת והעדכנית ביותר של ה-API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": "Say 'Connected'"}]}]}
        data = json.dumps(payload).encode()
        
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        try:
            with urllib.request.urlopen(req) as res:
                response = json.loads(res.read())
                answer = response['candidates'][0]['content']['parts'][0]['text']
                st.success(f"🎉 הצלחנו! Gemini עונה: {answer}")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            st.error(f"❌ שגיאת שרת: {e.code}")
            st.code(error_body) # כאן יופיע ההסבר המדויק של גוגל
        except Exception as e:
            st.error(f"❌ שגיאה כללית: {str(e)}")