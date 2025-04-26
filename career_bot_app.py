
# career_bot_app_with_gpt.py

import os
import streamlit as st
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from PIL import Image
import io
import time
import azure.cognitiveservices.speech as speechsdk
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Azure OpenAI GPT Setup ---
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_key = os.getenv("AZURE_OPENAI_KEY")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

def get_career_suggestions(prompt_text):
    try:
        response = openai.ChatCompletion.create(
            engine=openai_deployment,
            messages=[
                {"role": "system", "content": "You are a helpful career advisor assistant."},
                {"role": "user", "content": f"Suggest suitable career paths based on: {prompt_text}"}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠️ GPT Error: {str(e)}"

# Streamlit Setup
st.set_page_config(page_title="AI-Powered Career Guidance")
st.title("🎯 Career Recommender with Azure AI Services")

# Azure service configurations
lang_endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT")
lang_key = os.getenv("AZURE_LANGUAGE_KEY")
cv_endpoint = os.getenv("AZURE_CV_ENDPOINT")
cv_key = os.getenv("AZURE_CV_KEY")

# User input text
text_input = st.text_input("Tell me about your skills, interests, or goals:")

# 🎙️ Azure Speech-to-Text
st.subheader("🎙️ Voice Input")
if st.button("🎧 Start Recording (speech-to-text)"):
    if os.getenv("AZURE_SPEECH_KEY") and os.getenv("AZURE_SPEECH_REGION"):
        try:
            speech_config = speechsdk.SpeechConfig(
                subscription=os.getenv("AZURE_SPEECH_KEY"),
                region=os.getenv("AZURE_SPEECH_REGION")
            )
            speech_config.speech_recognition_language = "en-US"
            recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

            st.info("Listening... Speak now.")
            result = recognizer.recognize_once()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                st.success(f"🗣️ You said: {result.text}")
                text_input += " " + result.text
            else:
                st.warning(f"Speech not recognized: {result.reason}")

        except Exception as e:
            st.error(f"Speech recognition error: {str(e)}")
    else:
        st.error("Speech service credentials are not set.")

# File uploader
uploaded_file = st.file_uploader("Or upload an image (e.g., poster or brochure) to extract text:", type=["png", "jpg", "jpeg"])

# OCR: Extract text from uploaded image
extracted_text = ""
if uploaded_file and cv_endpoint and cv_key:
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
    try:
        cv_client = ComputerVisionClient(cv_endpoint, CognitiveServicesCredentials(cv_key))
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
            st.info(f"""📄 Text extracted from image:

{extracted_text.strip()}""")

    except Exception as e:
        st.error(f"OCR failed: {str(e)}")

# Combine both sources
combined_input = f"{text_input} {extracted_text}".strip()

# Recommendation logic
def recommend_career(phrases):
    phrases = [p.lower() for p in phrases]
    recommendations = []

    if any(k in phrases for k in ["ai", "machine learning", "data", "data analysis"]):
        recommendations.append("📊 You might enjoy a career in Data Science, AI Research, or Machine Learning.")
    if any(k in phrases for k in ["biology", "biotechnology", "pharma"]):
        recommendations.append("🧬 Consider careers in Biotechnology, Genetic Engineering, or Pharma Research.")
    if any(k in phrases for k in ["engineering", "mechanics", "electronics", "robotics"]):
        recommendations.append("🔧 Mechanical, Electrical, or Robotics Engineering might suit you.")
    if any(k in phrases for k in ["leadership", "strategy", "management"]):
        recommendations.append("📈 Project Management, Strategy Consulting, or Executive roles could be a great fit.")

    if not recommendations:
        recommendations.append("🤔 No specific matches found — try adding more detailed interests!")

    return recommendations

# Azure NLP and Results
if lang_endpoint and lang_key and combined_input:
    try:
        lang_client = TextAnalyticsClient(endpoint=lang_endpoint, credential=AzureKeyCredential(lang_key))
        st.spinner("🔍 Analysing your input...")
        response = lang_client.extract_key_phrases([combined_input])[0]

        if response.is_error:
            st.error(f"Azure Text Analytics Error: {response.error}")
        else:
            key_phrases = response.key_phrases
            st.subheader("🔑 Key Phrases Identified:")
            for phrase in key_phrases:
                st.markdown(f"- {phrase}")

            st.subheader("🧭 Career Suggestions (Rule-Based):")
            suggestions = recommend_career(key_phrases)
            for s in suggestions:
                st.success(s)

            # --- GPT Career Suggestions ---
            if combined_input:
                st.subheader("🧠 GPT Career Suggestions:")
                gpt_response = get_career_suggestions(combined_input)
                st.success(gpt_response)

    except Exception as e:
        st.error(f"❌ Analysis failed: {str(e)}")

elif not (lang_endpoint and lang_key):
    st.error("⚠️ Azure Text Analytics credentials are missing.")
