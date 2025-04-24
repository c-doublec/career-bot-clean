# career_bot_app.py
import os
import streamlit as st
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient

# Setup
st.set_page_config(page_title="AI-Powered Career Guidance")
st.title("🎯 Career Recommender with Azure Text Analytics")

# User input
user_input = st.text_input("Tell me about your skills, interests, or goals:")

# Azure configuration
endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT")
key = os.getenv("AZURE_LANGUAGE_KEY")

if not endpoint or not key:
    st.error("⚠️ Azure credentials are missing. Please check App Service settings.")
else:
    credential = AzureKeyCredential(key)
    client = TextAnalyticsClient(endpoint=endpoint, credential=credential)

    if user_input:
        with st.spinner("🔍 Analysing your input..."):
            try:
                response = client.extract_key_phrases([user_input])[0]

                if response.is_error:
                    st.error(f"Azure Text Analytics Error: {response.error}")
                else:
                    key_phrases = response.key_phrases
                    st.subheader("🔑 Key Phrases Identified:")
                    for phrase in key_phrases:
                        st.markdown(f"- {phrase}")

                    # Basic phrase-to-career suggestion logic
                    recommended = []
                    for phrase in key_phrases:
                        phrase_lower = phrase.lower()
                        if any(word in phrase_lower for word in ["data", "machine learning", "ai", "python"]):
                            recommended.append("Data Science / Machine Learning")
                        elif any(word in phrase_lower for word in ["biology", "lab", "health", "genetics"]):
                            recommended.append("Biotechnology / Bioinformatics")
                        elif any(word in phrase_lower for word in ["design", "media", "visual"]):
                            recommended.append("UX/UI Design or Digital Media")
                        elif "environment" in phrase_lower:
                            recommended.append("Environmental Science / Sustainability")
                        elif "business" in phrase_lower or "finance" in phrase_lower:
                            recommended.append("Business Analytics or FinTech")

                    if recommended:
                        st.subheader("🧭 Career Suggestions:")
                        for r in set(recommended):
                            st.success(f"➡ {r}")
                    else:
                        st.info("🤔 No specific matches found — try adding more detailed interests!")

            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")

