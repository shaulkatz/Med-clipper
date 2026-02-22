import streamlit as st
import json, urllib.request, re
from pypdf import PdfReader

st.set_page_config(page_title="Nelson Expert Researcher", page_icon="🔬", layout="wide")
st.title("🔬 Nelson AI: World-Renowned Medical Expert")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ חסר מפתח API ב-Secrets!")
    st.stop()

# ממשק משתמש
with st.sidebar:
    st.header("📂 ניהול קבצים")
    uploaded_files = st.file_uploader("העלה את חלקי הספר (PDF)", type="pdf", accept_multiple_files=True)

topic = st.text_input("הזן נושא למחקר מעמיק (Topic for Research):")

def call_gemini(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # שימוש בכתובת המדויקת שעבדה בבדיקות הקודמות
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Error: {str(e)}"

if st.button("בצע מחקר מקיף") and uploaded_files and topic:
    status_text = st.empty()
    
    # שלב 1: איסוף דגימות תוכן ואינדקס מכל קובץ (כדי למנוע הזיות)
    status_text.info("🧬 סורק את דפי המקור ובונה מפת תוכן...")
    context_data = ""
    for f in uploaded_files:
        reader = PdfReader(f)
        total_p = len(reader.pages)
        # דוגמים את ההתחלה (תוכן עניינים/כותרות) ומספר דפים מהאמצע
        sample = ""
        for i in [0, 1, 2, total_p//4, total_p//2, (3*total_p)//4, total_p-1]:
            try:
                sample += f"\n[PDF Page {i+1}]: " + reader.pages[i].extract_text()[:1000]
            except: continue
        context_data += f"\nFILE: {f.name}\nTOTAL PDF PAGES: {total_p}\nSAMPLES: {sample}\n"

    # שלב 2: הפרומפט החדש שלך
    expert_prompt = f"""
You are a world-renowned medical expert and researcher, with a deep clinical and academic understanding of all fields of medicine, anatomy, and physiology. I have attached files containing a professional medical textbook.

The topic I am focusing on is: {topic}.

Your task is to conduct a comprehensive, broad, and in-depth review of the attached book context, locating all chapters, sub-chapters, and paragraphs relevant to this topic. Since you are an expert, do not just look for exact keyword matches. Use your medical knowledge to identify chapters dealing with indirect contexts, mechanisms of action, underlying diseases, differential diagnoses, systemic effects, or any other relevant clinical context.

**CRITICAL AND STRICT RESTRICTION:** You are strictly forbidden from hallucinating or inventing any information, contexts, chapters, or page numbers. You must base your response entirely and exclusively (100%) on the exact content found within the attached files. Do not use external knowledge or your training data to fill in gaps. If the topic or a specific context does not appear in the book at all, state this explicitly.

Here is the context extracted from the files:
{context_data}

For each relevant chapter or section you locate in the files:
1. Explain professionally why it is related to the topic (based only on the text in the files).
2. Detail which aspects of the topic (e.g., pathology, treatment, diagnosis) are covered in this section.

After the in-depth textual review, summarize your findings in an organized table so I can easily navigate the book. The table must contain only the following columns:
- Chapter Name
- Chapter Number
- Printed Page Range (the page number as printed on the actual page of the book)
- File Index Page Range (the page number within the PDF/digital file itself)

Output in HEBREW, but maintain professional English medical terms.
"""

    status_text.info("הפרופסור מנתח כעת את כל ההקשרים הקליניים...")
    research_results = call_gemini(expert_prompt)
    
    st.markdown("---")
    st.markdown(research_results)
    status_text.success("המחקר הושלם!")
else:
    if not uploaded_files:
        st.info("אנא העלה את חמשת הקבצים כדי להתחיל.")
