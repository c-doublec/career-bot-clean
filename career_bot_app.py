# career_bot_app.py
import os
import streamlit as st
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from PIL import Image
import io

# Knowledge base for richer career suggestions
career_knowledge_base = {
    "leadership": {
        "title": "Leadership Roles",
        "careers": ["Project Manager", "Operations Director", "Team Lead"],
        "summary": "Careers that focus on leading teams, strategic planning, and decision-making."
    },
    "negotiations": {
        "title": "Negotiation & Diplomacy",
        "careers": ["Diplomat", "Legal Consultant", "Sales Executive"],
        "summary": "Careers that rely on persuasion, mediation, and relationship building."
    },
    "sciences": {
        "title": "Scientific Exploration",
        "careers": ["Research Scientist", "Environmental Analyst", "Pharmacologist"],
        "summary": "Careers in empirical research and experimentation across disciplines."
    }
}

# Setup
st.set_page_config(page_title="AI-Powered Career Guidance")
st.title("🎯 Career Recommender with Azure Text Analytics + OCR")

# User input text
user_input = st.text_input("Tell me about your skills, interests, or goals:")

# OCR section
uploaded_file = st.file_uploader("Or upload an image (e.g., poster or brochure) to extract text:", type=["png", "jpg", "jpeg"])

# Azure configuration
lang_endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT")
lang_key = os.getenv("AZURE_LANGUAGE_KEY")
cv_endpoint = os.getenv("AZURE_CV_ENDPOINT")
cv_key = os.getenv("AZURE_CV_KEY")

if not lang_endpoint or not lang_key:
    st.error("⚠️ Azure Text Analytics credentials are missing.")
else:
    lang_cred = AzureKeyCredential(lang_key)
    lang_client = TextAnalyticsClient(endpoint=lang_endpoint, credential=lang_cred)

    if cv_endpoint and cv_key:
        cv_client = ComputerVisionClient(cv_endpoint, CognitiveServicesCredentials(cv_key))

    # Extract text from uploaded image
    if uploaded_file and cv_endpoint and cv_key:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        with st.spinner("🧠 Extracting text from image..."):
            try:
                image_bytes = uploaded_file.read()
                stream = io.BytesIO(image_bytes)
                ocr_result = cv_client.read_in_stream(stream, raw=True)
                operation_location = ocr_result.headers["Operation-Location"]
                operation_id = operation_location.split("/")[-1]

                import time
                while True:
                    result = cv_client.get_read_result(operation_id)
                    if result.status not in ['notStarted', 'running']:
                        break
                    time.sleep(1)

                extracted_text = ""
                if result.status == OperationStatusCodes.succeeded:
                    for page in result.analyze_result.read_results:
                        for line in page.lines:
                            extracted_text += line.text + " "

                user_input = extracted_text.strip()
                st.info(f"📄 Text extracted from image:\n\n{user_input}")

            except Exception as e:
                st.error(f"OCR failed: {str(e)}")

    if user_input:
        with st.spinner("🔍 Analysing your input..."):
            try:
                response = lang_client.extract_key_phrases([user_input])[0]

                if response.is_error:
                    st.error(f"Azure Text Analytics Error: {response.error}")
                else:
                    key_phrases = response.key_phrases
                    st.subheader("🔑 Key Phrases Identified:")
                    for phrase in key_phrases:
                        st.markdown(f"- {phrase}")

                    matched_templates = []
                    for phrase in key_phrases:
                        for key in career_knowledge_base:
                            if key in phrase.lower():
                                matched_templates.append(career_knowledge_base[key])

                    if matched_templates:
                        st.subheader("🧭 Career Templates Suggested:")
                        for entry in matched_templates:
                            st.markdown(f"### {entry['title']}")
                            st.markdown(f"**Careers**: {', '.join(entry['careers'])}")
                            st.markdown(f"_Summary_: {entry['summary']}")
                            st.markdown("---")
                    else:
                        st.info("🤔 No specific matches found — try adding more detailed interests!")

            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")


