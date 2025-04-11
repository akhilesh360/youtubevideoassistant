import streamlit as st
import random
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re

# --- 🔐 DeepSeek API Key (still from Streamlit secrets) ---
api_key = st.secrets["DEEPSEEK_API_KEY"]

# --- 🔁 Proxy Setup ---
proxy_list = [
    "38.153.152.244:9594",
    "86.38.234.176:6630",
    "173.211.0.148:6641",
    "161.123.152.115:6360",
    "216.10.27.159:6837",
    "154.36.110.199:6853",
    "45.151.162.198:6600",
    "185.199.229.156:7492",
    "185.199.228.220:7300",
    "185.199.231.45:8382",
]

PROXY_USER = "cbsiwzom"
PROXY_PASS = "lgusaqqp7vwr"

def get_random_proxy():
    raw = random.choice(proxy_list)
    return {
        "http": f"http://{PROXY_USER}:{PROXY_PASS}@{raw}",
        "https": f"http://{PROXY_USER}:{PROXY_PASS}@{raw}",
    }

# --- DeepSeek API Client ---
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# --- Prompts ---
summary_prompt = """You are a YouTube video summarizer. You will summarize the transcript text 
and provide the important points within 250 words. Please provide the summary of the text given here: """

qa_prompt = """You are a helpful assistant. Use the provided summary to answer the user's question accurately and concisely. 
Summary: {summary}

Question: {question}

Answer:"""

# --- Helper Functions ---
def extract_video_id(youtube_url):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, youtube_url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid YouTube URL format. Could not extract video ID.")

def extract_transcript_details(youtube_video_url):
    try:
        video_id = extract_video_id(youtube_video_url)
        proxies = get_random_proxy()  # 🔁 Use random proxy
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id, proxies=proxies)
        transcript = " ".join([entry["text"] for entry in transcript_text])
        return transcript

    except TranscriptsDisabled:
        raise ValueError("Subtitles are disabled for this video.")
    except NoTranscriptFound:
        raise ValueError("No transcript found for this video.")
    except Exception as e:
        if "RequestBlocked" in str(e) or "IPBlocked" in str(e):
            raise ValueError("YouTube is blocking your IP. Try refreshing or using more proxies.")
        raise e

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

# --- Streamlit UI ---
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

# --- Q&A Section ---
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
