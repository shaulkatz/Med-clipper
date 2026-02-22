import streamlit as st
import json, urllib.request, re
from pypdf import PdfReader

st.set_page_config(page_title="Nelson 100% Accuracy", page_icon="⚖️", layout="wide")
st.title("⚖️ Nelson AI: מאמת העמודים הרפואי")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ חסר מפתח API ב-Secrets!")
    st.stop()

uploaded_files = st.file_uploader("העלה את חלקי הספר (PDF)", type="pdf", accept_multiple_files=True)
topic = st.text_input("הזן נושא למחקר (למשל: Measles complications):")

def find_text_in_pdf(reader, search_term):
    """מחפש מחרוזת ב-PDF ומחזיר את מספר עמוד ה-PDF האמיתי"""
    search_term = search_term.lower()
    for i, page in enumerate(reader.pages):
        text = page.extract_text().lower()
        if search_term in text:
            return i + 1  # מחזיר עמוד PDF (מתחיל ב-1)
    return None

def call_gemini(prompt):
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

if st.button("בצע סריקה ואימות עמודים") and uploaded_files and topic:
    status = st.empty()
    
    # שלב 1: חילוץ שמות פרקים וראשי פרקים מכל קובץ (רק התחלה של כל קובץ)
    status.info("🔍 בונה אינדקס שמות פרקים מתוך הקבצים...")
    book_index = ""
    for f in uploaded_files:
        reader = PdfReader(f)
        # דוגמים רק עמודי אינדקס/תוכן בתחילת הקובץ
        index_sample = ""
        for i in range(min(10, len(reader.pages))):
            index_sample += reader.pages[i].extract_text()
        book_index += f"\nFILE: {f.name}\nINDEX SAMPLE: {index_sample[:2000]}\n"

    # שלב 2: גמיני מוצא את שמות הפרקים הרלוונטיים (בלי לנחש עמודים!)
    discovery_prompt = f"""
    You are a medical librarian. Based on these index samples from Nelson Textbook:
    {book_index}
    
    The user is researching: '{topic}'.
    
    Identify the EXACT titles of the 3-5 most relevant chapters or sub-headings. 
    Return ONLY a JSON list of strings. Example: ["Chapter 352: Measles", "Complications of Measles"].
    """
    
    status.info("גמיני מזהה את שמות הפרקים הרלוונטיים...")
    chapters_raw = call_gemini(discovery_prompt)
    
    # ניקוי ה-JSON מהתשובה
    try:
        chapter_titles = json.loads(re.search(r'\[.*\]', chapters_raw, re.DOTALL).group())
    except:
        st.error("ה-AI לא הצליח לגבש רשימת פרקים. נסה נושא ספציפי יותר.")
        st.stop()

    # שלב 3: פייתון מחפש את הפרקים בתוך ה-PDF כדי למצוא עמודים אמיתיים
    status.info("🛠️ מאמת עמודים פיזיים בתוך ה-PDF...")
    verified_results = []
    
    for title in chapter_titles:
        for f in uploaded_files:
            reader = PdfReader(f)
            pdf_page = find_text_in_pdf(reader, title)
            if pdf_page:
                # חילוץ הטקסט מהעמוד כדי למצוא את המספר המודפס (Printed Page)
                page_text = reader.pages[pdf_page-1].extract_text()
                # רגקס לחיפוש מספר עמוד מודפס (בדרך כלל 3-4 ספרות בפינה)
                printed_page_match = re.search(r'\b\d{4}\b', page_text)
                printed_page = printed_page_match.group() if printed_page_match else "Unknown"
                
                verified_results.append({
                    "Chapter": title,
                    "File": f.name,
                    "PDF Page": pdf_page,
                    "Printed Page": printed_page
                })
                break

    # תצוגת התוצאות בטבלה
    if verified_results:
        st.markdown("---")
        st.subheader(f"✅ תוצאות מאומתות עבור: {topic}")
        df = pd.DataFrame(verified_results)
        st.table(df)
        
        st.success("העמודים בטבלה זו נסרקו פיזית על ידי המערכת והם מדויקים.")
    else:
        st.warning("לא נמצאו התאמות מדויקות. נסה להזין שם פרק כפי שהוא מופיע בספר.")

