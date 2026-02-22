import streamlit as st

st.title("מבחן החייאה: שלב 1")
st.write("אם אתה רואה את הטקסט הזה, השרת חי!")

# בדיקה אם המפתח בכלל קיים בזיכרון
if "GOOGLE_API_KEY" in st.secrets:
    st.success("המפתח (Secrets) מוגדר תקין.")
else:
    st.warning("המפתח חסר ב-Secrets.")
