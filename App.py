import streamlit as st
import json, urllib.request
from pypdf import PdfReader

st.set_page_config(page_title="Nelson File Analyzer", page_icon="📄")
st.title("📄 Nelson AI: ניתוח קובץ PDF")

# וידוא מפתח API
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ חסר מפתח API ב-Secrets!")
    st.stop()

# רכיב העלאת קובץ
uploaded_file = st.file_uploader("העלה קובץ PDF לניתוח", type="pdf")

if uploaded_file is not None:
    st.success("הקובץ הועלה בהצלחה!")
    
    if st.button("נתח את נושא הקובץ"):
        with st.spinner("קורא את הקובץ ושולח לגמיני..."):
            try:
                # 1. קריאת הטקסט מתוך ה-PDF (דוגמים את העמודים הראשונים כדי להבין נושא)
                reader = PdfReader(uploaded_file)
                text_sample = ""
                # לוקחים עד 3 עמודים ראשונים לקבלת הקשר
                for i in range(min(3, len(reader.pages))):
                    text_sample += reader.pages[i].extract_text()
                
                if not text_sample.strip():
                    st.error("לא הצלחתי לחלץ טקסט מהקובץ. וודא שזהו PDF עם טקסט ולא סריקה (תמונה).")
                else:
                    # 2. הכנת הפרומפט לגמיני
                    prompt = f"Please read the following text from a medical textbook and tell me: What is the general topic of this file?\n\nText:\n{text_sample[:5000]}"
                    
                    # 3. שליחה לגמיני
                    api_key = st.secrets["GOOGLE_API_KEY"].strip()
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                    
                    payload = {"contents": [{"parts": [{"text": prompt}]}]}
                    data = json.dumps(payload).encode('utf-8')
                    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
                    
                    with urllib.request.urlopen(req) as res:
                        result = json.loads(res.read().decode('utf-8'))
                        answer = result['candidates'][0]['content']['parts'][0]['text']
                        
                        st.markdown("---")
                        st.subheader("📝 ניתוח הנושא:")
                        st.write(answer)
                        
            except Exception as e:
                st.error(f"תקלה בתהליך: {str(e)}")
