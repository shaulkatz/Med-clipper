import streamlit as st
import requests
import json

st.set_page_config(page_title="Nelson Diagnosis Tool", page_icon="🩺")
st.title("🩺 Nelson AI: בדיקת מערכות")

# ה-IDs שלך
DRIVE_FILES = {
    "Nelson Part 1": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa",
    "Nelson Part 2": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6",
    "Nelson Part 3": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx",
    "Nelson Part 4": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt",
    "Nelson Part 5": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v",
}

# --- בדיקה 1: Google Drive ---
st.header("1. בדיקת נגישות לקבצים (Drive)")
if st.button("הרץ בדיקת קבצים"):
    for name, f_id in DRIVE_FILES.items():
        url = f'https://drive.google.com/uc?id={f_id}&export=download'
        try:
            # אנחנו בודקים רק את ה-Header כדי לא להוריד את כל הקובץ סתם
            res = requests.head(url, allow_redirects=True)
            if res.status_code == 200:
                st.success(f"✅ {name}: מחובר וזמין!")
            else:
                st.error(f"❌ {name}: שגיאה {res.status_code} - בדוק שיתוף בדרייב")
        except Exception as e:
            st.error(f"❌ {name}: תקלה טכנית - {str(e)}")

st.markdown("---")

# --- בדיקה 2: Gemini API ---
st.header("2. בדיקת תקשורת עם Gemini")
if st.button("שלח 'Ping' ל-Gemini"):
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("❌ המפתח GOOGLE_API_KEY לא נמצא ב-Secrets!")
    else:
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        # הכתובת המדויקת ביותר למניעת 404
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        payload = {"contents": [{"parts": [{"text": "say 'Connection Successful'"}]}]}
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                msg = result['candidates'][0]['content']['parts'][0]['text']
                st.success(f"✅ Gemini עונה: {msg}")
            elif response.status_code == 429:
                st.warning("⚠️ שגיאה 429: המכסה הסתיימה. חכה 60 שניות.")
            elif response.status_code == 404:
                st.error("❌ שגיאה 404: הכתובת של המודל לא נמצאה. נסה לשנות לגרסה אחרת.")
            else:
                st.error(f"❌ שגיאה {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"❌ תקלה בתקשורת: {str(e)}")
