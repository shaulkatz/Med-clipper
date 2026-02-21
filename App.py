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
        
        with st.spinner("סורק את הספר ומחפש מילות מפתח..."):
            found_in_pages = []
            map_data = ""
            
            # חיפוש טקסטואלי פשוט בכל עמוד ועמוד (מהיר מאוד)
            for i in range(total_pages):
                text = reader.pages[i].extract_text()
                if text and topic.lower() in text.lower():
                    found_in_pages.append(i + 1)
                    # מוסיף דגימות ל-AI רק מהעמודים שבהם המילה נמצאה
                    if len(map_data) < 30000:
                        map_data += f"\n[PAGE_{i+1}] {text[:1500]}\n"
            
            if not found_in_pages:
                st.error(f"המילה '{topic}' לא נמצאה בכלל בטקסט של הקובץ הזה.")
                st.info("טיפ: וודא שהנושא אכן נמצא בטווח העמודים שהעלית.")
            else:
                st.write(f"🔍 נמצאו אזכורים בעמודים: {found_in_pages[:10]}...")
                
                # עכשיו שואלים את ה-AI להגדיר את גבולות הפרק
                prompt = f"""
                I found mentions of '{topic}' in these PDF pages: {found_in_pages}.
                Here is the text from some of those pages:
                {map_data}
                
                Based on this, what is the full start and end page range of the CHAPTER covering '{topic}'?
                Return ONLY the range like: start-end.
                """
                
                ans = ask_gemini(prompt).strip()
                nums = re.findall(r'\d+', ans)
                
                if len(nums) >= 2:
                    start_p, end_p = int(nums[0]), int(nums[1])
                    # הגנה מפני טעויות טווח
                    start_p = max(1, start_p - 2)
                    end_p = min(total_pages, end_p + 5)
                    
                    st.success(f"הפרק אותר! חותך עמודים {start_p} עד {end_p}")
                    writer = PdfWriter()
                    for p in range(start_p - 1, end_p):
                        writer.add_page(reader.pages[p])
                    
                    output = io.BytesIO()
                    writer.write(output)
                    st.download_button(f"📥 הורד פרק: {topic}", output.getvalue(), f"{topic}.pdf")
                else:
                    st.warning("ה-AI התקשה להגדיר טווח, מוריד את העמודים הספציפיים שבהם המילה נמצאה.")
                    writer = PdfWriter()
                    for p_num in found_in_pages[:50]: # הגבלה ל-50 עמודים
                        writer.add_page(reader.pages[p_num-1])
                    output = io.BytesIO()
                    writer.write(output)
                    st.download_button("📥 הורד עמודים עם אזכורים", output.getvalue(), "mentions.pdf")
