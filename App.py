import streamlit as st
import os

# הגדרה בסיסית ביותר למניעת קריסה
st.title("🔬 Nelson AI: Boot Mode")

# בדיקה ויזואלית של ה-Secrets
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ מפתח ה-API (GOOGLE_API_KEY) חסר ב-Secrets!")
    st.stop()
else:
    st.success("✅ מפתח API זוהה.")

# הצגת מידע על הקבצים רק כדי לראות אם משהו קיים בשרת
st.subheader("מצב אחסון מקומי:")
pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
if pdf_files:
    st.write(f"נמצאו קבצים: {pdf_files}")
else:
    st.info("השרת נקי מקבצים. מוכן להורדה ראשונה.")

# כפתור שמפעיל את שאר הלוגיקה (כדי שלא יקרוס בטעינה)
if st.button("הפעל את המערכת המלאה"):
    st.write("מפעיל הורדה וניתוח...")
    # כאן נכניס בהמשך את שאר הקוד
