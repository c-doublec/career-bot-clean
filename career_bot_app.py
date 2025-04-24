# career_bot_app.py
import streamlit as st

st.set_page_config(page_title="Career Recommender", layout="centered")
st.title("🎓 Intelligent STEM Career Recommender")

user_input = st.text_input("Enter your career interests:")
if st.button("Get Recommendation"):
    if "data" in user_input.lower():
        st.success("📊 You might enjoy a career in Data Science or Analytics.")
    elif "biology" in user_input.lower():
        st.success("🧬 Consider Biotechnology or Pharmacology.")
    elif "engineering" in user_input.lower():
        st.success("🔧 Mechanical or Electrical Engineering could be a fit.")
    else:
        st.warning("Try mentioning areas like data, biology, or engineering.")
