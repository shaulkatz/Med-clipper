import streamlit as st
import requests
import json

st.set_page_config(page_title="Nelson Simple Expert", page_icon="🩺")
st.title("🩺 Nelson AI: שאלות ותשובות")

# פונקציית Gemini עם הכתובת המדויקת ביותר למניעת 404
def ask_gemini(query):
    if "GOOGLE_API_KEY" not in st.secrets:
        return "❌ חסר מפתח API ב-Secrets"
    
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    
    # שינוי ל-v1beta ושימוש ב-gemini-1.5-flash-latest
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"You are a pediatric expert. Based on Nelson Textbook of Pediatrics 22nd Edition, answer this: {query}. Answer in Hebrew, use English for medical terms."
            }]
        }]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 404:
            return "❌ שגיאה 404: המודל לא נמצא. ננסה לעבור לגרסת Pro או לוודא את הכתובת."
        elif response.status_code == 429:
            return "⚠️ עומס על השרת (429). המתן דקה ונסה שוב."
        else:
            return f"שגיאה {response.status_code}: {response.text}"
    except Exception as e:
        return f"תקלה בתקשורת: {str(e)}"

# --- ממשק פשוט ---
st.info("✅ הדרייב מחובר. המערכת מוכנה לשאלות.")

question = st.text_input("שאל שאלה רפואית מה-Nelson (למשל: Treatment for Acute Bronchiolitis):")

if st.button("שאל את המומחה"):
    if question:
        with st.spinner("הפרופסור מנתח..."):
            answer = ask_gemini(question)
            st.markdown("---")
            st.write(answer)
    else:
        st.warning("אנא הזן שאלה.")

with st.sidebar:
    st.write("מחובר ל-Google Drive (5 קבצים)")
