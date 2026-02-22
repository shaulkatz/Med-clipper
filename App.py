import streamlit as st
import json, urllib.request, os, requests, re
from pypdf import PdfReader

# --- הגדרות דף ---
st.set_page_config(page_title="Nelson Senior Expert", page_icon="🔬", layout="wide")

# --- 1. ה-IDs של הספרייה שלך (מוטמעים) ---
DRIVE_FILES = {
    "Nelson Part 1": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa",
    "Nelson Part 2": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6",
    "Nelson Part 3": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx",
    "Nelson Part 4": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt",
    "Nelson Part 5": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v",
}

# --- 2. פונקציית הורדה עם פס התקדמות ויזואלי ---
def download_with_progress(url, local_path, display_name):
    if os.path.exists(local_path):
        return True

    status_container = st.empty()
    progress_bar = st.progress(0)
    
    try:
        # פנייה לגוגל דרייב להורדה ישירה
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        # הערכה של 150MB לתצוגה אם השרת לא מחזיר גודל
        if total_size == 0: total_size = 150 * 1024 * 1024 

        downloaded_size = 0
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    progress = min(downloaded_size / total_size, 1.0)
                    progress_bar.progress(progress)
                    status_container.text(f"📥 מוריד את {display_name}: {downloaded_size // (1024*1024)}MB")
        
        status_container.empty()
        progress_bar.empty()
        return True
    except Exception as e:
        st.error(f"שגיאה בהורדת {display_name}: {str(e)}")
        return False

@st.cache_resource
def setup_library():
    library = []
    for name, f_id in DRIVE_FILES.items():
        url = f'https://drive.google.com/uc?id={f_id}&export=download'
        path = f"{name.replace(' ', '_')}.pdf"
        success = download_with_progress(url, path, name)
        if success:
            library.append({"name": name, "path": path})
    return library

# --- 3. פונקציית Gemini ---
def call_gemini(prompt):
    if "GOOGLE_API_KEY" not in st.secrets:
        return "Error: Missing API Key in Secrets"
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
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

# --- 4. ממשק משתמש ---
st.title("🔬 Nelson AI: Senior Medical Expert Researcher")

# טעינה אוטומטית של הספרייה מהדרייב
library_data = setup_library()

if library_data:
    st.success(f"✅ הספרייה של נלסון (22nd Ed) טעונה ומוכנה! ({len(library_data)} קבצים)")

with st.sidebar:
    st.header("⏱️ הגדרות הרצאה")
    duration = st.text_input("מה משך הזמן המוקצב להרצאה?", placeholder="למשל: 45 minutes")
    st.markdown("---")
    if st.button("רענן ספרייה (Cache Clear)"):
        st.cache_resource.clear()
        st.rerun()

topic = st.text_input("הזן נושא למחקר מקיף ומעמיק (למשל: Kawasaki Disease):")

if st.button("התחל מחקר עומק"):
    if not duration:
        st.warning("⚠️ מה משך הזמן המוקצב להרצאה?")
    elif not topic:
        st.error("אנא הזן נושא למחקר.")
    else:
        with st.spinner("המערכת מבצעת כיול עמודים וניתוח הקשרים קליניים..."):
            # יצירת מפת עוגנים (Calibration) לדיוק מקסימלי בעמודים
            calibration_map = ""
            for book in library_data:
                try:
                    reader = PdfReader(book["path"])
                    # דגימה של דף ראשון ואמצע למניעת סטיות
                    anchor_text = reader.pages[0].extract_text()[:1000]
                    calibration_map += f"\nFILE: {book['name']}\nTOTAL PDF PAGES: {len(reader.pages)}\nFIRST PAGE SNIPPET: {anchor_text}\n"
                except: continue

            # הפרומפט המקצועי המשולב (הגרסה שלך)
            expert_prompt = f"""
            You are a world-renowned medical expert and researcher, with a deep clinical and academic understanding of all fields of medicine, anatomy, and physiology. 
            I have attached files containing a professional medical textbook (Nelson Textbook of Pediatrics, 22nd Edition).

            The topic I am focusing on is: {topic}.
            The lecture duration is: {duration}.

            Your task is to conduct a comprehensive, broad, and in-depth review of the attached book context, locating all chapters, sub-chapters, and paragraphs relevant to this topic. Use your medical knowledge to identify chapters dealing with indirect contexts, mechanisms of action, underlying diseases, differential diagnoses, systemic effects, or any other relevant clinical context.

            **CRITICAL AND STRICT RESTRICTION:** You are strictly forbidden from hallucinating or inventing any information, contexts, chapters, or page numbers. You must base your response entirely and exclusively (100%) on the exact content found within the attached files. 
            
            CALIBRATION DATA:
            {calibration_map}

            For each relevant chapter or section:
            1. Explain professionally why it is related to the topic (based only on the text in the files).
            2. Detail which aspects of the topic (pathology, treatment, etc.) are covered.

            After the review, summarize in an organized table:
            - Chapter Name
            - Chapter Number
            - Printed Page Range (from actual page)
            - File Index Page Range (PDF page number)

            Language: Hebrew prose, English medical terms.
            Conclude with: "האם תרצה שאבנה עבורך תיאור מקרה קליני (Clinical Case Study) או שאלות אמריקאיות (MCQs) לבחינת השליטה בחומר?"
            """
            
            final_report = call_gemini(expert_prompt)
            st.markdown("---")
            st.markdown(final_report)
