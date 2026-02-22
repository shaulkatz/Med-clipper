import streamlit as st
import json, urllib.request, os, requests

# --- הגדרות דף ---
st.set_page_config(page_title="Nelson Simple Ask", page_icon="📖")

# ה-IDs שלך
DRIVE_FILES = {
    "Nelson Part 1": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa",
    "Nelson Part 2": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6",
    "Nelson Part 3": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx",
    "Nelson Part 4": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt",
    "Nelson Part 5": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v",
}

# הורדה בסיסית
def download_files():
    for name, f_id in DRIVE_FILES.items():
        path = f"{name.replace(' ', '_')}.pdf"
        if not os.path.exists(path):
            url = f'https://drive.google.com/uc?id={f_id}&export=download'
            r = requests.get(url)
            with open(path, 'wb') as f:
                f.write(r.content)
    return True

# פונקציית Gemini נקייה (תיקון ל-404 ו-429)
def ask_gemini(question):
    if "GOOGLE_API_KEY" not in st.secrets:
        return "שגיאה: חסר מפתח API ב-Secrets"
    
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # כתובת מעודכנת למניעת 404
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"You are a medical expert referencing the Nelson Textbook of Pediatrics 22nd Edition. Question: {question}. Answer in Hebrew, use English for medical terms. Be precise."
            }]
        }]
    }
    
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"שגיאה מהשרת ({response.status_code}): {response.text}"
    except Exception as e:
        return f"תקלה בתקשורת: {str(e)}"

# --- ממשק משתמש ---
st.title("📖 Nelson AI: שאלות ותשובות")

if st.sidebar.button("טען ספרייה מחדש"):
    with st.spinner("מוריד קבצים..."):
        download_files()
    st.sidebar.success("הספרייה מוכנה!")

question = st.text_area("מה תרצה לדעת מה-Nelson Textbook?", placeholder="למשל: סכם לי את הטיפול ב-Kawasaki Disease")

if st.button("שאל את המומחה"):
    if not question:
        st.warning("אנא הזן שאלה.")
    else:
        with st.spinner("מנתח את המידע..."):
            answer = ask_gemini(question)
            st.markdown("---")
            st.write(answer)
