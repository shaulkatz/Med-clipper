import streamlit as st
import json, urllib.request

st.set_page_config(page_title="Nelson AI Chat", page_icon="🤖")
st.title("🤖 Nelson AI: שלב השאלות והתשובות")
st.markdown("שלב זה נועד לוודא שהאפליקציה מקבלת ממך קלט ומחזירה תשובה כהלכה.")

# וידוא מפתח API
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ חסר מפתח API ב-Secrets!")
    st.stop()

# תיבת קלט מהמשתמש
user_query = st.text_area("כתוב כאן שאלה לגמיני:", placeholder="למשל: What are the primary symptoms of Kawasaki disease?")

if st.button("שלח שאלה"):
    if not user_query:
        st.warning("אנא הזן שאלה לפני הלחיצה.")
    else:
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        # הכתובת המדויקת שעבדה בבדיקה הקודמת
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
        
        payload = {"contents": [{"parts": [{"text": user_query}]}]}
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        with st.spinner("גמיני מנתח ועונה..."):
            try:
                with urllib.request.urlopen(req) as res:
                    result = json.loads(res.read().decode('utf-8'))
                    # שליפת התשובה מהמבנה של גוגל
                    answer = result['candidates'][0]['content']['parts'][0]['text']
                    
                    st.markdown("---")
                    st.subheader("💡 התשובה של גמיני:")
                    st.write(answer)
            except Exception as e:
                st.error(f"תקלה בתקשורת: {str(e)}")
