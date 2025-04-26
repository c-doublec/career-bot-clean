import os
import io
import time
import streamlit as st
import openai
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioConfig, ResultReason
from msrest.authentication import CognitiveServicesCredentials


# Load environment variables
load_dotenv()

# Azure OpenAI GPT Setup
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_key = os.getenv("AZURE_OPENAI_KEY")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# Speech configuration
speech_key = os.getenv("AZURE_SPEECH_KEY")
speech_region = os.getenv("AZURE_SPEECH_REGION")

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

# --- Functions ---
def get_career_suggestions(prompt_text):
    try:
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": "You are a helpful career advisor assistant."},
                {"role": "user", "content": f"Suggest suitable career paths based on: {prompt_text}"}
            ]
        )
        return response.choices[0].message.content
    except openai.RateLimitError as e:
        st.error(f"⚠️ GPT Rate Limit Error: {str(e)}")
    except Exception as e:
        st.error(f"⚠️ GPT General Error: {str(e)}")
        
# --- Streamlit App ---
st.set_page_config(page_title="Career Recommender with Azure AI Services", page_icon="🎯")
st.title("🎯 Career Recommender with Azure AI Services")

# Detect if running in Azure
running_in_azure = os.getenv("WEBSITE_SITE_NAME") is not None

# User input
user_text = st.text_input("Tell me about your skills, interests, or goals:")

# Voice input (only available locally)
if not running_in_azure:
    st.subheader("🎙️ Voice Input")
    if st.button("🎧 Start Recording (speech-to-text)"):
        if speech_key and speech_region:
            try:
                speech_config = SpeechConfig(subscription=speech_key, region=speech_region)
                audio_config = AudioConfig(use_default_microphone=True)
                recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

                st.info("Listening... Speak now.")
                result = recognizer.recognize_once()

                if result.reason == ResultReason.RecognizedSpeech:
                    user_text = result.text
                    st.success(f"🗣️ You said: {result.text}")
                else:
                    st.warning("⚠️ Speech not recognized. Please try again.")
            except Exception as e:
                st.error(f"Speech recognition error: {str(e)}")
        else:
            st.error("Speech service credentials are not set.")
else:
    st.subheader("🎙️ Voice Input (Unavailable on Azure Deployment)")
    st.info("Voice input is available when running locally, but not on Azure deployment.")

# OCR section
uploaded_file = st.file_uploader("Or upload an image (e.g., poster or brochure) to extract text:", type=["png", "jpg", "jpeg"])
extracted_text = ""
cv_key = os.getenv("AZURE_CV_KEY")
cv_endpoint = os.getenv("AZURE_CV_ENDPOINT")
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

# Combine user input
final_text = user_text or extracted_text

# Analyze Key Phrases
language_key = os.getenv("AZURE_LANGUAGE_KEY")
language_endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT")
if final_text and language_key and language_endpoint:
    try:
        client = TextAnalyticsClient(endpoint=language_endpoint, credential=AzureKeyCredential(language_key))
        response = client.extract_key_phrases([final_text])[0]

        if not response.is_error:
            key_phrases = response.key_phrases
            st.subheader("🔑 Key Phrases Identified:")
            for phrase in key_phrases:
                st.write(f"- {phrase}")

            # --- Rule-Based Career Recommendations ---
            st.subheader("🧭 Career Suggestions (Rule-Based):")
            suggestions = recommend_career(key_phrases)
            for s in suggestions:
                st.success(s)

            # --- GPT Career Suggestions ---
            st.subheader("🧠 GPT Career Suggestions:")
            gpt_response = get_career_suggestions(final_text)
            st.success(gpt_response)

    except Exception as e:
        st.error(f"Text Analytics Error: {str(e)}")
else:
    if not (language_key and language_endpoint):
        st.error("⚠️ Azure Text Analytics credentials are missing.")
