import streamlit as st
import json, urllib.request, time, io, re
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="Med Clipper Pro", page_icon="🔬")
st.title("🔬 Med Clipper Pro")

api_key = st.secrets["GOOGLE_API_KEY"]

uploaded_file = st.file_uploader("העלה קובץ PDF", type="pdf")
topic = st.text_input("נושא לחיפוש (באנגלית):")

def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())['candidates'][0]['content']['parts'][0]['text']
    except: return "None"

if st.button("בצע חיפוש עומק"):
    if uploaded_file and topic:
        reader = PdfReader(uploaded_file)
        total_pages = len(reader.pages)
        
        # שלב 1: בדיקת תקינות טקסט
        test_text = reader.pages[0].extract_text()[:500]
        with st.expander("🔍 הצץ לתוך הקובץ (בדיקת קריאות)"):
            st.code(test_text)

        with st.spinner("סורק את הספר..."):
            # דגימה צפופה יותר (כל 6 עמודים) ותפיסת כותרות
            map_data = ""
            for i in range(0, total_pages, 6):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    # לוקח את 1200 התווים הראשונים (כדי לא לפספס כותרות בגלל עמודות)
                    map_data += f"\n[DOC_PAGE_{i+1}] {page_text[:1200]}\n"

            prompt = f"""
            You are a medical researcher. I need to find the chapter about '{topic}'.
            I have a textbook where text might be messy due to double columns.
            Look at these samples every 6 pages:
            {map_data[:40000]}
            
            Find the starting and ending PDF page numbers for '{topic}'. 
            Even if the exact term isn't there, look for related clinical sections.
            Return ONLY the range like: start-end. If not found, return 'None'.
            """
            
            ans = ask_gemini(prompt).strip()
            nums = re.findall(r'\d+', ans)
            
            if len(nums) >= 2:
                start_p, end_p = int(nums[0]), int(nums[1])
                # הרחבת טווח ביטחון ל-10 עמודים כי מדובר בנלסון
                start_p = max(1, start_p - 5)
                end_p = min(total_pages, end_p + 10)
                
                st.success(f"הנושא אותר! עמודים {start_p} עד {end_p}")
                writer = PdfWriter()
                for p in range(start_p - 1, end_p):
                    writer.add_page(reader.pages[p])
                
                output = io.BytesIO()
                writer.write(output)
                st.download_button(f"📥 הורד פרק: {topic}", output.getvalue(), f"{topic}.pdf")
            else:
                st.error(f"לא הצלחתי למצוא את '{topic}'. נסה מונח רחב יותר כמו 'Immunodeficiency' במקום 'T cell'.")
