import streamlit as st
import requests

st.set_page_config(page_title="Nelson Model Finder", page_icon="🔍")
st.title("🔍 Nelson AI: איתור מודל פתוח")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ מפתח API חסר ב-Secrets!")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip()

# פונקציה שמושכת את כל המודלים שפתוחים לך בחשבון
def fetch_available_models():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            models_data = res.json()
            # מחלצים רק את השמות שתומכים ביצירת תוכן
            return [m['name'].replace('models/', '') for m in models_data['models'] 
                    if 'generateContent' in m['supportedGenerationMethods']]
        else:
            st.error(f"שגיאת שרת {res.status_code}: {res.text}")
            return []
    except Exception as e:
        st.error(f"תקלה בתקשורת: {e}")
        return []

# --- כפתור הפעלה ---
if st.button("סרוק מודלים זמינים בחשבון שלי"):
    with st.spinner("שואל את גוגל אילו מודלים פתוחים לך..."):
        models = fetch_available_models()
        if models:
            st.success(f"נמצאו {len(models)} מודלים זמינים!")
            selected_model = st.selectbox("בחר מודל לבדיקה:", models)
            st.session_state['chosen_model'] = selected_model
        else:
            st.warning("לא נמצאו מודלים. וודא שהמפתח הופק ב-Google AI Studio.")

st.markdown("---")

# --- בדיקת המודל הנבחר ---
if 'chosen_model' in st.session_state:
    st.write(f"בודק את המודל: **{st.session_state['chosen_model']}**")
    if st.button("שלח שאלת ניסיון"):
        model = st.session_state['chosen_model']
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": "Say 'System Online'"}]}]}
        
        try:
            r = requests.post(url, json=payload)
            if r.status_code == 200:
                answer = r.json()['candidates'][0]['content']['parts'][0]['text']
                st.balloons()
                st.success(f"מעולה! המודל ענה: {answer}")
                st.info(f"השם המדויק שצריך להשתמש בו הוא: {model}")
            else:
                st.error(f"המודל {model} החזיר שגיאה {r.status_code}")
        except Exception as e:
            st.error(f"תקלה: {e}")
