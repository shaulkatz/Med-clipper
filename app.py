import streamlit as st
import requests
import json

st.set_page_config(page_title="Nelson Fixer", page_icon="🔧")
st.title("🔧 Nelson AI: תיקון חיבור סופי")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ מפתח API חסר ב-Secrets!")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip()

# פונקציה שמנסה למצוא איזה מודל עובד אצלך
def get_working_model():
    # רשימת מודלים אפשריים לפי סדר עדיפות
    models_to_try = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-pro"
    ]
    
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": "hi"}]}]}
        try:
            res = requests.post(url, json=payload, timeout=5)
            if res.status_code == 200:
                return model_name
        except:
            continue
    return None

# --- ממשק הבדיקה ---
if st.button("בדוק איזה מודל זמין לי"):
    with st.spinner("סורק מודלים של גוגל..."):
        working_model = get_working_model()
        if working_model:
            st.success(f"✅ נמצא מודל עובד: `{working_model}`")
            st.session_state['active_model'] = working_model
        else:
            st.error("❌ לא נמצא מודל זמין. בדוק אם המפתח תקין או אם יש חסימה בחשבון Google AI Studio.")

st.markdown("---")

# --- שליחת שאלה (אחרי שמצאנו מודל) ---
question = st.text_input("שאל משהו את המומחה (למשל: מה זה נלסון?):")

if st.button("שאל עכשיו"):
    model = st.session_state.get('active_model', "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"You are a medical expert referencing Nelson Pediatrics. Question: {question}. Answer in Hebrew."
            }]
        }]
    }
    
    with st.spinner("מתקשר עם Gemini..."):
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                answer = response.json()['candidates'][0]['content']['parts'][0]['text']
                st.info("תשובת המומחה:")
                st.write(answer)
            else:
                st.error(f"שגיאה {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"תקלה: {str(e)}")
