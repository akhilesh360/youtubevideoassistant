import streamlit as st
from dotenv import load_dotenv
import os
from openai import OpenAI  # Using OpenAI-compatible SDK for DeepSeek
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re  # For regular expressions to extract video IDs

# Load environment variables
load_dotenv()

# Configure DeepSeek API
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("DEEPSEEK_API_KEY environment variable not set")

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# Prompt for summarization
summary_prompt = """You are a YouTube video summarizer. You will summarize the transcript text 
and provide the important points within 250 words. Please provide the summary of the text given here: """

# Prompt for answering questions based on the summary
qa_prompt = """You are a helpful assistant. Use the provided summary to answer the user's question accurately and concisely. 
Summary: {summary}

Question: {question}

Answer:"""

# Function to extract YouTube video ID from various URL formats
def extract_video_id(youtube_url):
    try:
        # Regular expression to match various YouTube URL formats
        regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
        match = re.search(regex, youtube_url)
        if match:
            return match.group(1)
        else:
            raise ValueError("Invalid YouTube URL format. Could not extract video ID.")
    except Exception as e:
        raise e

# Function to extract transcript details from YouTube videos
def extract_transcript_details(youtube_video_url):
    try:
        video_id = extract_video_id(youtube_video_url)
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)

        # Combine all transcript entries into a single string
        transcript = " ".join([entry["text"] for entry in transcript_text])

        return transcript

    except TranscriptsDisabled:
        raise ValueError("Subtitles are disabled for this video.")
    except NoTranscriptFound:
        raise ValueError("No transcript found for this video.")
    except Exception as e:
        raise e

# Function to generate summary using DeepSeek API
def generate_deepseek_summary(transcript_text, prompt):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt + transcript_text},
            ],
            stream=False,
        )
        return response.choices[0].message.content

    except Exception as e:
        raise e

# Function to answer questions based on the summary using DeepSeek API
def answer_question(summary, question):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": qa_prompt.format(summary=summary, question=question)},
            ],
            stream=False,
        )
        return response.choices[0].message.content

    except Exception as e:
        raise e

# Streamlit UI
st.markdown("<h1 style='text-align: center;'>YouTube Video Assistant</h1>", unsafe_allow_html=True)

# Initialize session state for storing the summary
if "summary" not in st.session_state:
    st.session_state.summary = None  # Initialize as None

youtube_link = st.text_input("Enter YouTube Video Link:")

if youtube_link:
    try:
        # Extract and display thumbnail image
        video_id = extract_video_id(youtube_link)
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)

    except ValueError as ve:
        st.error(str(ve))

if st.button("Get Detailed Notes"):
    try:
        # Extract transcript from the provided YouTube link
        with st.spinner("Extracting transcript..."):
            transcript_text = extract_transcript_details(youtube_link)

        # Generate summary using DeepSeek API and store it in session state
        if transcript_text:
            with st.spinner("Generating summary..."):
                st.session_state.summary = generate_deepseek_summary(transcript_text, summary_prompt)
            
            # Display the summary
            st.markdown("## Detailed Notes:")
            st.write(st.session_state.summary)

    except ValueError as ve:
        st.error(str(ve))
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

# Ask Question Section (only if a summary is available)
if st.session_state.summary:  # Check if a summary is stored in session state
    st.markdown("---")
    st.markdown("## Ask a Question")
    
    # Input field for user question
    user_question = st.text_input("Enter your question about the video:", key="question_input")
    
    # Submit button for asking questions and displaying results in a text area
    if st.button("Submit Question"):
        if user_question.strip():  # Ensure question is not empty or whitespace
            try:
                with st.spinner("Fetching answer..."):
                    answer = answer_question(st.session_state.summary, user_question)
                
                # Display the answer in a text field below
                st.markdown("### Answer:")
                st.text_area(label="Answer:", value=answer, height=150)

            except Exception as e:
                st.error(f"An error occurred while answering your question: {e}")
        else:
            st.warning("Please enter a valid question before submitting.")
