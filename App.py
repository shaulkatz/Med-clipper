import streamlit as st
import json, urllib.request, time
from pypdf import PdfReader, PdfWriter
import io

st.set_page_config(page_title="Medical AI Clipper", page_icon="🩺")
st.title("🩺 Medical PDF AI Clipper")
st.write("העלה ספר רפואי, כתוב נושא, וקבל פרק חתוך וממוקד!")

# ממשק קלט
api_key = st.sidebar.text_input("הכנס Google API Key:", type="password")
uploaded_file = st.file_uploader("בחר קובץ PDF (למשל Nelson)", type="pdf")
topic = st.text_input("איזה נושא/מחלה לחפש?")

if st.button("חתוך לי את הספר!"):
    if not api_key or not uploaded_file or not topic:
        st.warning("חסר מידע: ודא שהעלית קובץ, הכנסת מפתח וכתבת נושא.")
    else:
        with st.spinner("ה-AI קורא ומנתח את הספר... זה עשוי לקחת כמה דקות."):
            reader = PdfReader(uploaded_file)
            total_pages = len(reader.pages)
            writer = PdfWriter()
            relevant_pages = set()
            
            # סריקה במנות קטנות כדי למנוע חסימה
            batch_size = 30
            for i in range(0, total_pages, batch_size):
                end_page = min(i + batch_size, total_pages)
                chunk_text = ""
                for j in range(i, end_page):
                    page_text = reader.pages[j].extract_text()
                    if page_text: chunk_text += f"\n--P{j}--\n{page_text}"
                
                if chunk_text:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                    prompt = f"Find pages about '{topic}'. Return ONLY page numbers separated by commas or 'None': {chunk_text[:30000]}"
                    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
                    try:
                        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
                        res = json.loads(urllib.request.urlopen(req).read())
                        ans = res['candidates'][0]['content']['parts'][0]['text']
                        if "None" not in ans:
                            for p in ans.split(','):
                                try: relevant_pages.add(int(''.join(filter(str.isdigit, p))))
                                except: pass
                    except: pass
                time.sleep(3) # מנוחה קצרה לשרת

            if relevant_pages:
                for p_num in sorted(list(relevant_pages)):
                    if 0 <= p_num < total_pages: writer.add_page(reader.pages[p_num])
                
                output = io.BytesIO()
                writer.write(output)
                st.success(f"סיימתי! מצאתי {len(relevant_pages)} עמודים.")
                st.download_button("📥 הורד את הקובץ החתוך", output.getvalue(), f"{topic}.pdf")
            else:
                st.error("ה-AI לא מצא עמודים רלוונטיים.")
