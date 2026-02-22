import streamlit as st
import json, urllib.request

st.title("🛠️ בדיקת חיבור סופית ל-Gemini")

# בדיקה אם המפתח קיים בכלל בסיקרטס
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ המפתח GOOGLE_API_KEY לא נמצא ב-Secrets!")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip()

if st.button("לחץ כאן לבדיקת תקשורת"):
    # הכתובת המדויקת של ה-API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # שליחת בקשה הכי פשוטה שיש
    payload = {"contents": [{"parts": [{"text": "Hello, confirm connection."}]}]}
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode('utf-8'))
            answer = result['candidates'][0]['content']['parts'][0]['text']
            st.success(f"🎉 הצלחנו! גמיני עונה: {answer}")
            st.balloons()
    except urllib.error.HTTPError as e:
        # כאן אנחנו שולפים את הסיבה האמיתית של גוגל
        error_details = e.read().decode('utf-8')
        st.error(f"❌ שגיאת שרת גוגל: {e.code}")
        st.write("הסבר השגיאה מגוגל:")
        st.json(json.loads(error_details)) 
    except Exception as e:
        st.error(f"❌ שגיאה כללית: {str(e)}")
