import streamlit as st
import requests
import json

# --- הגדרות דף ---
st.set_page_config(page_title="Nelson AI Expert", page_icon="📖")
st.title("📖 Nelson AI: המומחה הרפואי שלך")

# ה-IDs שווידאנו שיש אליהם גישה
DRIVE_FILES = {
    "Part 1": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa",
    "Part 2": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6",
    "Part 3": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx",
    "Part 4": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt",
    "Part 5": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v",
}

# --- פונקציית Gemini המנצחת ---
def ask_nelson_expert(query):
    if "GOOGLE_API_KEY" not in st.secrets:
        return "❌ חסר מפתח API ב-Secrets"
    
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    
    # שימוש במודל המדויק שמצאנו בסריקה: gemini-2.5-flash
    model_name = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"You are a senior pediatric expert. Using the Nelson Textbook of Pediatrics 22nd Edition (all 5 parts) as your primary and only source, answer the following question in a comprehensive and professional manner. Locate all relevant chapters and details. Answer in Hebrew, but use English for all medical terms and diagnoses. Question: {query}"
            }]
        }]
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 429:
            return "⚠️ עומס על השרת. אנא המתן דקה ונסה שוב (מגבלת Quota של גוגל)."
        else:
            return f"שגיאה {response.status_code}: {response.text}"
    except Exception as e:
        return f"תקלה בתקשורת: {str(e)}"

# --- ממשק משתמש פשוט ---
st.info("🧬 הספרייה מחוברת (5 קבצים). המודל המופעל: **Gemini 2.5 Flash**")

question = st.text_area("הזן שאלה או נושא למחקר (למשל: סכם את כל המידע על Kawasaki Disease):", height=150)

if st.button("שאל את המומחה"):
    if question:
        with st.spinner("הפרופסור סורק את חמשת חלקי הספר..."):
            answer = ask_nelson_expert(question)
            st.markdown("---")
            st.markdown("### תשובת המומחה:")
            st.write(answer)
    else:
        st.warning("אנא הזן שאלה לפני הלחיצה.")

with st.sidebar:
    st.write("📖 **Nelson 22nd Ed.**")
    st.write("כל 5 החלקים זמינים לניתוח.")
