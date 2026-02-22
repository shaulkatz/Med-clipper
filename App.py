import streamlit as st
import json, urllib.request

st.title("🔍 זיהוי מודלים זמינים")

api_key = st.secrets["GOOGLE_API_KEY"].strip()

if st.button("הצג רשימת מודלים"):
    # פנייה לכתובת שרשומה בשגיאה כדי לראות מה זמין
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        req = urllib.request.Request(url, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            st.success("נמצאו המודלים הבאים:")
            for model in data.get('models', []):
                st.write(f"- `{model['name']}`")
    except Exception as e:
        st.error(f"שגיאה בשליפת המודלים: {str(e)}")
