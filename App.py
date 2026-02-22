import streamlit as st
import json, urllib.request
from pypdf import PdfReader

st.set_page_config(page_title="Nelson Multi-File Mapper", page_icon="📚", layout="wide")
st.title("📚 Nelson AI: מיפוי וניתוח מספר קבצים")

# וידוא מפתח API
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ חסר מפתח API ב-Secrets!")
    st.stop()

# רכיב העלאת מספר קבצים
uploaded_files = st.file_uploader("העלה את חלקי הספר (PDF)", type="pdf", accept_multiple_files=True)

if uploaded_files:
    st.info(f"זוהו {len(uploaded_files)} קבצים. מתחיל בניתוח...")
    
    # יצירת טבלה או רשימה להצגת התוצאות
    for uploaded_file in uploaded_files:
        with st.expander(f"📄 קובץ: {uploaded_file.name}", expanded=True):
            try:
                # 1. חילוץ נתונים טכניים
                reader = PdfReader(uploaded_file)
                num_pages = len(reader.pages)
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.metric("מספר עמודים", num_pages)
                
                # 2. דגימת טקסט לזיהוי פרקים (עמודים ראשונים בדרך כלל מכילים תוכן עניינים או כותרות)
                sample_text = ""
                for i in range(min(5, num_pages)):
                    sample_text += reader.pages[i].extract_text()
                
                # 3. פנייה לגמיני לזיהוי פרקים
                if sample_text.strip():
                    api_key = st.secrets["GOOGLE_API_KEY"].strip()
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                    
                    prompt = f"""
                    Analyze this medical text sample from the file '{uploaded_file.name}'.
                    1. Identify two specific chapters or major headings that appear in this section.
                    2. Return only the names of the two chapters.
                    
                    Text sample:
                    {sample_text[:4000]}
                    """
                    
                    payload = {"contents": [{"parts": [{"text": prompt}]}]}
                    data = json.dumps(payload).encode('utf-8')
                    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
                    
                    with urllib.request.urlopen(req) as res:
                        result = json.loads(res.read().decode('utf-8'))
                        answer = result['candidates'][0]['content']['parts'][0]['text']
                        
                        with col2:
                            st.markdown("**פרקים שזוהו בקובץ זה:**")
                            st.write(answer)
                else:
                    st.warning("לא ניתן היה לחלץ טקסט מהקובץ לצורך זיהוי פרקים.")
                    
            except Exception as e:
                st.error(f"שגיאה בניתוח הקובץ {uploaded_file.name}: {str(e)}")

    st.success("סריקת כל הקבצים הושלמה!")
