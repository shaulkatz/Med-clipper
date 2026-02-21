import streamlit as st
import json, urllib.request, time, io, re
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="Med Clipper Pro", page_icon="🔬")
st.title("🔬 Med Clipper Pro")

# משיכת המפתח
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("לא נמצא מפתח ב-Secrets")
    st.stop()

uploaded_file = st.file_uploader("העלה קובץ PDF", type="pdf")
topic = st.text_input("נושא לחיפוש (למשל: T-cell deficiency):")

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
        
        # ניקוי מילות החיפוש
        search_words = topic.lower().replace('-', ' ').split()
        
        with st.spinner("סורק את הספר בחיפוש גמיש..."):
            found_in_pages = []
            map_data = ""
            
            for i in range(total_pages):
                text = reader.pages[i].extract_text()
                if text:
                    # ניקוי הטקסט בעמוד לצורך החיפוש
                    clean_text = text.lower().replace('-', ' ')
                    # בדיקה האם רוב מילות החיפוש מופיעות בעמוד
                    match_count = sum(1 for word in search_words if word in clean_text)
                    
                    if match_count >= len(search_words) * 0.7: # התאמה של 70% מהמילים
                        found_in_pages.append(i + 1)
                        if len(map_data) < 35000:
                            map_data += f"\n[PAGE_{i+1}] {text[:1500]}\n"
            
            if not found_in_pages:
                st.error(f"לא מצאתי את '{topic}'. נסה לחפש מילה אחת מרכזית כמו 'T-Cell' או 'Immunodeficiency'.")
            else:
                st.info(f"🔍 נמצאו אזכורים רלוונטיים ב-{len(found_in_pages)} עמודים.")
                
                prompt = f"""
                Analyze these textbook snippets. We are looking for the chapter on '{topic}'.
                 mentios found on pages: {found_in_pages}.
                Snippets:
                {map_data}
                
                What is the full start and end PDF page range of this chapter? 
                Return ONLY 'start-end'.
                """
                
                ans = ask_gemini(prompt).strip()
                nums = re.findall(r'\d+', ans)
                
                if len(nums) >= 2:
                    start_p, end_p = int(nums[0]), int(nums[1])
                    start_p, end_p = max(1, start_p - 1), min(total_pages, end_p + 3)
                    
                    st.success(f"הפרק אותר! עמודים {start_p} עד {end_p}")
                    writer = PdfWriter()
                    for p in range(start_p - 1, end_p):
                        writer.add_page(reader.pages[p])
                    
                    output = io.BytesIO()
                    writer.write(output)
                    st.download_button(f"📥 הורד פרק: {topic}", output.getvalue(), f"{topic}.pdf")
                else:
                    st.warning("ה-AI לא הצליח להגדיר טווח מדויק, אך מוריד את העמודים שנמצאו.")
                    writer = PdfWriter()
                    for p_num in found_in_pages[:30]:
                        writer.add_page(reader.pages[p_num-1])
                    output = io.BytesIO()
                    writer.write(output)
                    st.download_button("📥 הורד עמודי אזכורים", output.getvalue(), "results.pdf")
