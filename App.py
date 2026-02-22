import streamlit as st
import json, urllib.request

st.title("🛡️ ניסיון עקיפת חסימת מכסה (429)")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ המפתח לא נמצא ב-Secrets!")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip()

# כפתור הבדיקה
if st.button("בדיקת חיבור סופית (Gemini 1.5)"):
    # שימוש בגרסת ה-v1 היציבה ובמודל 1.5 פלאש שיש לו מכסה רחבה יותר
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {"contents": [{"parts": [{"text": "Connected?"}]}]}
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode('utf-8'))
            answer = result['candidates'][0]['content']['parts'][0]['text']
            st.success(f"✅ הצלחנו! גמיני עונה: {answer}")
    except urllib.error.HTTPError as e:
        if e.code == 429:
            st.error("❌ שגיאה 429: עדיין יש עומס על המפתח שלך.")
            st.info("נסה ליצור פרויקט חדש ב-Google AI Studio וליצור מפתח חדש לגמרי שם.")
        else:
            st.error(f"שגיאה {e.code}: {e.read().decode()}")
    except Exception as e:
        st.error(f"שגיאה כללית: {str(e)}")
