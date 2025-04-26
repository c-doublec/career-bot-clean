
import os
import io
import time
import streamlit as st
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioConfig
import openai

# Load environment variables
load_dotenv()

# Azure Cognitive Services setup
text_analytics_key = os.getenv("AZURE_LANGUAGE_KEY")
text_analytics_endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT")
cv_key = os.getenv("AZURE_CV_KEY")
cv_endpoint = os.getenv("AZURE_CV_ENDPOINT")
speech_key = os.getenv("AZURE_SPEECH_KEY")
speech_region = os.getenv("AZURE_SPEECH_REGION")

# Azure OpenAI setup
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_key = os.getenv("AZURE_OPENAI_KEY")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# Streamlit app
st.set_page_config(page_title="Career Recommender with Azure AI Services", page_icon="🎯")

st.title("Career Recommender with Azure AI Services")
user_input = st.text_input("Tell me about your skills, interests, or goals:")

# Voice input
st.subheader("Voice Input (Unavailable on Azure Deployment)")
st.info("Voice input is available when running locally, but not on Azure deployment.")

# File uploader for OCR
uploaded_file = st.file_uploader("Or upload an image (e.g., poster or brochure) to extract text:", type=["png", "jpg", "jpeg"])

# OCR logic
extracted_text = ""
if uploaded_file and cv_endpoint and cv_key:
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
    try:
        cv_client = ComputerVisionClient(cv_endpoint, AzureKeyCredential(cv_key))
        stream = io.BytesIO(uploaded_file.read())
        ocr_result = cv_client.read_in_stream(stream, raw=True)
        operation_id = ocr_result.headers["Operation-Location"].split("/")[-1]

        while True:
            result = cv_client.get_read_result(operation_id)
            if result.status not in ['notStarted', 'running']:
                break
            time.sleep(1)

        if result.status == OperationStatusCodes.succeeded:
            for page in result.analyze_result.read_results:
                for line in page.lines:
                    extracted_text += line.text + " "
            st.info(f"Text extracted from image:\n{extracted_text.strip()}")
    except Exception as e:
        st.error(f"OCR failed: {str(e)}")

# Prepare text for analysis
final_text = extracted_text.strip() if extracted_text else user_input.strip()

# Text Analytics for key phrases
key_phrases = []
if final_text and text_analytics_endpoint and text_analytics_key:
    try:
        ta_client = TextAnalyticsClient(endpoint=text_analytics_endpoint, credential=AzureKeyCredential(text_analytics_key))
        response = ta_client.extract_key_phrases(documents=[final_text])[0]
        if not response.is_error:
            key_phrases = response.key_phrases
    except Exception as e:
        st.error(f"Text Analytics Error: {str(e)}")

# Display key phrases
if key_phrases:
    st.subheader("Key Phrases Identified:")
    for phrase in key_phrases:
        st.write("-", phrase)

# Rule-based simple career recommendations
def get_rule_based_recommendation(key_phrases):
    recommendations = []
    if any(kw.lower() in ["ai", "machine learning", "data"] for kw in key_phrases):
        recommendations.append("Data Science, AI Research, or Machine Learning")
    if any(kw.lower() in ["leadership", "manager", "organizer"] for kw in key_phrases):
        recommendations.append("Business Management, Operations, or Project Leadership")
    if any(kw.lower() in ["biology", "chemistry", "genetics"] for kw in key_phrases):
        recommendations.append("Biotechnology, Genetic Engineering, or Pharma Research")
    return recommendations

# Display rule-based recommendations
if key_phrases:
    rule_based = get_rule_based_recommendation(key_phrases)
    st.subheader("Career Suggestions (Rule-Based):")
    if rule_based:
        for rec in rule_based:
            st.success(f"Consider careers in {rec}.")
    else:
        st.info("No specific rule-based career suggestions found. Try refining your interests!")

# GPT Career Suggestions
def get_gpt_recommendations(prompt_text):
    try:
        response = openai.ChatCompletion.create(
            engine=openai_deployment,
            messages=[
                {"role": "system", "content": "You are a helpful career advisor."},
                {"role": "user", "content": f"Suggest suitable career paths based on: {prompt_text}"}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"GPT General Error: {str(e)}"

# Display GPT suggestions
if final_text:
    st.subheader("GPT Career Suggestions:")
    gpt_response = get_gpt_recommendations(final_text)
    if gpt_response:
        st.success(gpt_response)
    else:
        st.info("No GPT suggestions returned.")

