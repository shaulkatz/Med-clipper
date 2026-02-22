import streamlit as st
import requests
import json

# --- הגדרות דף ---
st.set_page_config(page_title="Nelson Precise Expert", page_icon="🔬", layout="wide")
st.title("🔬 Nelson AI: המומחה המדויק (מהדורה 22)")

# המיפוי המדויק שסיפקת
NELSON_MAP = [
    {"name": "Part 1", "id": "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa", "start": 1, "end": 958},
    {"name": "Part 2", "id": "1XgAmPZRspaFixuwZRUA9WRDtJe7UfGX6", "start": 959, "end": 1958},
    {"name": "Part 3", "id": "1iEukcQ443jQeG35u4zSENFb_9vkhiCtx", "start": 1959, "end": 2960},
    {"name": "Part 4", "id": "1rgucmtUfSN6wUzpyptOilOi4LVykQQnt", "start": 2961, "end": 3960},
    {"name": "Part 5", "id": "1ru9-fs1MnTaa5vJzNV1sryj0hRxPy3_v", "start": 3961, "end": 4472},
]

# --- פונקציית Gemini ---
def ask_nelson(topic):
    if "GOOGLE_API_KEY" not in st.secrets:
        return "❌ חסר מפתח API ב-Secrets"
    
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # המודל המדויק שעובד אצלך: gemini-2.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # בניית ההקשר של מספרי העמודים עבור המודל
    map_context = "\n".join([f"{m['name']}: Pages {m['start']} to {m['end']}" for m in NELSON_MAP])
    
    prompt = f"""
    You are a world-class pediatric expert. Your source is the Nelson Textbook of Pediatrics, 22nd Edition.
    The book is divided into 5 PDF files with the following EXACT page ranges:
    {map_context}
    
    TOPIC: {topic}
    
    INSTRUCTIONS:
    1. Conduct a deep, comprehensive medical review of the topic.
    2. Map every relevant chapter.
    3. CREATE A SUMMARY TABLE with these columns:
       - Chapter Name | Chapter Number
       - Printed Page: The actual page number from the textbook.
       - PDF Location: Which 'Part X' the page is in.
       - PDF Page Index: Calculate this: (Printed Page - Start Page of that Part + 1).
    
    Example: If you find info on printed page 1000, it belongs to Part 2 (which starts at 959). 
    Calculation: 1000 - 959 + 1 = 42. So PDF Page Index is 42.
    
    Language: Hebrew for prose, professional English for medical terms. Be 100% accurate.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"שגיאה {response.status_code}: {response.text}"
    except Exception as e:
        return f"תקלה: {str(e)}"

# --- ממשק משתמש ---
st.sidebar.header("📚 מבנה הספרייה")
for m in NELSON_MAP:
    st.sidebar.write(f"**{m['name']}**: {m['start']} - {m['end']}")

topic = st.text_input("הזן נושא למחקר (למשל: Rheumatic Fever או Bronchiolitis):")

if st.button("בצע מחקר ומיפוי מדויק"):
    if topic:
        with st.spinner("הפרופסור סורק את הספרייה ומחשב עמודים..."):
            result = ask_nelson(topic)
            st.markdown("---")
            st.markdown(result)
    else:
        st.warning("אנא הזן נושא.")
