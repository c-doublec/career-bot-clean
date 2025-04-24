# career_bot_app.py
import os
import streamlit as st
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient

# Streamlit App UI
st.set_page_config(page_title="Intelligent STEM Career Recommender with Text Analytics", layout="centered")
st.title("🧠 Azure-Powered Career Recommender")

# User input
user_input = st.text_input("What are your interests or skills?")

# Setup Azure Text Analytics
endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT")
key = os.getenv("AZURE_LANGUAGE_KEY")

if not endpoint or not key:
    st.error("Azure Text Analytics credentials are missing. Please set AZURE_LANGUAGE_ENDPOINT and AZURE_LANGUAGE_KEY in App Service → Configuration.")
else:
    credential = AzureKeyCredential(key)
    client = TextAnalyticsClient(endpoint=endpoint, credential=credential)

    if user_input:
        with st.spinner("Analysing your input..."):
            try:
                response = client.extract_key_phrases([user_input])[0]
                if not response.is_error:
                    st.subheader("🔍 Key Phrases Identified:")
                    for phrase in response.key_phrases:
                        st.markdown(f"- {phrase}")
                    st.success("✅ Use these to explore STEM careers like Data Science, Biotechnology, or AI Ethics.")
                else:
                    st.error(f"Error: {response.error}")
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
