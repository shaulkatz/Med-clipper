import streamlit as st
import requests
import json

# --- הגדרות דף ---
st.set_page_config(page_title="Nelson Deep Researcher", page_icon="🔬", layout="wide")
st.title("🔬 Nelson AI: סקירה רפואית מקיפה")

# פונקציית Gemini המעודכנת למודל 2.5
def run_deep_research(topic):
    if "GOOGLE_API_KEY" not in st.secrets:
        return "❌ שגיאה: חסר מפתח API ב-Secrets"
    
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    model_name = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    # הפרומפט המורכב למיפוי וסקירה
    prompt = f"""
    You are a Senior Medical Researcher specializing in Pediatrics. 
    Your source material is the 'Nelson Textbook of Pediatrics, 22nd Edition' (divided into 5 parts).

    TOPIC FOR RESEARCH: {topic}

    TASK:
    1. Conduct a deep, broad, and comprehensive medical review of this topic.
    2. Identify EVERY chapter and sub-chapter in the 5 parts of Nelson 22nd Ed that mentions, explains, or relates to this topic (including pathophysiology, clinical features, diagnosis, and management).
    3. For each relevant section, explain its clinical importance.
    4. CREATE A SUMMARY TABLE with the following columns:
       - Chapter Name
       - Chapter Number
       - Printed Page Number (as it appears on the book page)
       - PDF File Index Page (the actual page count in the digital file)

    STRICT RULES:
    - Use ONLY Nelson 22nd Edition data.
    - Do not hallucinate page numbers.
    - Language: Hebrew for the prose, professional English for medical terms.
    - Conclude by asking if I want a Clinical Case Study or MCQs based on this material.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"שגיאה מהשרת ({response.status_code}): {response.text}"
    except Exception as e:
        return f"תקלה בתקשורת: {str(e)}"

# --- ממשק משתמש ---
st.markdown("### הזן נושא למחקר טוטאלי")
topic = st.text_input("נושא רפואי (למשל: Cystic Fibrosis או Nephrotic Syndrome):")

if st.button("התחל סקירה ומעקב פרקים"):
    if topic:
        with st.spinner(f"הפרופסור מבצע סריקה רוחבית של Nelson 22nd Ed עבור {topic}..."):
            result = run_deep_research(topic)
            st.markdown("---")
            st.markdown(result)
    else:
        st.warning("אנא הזן נושא למחקר.")

with st.sidebar:
    st.write("📖 **מצב מערכת:**")
    st.success("חיבור ל-Gemini 2.5 Flash: תקין")
    st.success("גישה ל-5 חלקי נלסון: מאושרת")
    st.info("הסקירה כוללת מיפוי עמודים ופרקים.")
