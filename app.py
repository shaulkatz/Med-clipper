import streamlit as st
import requests
import json

# --- הגדרות דף ---
st.set_page_config(page_title="Nelson Final Expert", page_icon="🔬", layout="wide")
st.title("🔬 Nelson AI: המומחה המדויק (גרסת הקצה)")

# המיפוי הסופי והמדויק עם ה-IDs שלך
NELSON_MAP = [
    {"name": "Part 1", "id": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt", "start": -41, "end": 958},
    {"name": "Part 2", "id": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v", "start": 959, "end": 1958},
    {"name": "Part 3", "id": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa", "start": 1959, "end": 2960},
    {"name": "Part 4", "id": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6", "start": 2961, "end": 3960},
    {"name": "Part 5", "id": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx", "start": 3961, "end": 4472},
]

# --- פונקציית Gemini ---
def ask_nelson(topic):
    if "GOOGLE_API_KEY" not in st.secrets:
        return "❌ חסר מפתח API ב-Secrets"
    
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # המודל המהיר והחזק: gemini-1.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # בניית הקשר המיפוי עבור המודל
    map_context = "\n".join([f"{m['name']}: Pages {m['start']} to {m['end']}" for m in NELSON_MAP])
    
    prompt = f"""
    You are a professional medical librarian and pediatric expert for the Nelson Textbook of Pediatrics, 22nd Edition.
    The textbook is split into 5 PDF files with these EXACT starting and ending printed pages:
    {map_context}
    
    TOPIC: {topic}
    
    INSTRUCTIONS:
    1. Conduct a deep and thorough medical review of the topic.
    2. Identify every relevant chapter and section in Nelson 22nd Ed.
    3. CREATE A SUMMARY TABLE with these exact columns:
       - Chapter Name | Chapter Number
       - Printed Page: The actual number written on the textbook leaf.
       - PDF Location: Which 'Part X' it is in.
       - PDF Page Index: MUST calculate this using: (Target Printed Page - File Start Page + 1).
    
    CRITICAL CALCULATION EXAMPLES:
    - If Printed Page is 1, and Part 1 starts at -41: 1 - (-41) + 1 = 43. (PDF Index 43).
    - If Printed Page is 1000, and Part 2 starts at 959: 1000 - 959 + 1 = 42. (PDF Index 42).
    
    Language: Hebrew for prose, professional English for medical terms and table content.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"שגיאה מהשרת ({response.status_code}): {response.text}"
    except Exception as e:
        return f"תקלה: {str(e)}"

# --- ממשק משתמש ---
st.sidebar.header("📚 מבנה הספרייה")
for m in NELSON_MAP:
    st.sidebar.write(f"**{m['name']}**: עמודים {m['start']} - {m['end']}")

topic = st.text_input("הזן נושא למחקר (למשל: Tetralogy of Fallot):")

if st.button("בצע מחקר ומיפוי סופי"):
    if topic:
        with st.spinner("הפרופסור מנתח את כל חמשת חלקי הספר..."):
            result = ask_nelson(topic)
            st.markdown("---")
            st.markdown(result)
    else:
        st.warning("אנא הזן נושא לחיפוש.")
