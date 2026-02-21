import streamlit as st
import json, urllib.request, time, io, re
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="Med Clipper Multi-Chapter", page_icon="🧬")
st.title("🧬 Med Clipper Multi-Chapter")
st.markdown("### חילוץ רב-מערכתי: מוצא את כל הפרקים הרלוונטיים (ראשיים ומשניים)")

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("לא נמצא מפתח ב-Secrets")
    st.stop()

uploaded_file = st.file_uploader("העלה ספר PDF", type="pdf")
topic = st.text_input("מה הנושא? (ה-Gem יחפש הקשרים בכל מערכות הגוף)")

def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())['candidates'][0]['content']['parts'][0]['text']
    except: return "None"

if st.button("בצע חילוץ רב-מערכתי"):
    if uploaded_file and topic:
        reader = PdfReader(uploaded_file)
        total_pages = len(reader.pages)
        
        with st.spinner("ה-Gem סורק הקשרים רפואיים ומזהה את כל הפרקים הרלוונטיים..."):
            map_data = ""
            step = 10 
            for i in range(0, total_pages, step):
                text = reader.pages[i].extract_text()
                if text:
                    map_data += f"\n[DOC_PAGE_{i+1}] {text[:1000]}\n"

            multi_chapter_prompt = f"""
            You are a specialist physician. I am studying '{topic}'.
            I need ALL relevant FULL chapters. 
            
            1. Find the MAIN chapter for '{topic}'.
            2. Find any SECONDARY chapters where '{topic}' has a major clinical impact (e.g., if it's a systemic disease, look for chapters on affected organs like Kidneys, Heart, or Brain).
            3. For each location, identify the FULL chapter boundaries (Start to End).
            
            Map:
            {map_data[:45000]}
            
            Return ONLY a list of ranges separated by commas, like: '100-120, 450-480'.
            If no major chapters are found, return 'None'.
            """
            
            res = ask_gemini(multi_chapter_prompt).strip()
            ranges = re.findall(r'\d+-\d+', res)
            
            if ranges:
                st.success(f"איתרתי {len(ranges)} מוקדי ידע רלוונטיים: {', '.join(ranges)}")
                writer = PdfWriter()
                pages_added = set()
                
                for r in ranges:
                    start_p, end_p = map(int, r.split('-'))
                    for p in range(start_p - 1, min(end_p, total_pages)):
                        if p not in pages_added:
                            writer.add_page(reader.pages[p])
                            pages_added.add(p)
                
                output = io.BytesIO()
                writer.write(output)
                st.download_button(f"📥 הורד את כל הפרקים הרלוונטיים", output.getvalue(), f"{topic}_Comprehensive.pdf")
            else:
                st.error("ה-Gem לא מצא פרקים עם דיון משמעותי בנושא זה.")
