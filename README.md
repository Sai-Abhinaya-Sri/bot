# WeNext AI Bot

A multilingual AI assistant for WeNext — answers questions about WeNext features, campaigns, automation, and CRM using your documentation as a knowledge base. Supports text and voice input in English, Hindi, Telugu, Tamil, and other Indian languages.

## Features

- **Multilingual support** — English, Hindi, Telugu, Tamil, Kannada, and more, including Romanized (Hinglish, Tenglish) variants
- **Voice input** — speak your question via the mic button; transcribed using Sarvam STT
- **Text-to-speech** — listen to any assistant response using Sarvam Bulbul v3
- **RAG pipeline** — answers grounded in your uploaded PDF/Excel/Word documents
- **Workflow agent** — guides users through building WhatsApp automation workflows
- **Smart routing** — automatically routes to the right agent based on query intent

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| LLM | Sarvam 30B (`sarvam-30b`) |
| STT | Sarvam Saarika v2.5 |
| TTS | Sarvam Bulbul v3 |
| Embeddings | `all-MiniLM-L6-v2` (sentence-transformers) |
| Vector DB | ChromaDB |
| Language detection | langdetect |

## Project Structure

```
├── app.py          # Streamlit UI, session state, voice/text input handling
├── agents.py       # LLM caller, TTS, smart agent, workflow agent
├── router.py       # Query routing — decides which agent handles the request
├── language.py     # Language/script detection, translation helpers
├── vectordb.py     # Document loading, chunking, ChromaDB vector search
├── config.py       # All configuration and constants (keys loaded from .env)
├── data/           # Place your PDF, Excel, Word, or CSV documents here
├── requirements.txt
└── .env.example    # Template for required environment variables
```

## Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd <repo-folder>
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

```bash
cp .env.example .env
```

Edit `.env` and add your [Sarvam AI API key](https://dashboard.sarvam.ai):

```
SARVAM_API_KEY=your_key_here
```

### 5. Add your documents

Drop your PDF, Excel, Word, or CSV files into the `data/` folder. The bot will load and index them on startup.

### 6. Run the app

```bash
streamlit run app.py
```

## Usage

- **Text**: Type your question in the chat input at the bottom
- **Voice**: Click the 🎤 mic button, speak, then click stop
- **Listen**: Click 🔊 on any assistant message to hear it read aloud
- Ask in any supported language — the bot detects your language automatically and responds in kind

## Supported Languages

English, Hindi, Telugu, Tamil, Kannada, Malayalam, Marathi, Gujarati, Bengali, Punjabi, Urdu, Odia, Assamese — including Romanized (code-mixed) variants like Hinglish and Tenglish.
