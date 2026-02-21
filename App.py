import streamlit as st
import json, urllib.request, time, io, re
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="Med Clipper Super-Mapper", page_icon="🧬")
st.title("🧬 Med Clipper: Full Chapter Mapper")
st.markdown("### חילוץ רב-מערכתי: מוצא את כל הפרקים המלאים שקשורים לנושא")

# משיכת המפתח מהכספת
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("לא נמצא מפתח ב-Secrets. וודא שהגדרת GOOGLE_API_KEY.")
    st.stop()

uploaded_file = st.file_uploader("העלה ספר PDF (נלסון המלא או חלקים)", type="pdf")
topic = st.text_input("מה הנושא? (למשל: Rheumatic fever)")

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())['candidates'][0]['content']['parts'][0]['text']
    except: return "None"

if st.button("בצע מיפוי וחילוץ"):
    if uploaded_file and topic:
        reader = PdfReader(uploaded_file)
        total_pages = len(reader.pages)
        
        with st.spinner("ה-Gem סורק את הספר ומזהה את כל הפרקים הרלוונטיים (ראשיים וסיבוכים)..."):
            # דגימה צפופה לזיהוי מבנה (כל 8 עמודים)
            map_data = ""
            for i in range(0, total_pages, 8):
                text = reader.pages[i].extract_text()
                if text:
                    map_data += f"\n[PDF_INDEX_{i+1}] {text[:1000]}\n"

            # פרומפט "הרופא הבלש"
            mapping_prompt = f"""
            You are a Medical Librarian Gem. I am studying '{topic}'. 
            This disease often has primary chapters and secondary complications in other chapters (e.g., Kidney, Joints, Heart).
            
            Based on this map:
            {map_data[:45000]}
            
            Mission:
            1. Find the PRIMARY chapter for '{topic}'.
            2. Find any OTHER chapters where significant complications of '{topic}' are discussed (e.g. Nephrology).
            3. For EACH found section, identify the FULL chapter boundaries (Start PDF Page to End PDF Page).
            4. Ensure you capture the ENTIRE chapter, not just the page with the keyword.
            
            Return ONLY a list of ranges: 'start-end, start-end'. If not found, return 'None'.
            """
            
            res = call_gemini(mapping_prompt).strip()
            ranges = re.findall(r'\d+-\d+', res)
            
            if ranges:
                st.success(f"איתרתי {len(ranges)} פרקים מלאים רלוונטיים: {', '.join(ranges)}")
                writer = PdfWriter()
                pages_added = set()
                
                # יצירת דף תוכן עניינים פנימי
                for r in ranges:
                    try:
                        start_p, end_p = map(int, r.split('-'))
                        # וידוא גבולות
                        start_p = max(1, start_p)
                        end_p = min(total_pages, end_p)
                        
                        # הוספת העמודים לקובץ החדש
                        for p in range(start_p - 1, end_p):
                            if p not in pages_added:
                                writer.add_page(reader.pages[p])
                                pages_added.add(p)
                    except: continue
                
                output = io.BytesIO()
                writer.write(output)
                st.download_button(f"📥 הורד מארז פרקים: {topic}", output.getvalue(), f"{topic}_Full_Study_Pack.pdf")
                
                with st.expander("ראה מה ה-Gem מצא (תצוגה מקדימה)"):
                    for r in ranges:
                        s = int(r.split('-')[0])
                        st.markdown(f"**פרק המתחיל בעמוד {s}:**")
                        st.write(reader.pages[s-1].extract_text()[:600] + "...")
            else:
                st.error("ה-Gem לא הצליח למפות פרקים רלוונטיים בקובץ זה.")
