import streamlit as st
import requests

st.title("🧪 בדיקת חיבור ל-Google Drive")

# נבדוק את הקובץ הראשון שלך כדוגמה
FILE_ID = "1QAcPOd_EZnIMN9AZKFhXTPycQb_3XtHa"
url = f'https://drive.google.com/uc?id={FILE_ID}&export=download'

st.write(f"מנסה להתחבר לקובץ: `{FILE_ID}`")

if st.button("בדוק גישה עכשיו"):
    try:
        # אנחנו מבקשים רק את ה-Header (הכותרת) של הקובץ כדי לא להוריד הכל סתם
        response = requests.get(url, stream=True)
        
        if response.status_code == 200:
            st.success("✅ הצלחנו! השרת מצליח לגשת לקובץ בדרייב.")
            st.write(f"גודל הקובץ שזוהה: {int(response.headers.get('Content-Length', 0)) // 1024} KB")
        elif response.status_code == 403:
            st.error("❌ שגיאה 403: הגישה נחסמה. וודא שהקובץ בדרייב מוגדר כ-'Anyone with the link'.")
        else:
            st.error(f"❌ שגיאה {response.status_code}: גוגל לא מאפשר להוריד את הקובץ.")
            
    except Exception as e:
        st.error(f"❌ תקלה טכנית בחיבור: {e}")

st.markdown("---")
st.info("אם הבדיקה עוברת בהצלחה (ירוק), אנחנו יכולים להחזיר את הקוד המלא של הניתוח וה-Gemini.")
