import streamlit as st
import json, urllib.request

st.title("🧪 בדיקת דופק: חיבור ל-Gemini 2.0")

# בדיקה שהמפתח מוגדר ב-Secrets
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ המפתח לא נמצא ב-Secrets של Streamlit!")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip()

if st.button("שלח הודעת בדיקה"):
    # שימוש במודל המדויק שמצאנו ברשימה שלך
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": "תגיד את המילה: מחובר"}]}]
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode('utf-8'))
            answer = result['candidates'][0]['content']['parts'][0]['text']
            st.success(f"✅ התקשורת עובדת! גמיני עונה: {answer}")
            st.balloons()
    except Exception as e:
        st.error(f"❌ התקשורת נכשלה: {str(e)}")
