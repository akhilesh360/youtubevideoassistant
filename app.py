import streamlit as st
import os
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re

# Load environment variables (from GitHub environment secrets)
api_key = os.environ.get("DEEPSEEK_API_KEY")
http_proxy = os.environ.get("HTTP_PROXY")
https_proxy = os.environ.get("HTTPS_PROXY")

# Validate secrets
if not api_key or not http_proxy or not https_proxy:
    raise ValueError("Missing required environment variables: DEEPSEEK_API_KEY, HTTP_PROXY, HTTPS_PROXY")

# Configure DeepSeek API
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# Proxy dictionary for requests
proxies = {
    "http": http_proxy,
    "https": https_proxy,
}

# Prompts
summary_prompt = """You are a YouTube video summarizer. You will summarize the transcript text 
and provide the important points within 250 words. Please provide the summary of the text given here: """

qa_prompt = """You are a helpful assistant. Use the provided summary to answer the user's question accurately and concisely. 
Summary: {summary}

Question: {question}

Answer:"""

# Extract YouTube video ID
def extract_video_id(youtube_url):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, youtube_url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid YouTube URL format. Could not extract video ID.")

# Get transcript with proxy support
def extract_transcript_details(youtube_video_url):
    try:
        video_id = extract_video_id(youtube_video_url)
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id, proxies=proxies)
        transcript = " ".join([entry["text"] for entry in transcript_text])
        return transcript

    except TranscriptsDisabled:
        raise ValueError("Subtitles are disabled for this video.")
    except NoTranscriptFound:
        raise ValueError("No transcript found for this video.")
    except Exception as e:
        if "RequestBlocked" in str(e) or "IPBlocked" in str(e):
            raise ValueError("YouTube is blocking your IP. Use a residential proxy.")
        raise e

# Generate summary with DeepSeek
def generate_deepseek_summary(transcript_text, prompt):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": prompt + transcript_text},
        ],
        stream=False,
    )
    return response.choices[0].message.content

# Answer questions using summary
def answer_question(summary, question):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": qa_prompt.format(summary=summary, question=question)},
        ],
        stream=False,
    )
    return response.choices[0].message.content

# --- Streamlit App UI ---
st.markdown("<h1 style='text-align: center;'>YouTube Video Assistant</h1>", unsafe_allow_html=True)

if "summary" not in st.session_state:
    st.session_state.summary = None

youtube_link = st.text_input("Enter YouTube Video Link:")

if youtube_link:
    try:
        video_id = extract_video_id(youtube_link)
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)
    except ValueError as ve:
        st.error(str(ve))

if st.button("Get Detailed Notes"):
    try:
        with st.spinner("Extracting transcript..."):
            transcript_text = extract_transcript_details(youtube_link)

        if transcript_text:
            with st.spinner("Generating summary..."):
                st.session_state.summary = generate_deepseek_summary(transcript_text, summary_prompt)

            st.markdown("## Detailed Notes:")
            st.write(st.session_state.summary)

    except ValueError as ve:
        st.error(str(ve))
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

# Question answering section
if st.session_state.summary:
    st.markdown("---")
    st.markdown("## Ask a Question")

    user_question = st.text_input("Enter your question about the video:", key="question_input")

    if st.button("Submit Question"):
        if user_question.strip():
            try:
                with st.spinner("Fetching answer..."):
                    answer = answer_question(st.session_state.summary, user_question)

                st.markdown("### Answer:")
                st.text_area(label="Answer:", value=answer, height=150)

            except Exception as e:
                st.error(f"An error occurred while answering your question: {e}")
        else:
            st.warning("Please enter a valid question before submitting.")
