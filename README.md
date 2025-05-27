# YouTube Video Assistant (Streamlit)

A Streamlit application that enables users to summarize YouTube video transcripts and perform question-answering using DeepSeek's AI API. The app extracts video transcripts via the YouTube Transcript API, summarizes content, and provides interactive Q&A functionality.

---

## Table of Contents
1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Architecture Overview](#architecture-overview)
7. [Future Improvements](#future-improvements)
8. [License](#license)

---

## Features
- **Transcript Extraction**: Retrieve subtitles from YouTube videos, handling proxies to circumvent IP restrictions.
- **Summarization**: Generate concise video summaries (≤250 words) via DeepSeek's `deepseek-chat` model.
- **Interactive Q&A**: Answer user questions based on the generated summary.
- **Session State**: Maintain summary across interactions for seamless Q&A.

## Prerequisites
- Python 3.8 or higher
- YouTube Transcript API access
- DeepSeek API key

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/<username>/youtube-video-assistant.git
   cd youtube-video-assistant
````

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Streamlit Secrets**: Add your DeepSeek API key to `.streamlit/secrets.toml`:

   ```toml
   [secrets]
   DEEPSEEK_API_KEY = "<your_api_key>"
   ```
2. **Proxy Credentials**: Ensure proxy username and password are set in `main.py` (constants `PROXY_USER` and `PROXY_PASS`).

## Usage

Run the Streamlit app locally:

```bash
streamlit run main.py
```

1. Enter a YouTube video URL.
2. Click **Get Detailed Notes** to extract and summarize the transcript.
3. After summary appears, ask questions in the Q\&A section.
4. Submit a question to receive an AI-generated answer.

## Architecture Overview

```mermaid
graph LR
  A[User Input: YouTube URL] --> B[Extract Video ID]
  B --> C[YouTube Transcript API (with proxy)]
  C --> D[Transcript Text]
  D --> E[DeepSeek Summarization]
  E --> F[Display Summary]
  F --> G[User Question Input]
  G --> H[DeepSeek Q&A]
  H --> I[Answer Display]
```

* **Proxy Pool**: Rotates through a list of HTTP proxies to avoid request blocking.
* **DeepSeek Client**: Wraps OpenAI-compatible API with base URL `https://api.deepseek.com`.

## Future Improvements

* Add error retry logic with exponential backoff for proxy failures.
* Support multiple summary lengths or summary styles.
* Integrate additional AI models or services for enhanced analysis.
* Deploy on Streamlit Cloud or custom Docker environment for production.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

```
```
