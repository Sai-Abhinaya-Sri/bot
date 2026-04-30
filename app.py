import streamlit as st
import requests
from streamlit_mic_recorder import mic_recorder

from config import DATA_FOLDER, SARVAM_STT_URL, SARVAM_API_KEY, STT_MODEL
from language import detect_user_language_and_script
from vectordb import VectorDB, load_files
from router import agent_router, route_request
from agents import text_to_speech


# ================= PAGE SETUP =================

st.set_page_config(page_title="🤖 WeNext AI Bot", layout="wide")

# ================= FIXED LAYOUT CSS =================

st.markdown("""
<style>
/* ── Scrollable chat area with space for fixed bottom bar ── */
.main .block-container {
    padding-bottom: 90px !important;
    max-width: 860px !important;
    margin: auto !important;
}

/* ── Fix Streamlit's native bottom bar ── */
.stBottomBlockContainer {
    position: fixed !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 1000 !important;
    background-color: #0e1117 !important;
    padding: 0.5rem 4rem 0.7rem 1.5rem !important;
    border-top: 1px solid rgba(255,255,255,0.08) !important;
}

/* ── Grab the mic recorder widget (first stElementContainer in body)
      and pin it to bottom-right, overlapping the chat input bar ── */
[data-testid="stElementContainer"]:has(> div > div > button[title="Start recording"]),
[data-testid="stElementContainer"]:has(> div > div > button[title="Stop recording"]) {
    position: fixed !important;
    bottom: 0.55rem !important;
    right: 1.2rem !important;
    z-index: 1100 !important;
    width: auto !important;
}

/* ── Mic button style — round, compact ── */
button[title="Start recording"],
button[title="Stop recording"] {
    border-radius: 50% !important;
    width: 2.4rem !important;
    height: 2.4rem !important;
    min-width: unset !important;
    padding: 0 !important;
    font-size: 1.1rem !important;
    background-color: #1e2130 !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
}

button[title="Start recording"]:hover,
button[title="Stop recording"]:hover {
    background-color: #ff4b4b !important;
    border-color: #ff4b4b !important;
}

/* ── Hide the audio playback element mic_recorder adds ── */
[data-testid="stElementContainer"]:has(> div > div > button[title="Start recording"]) audio,
[data-testid="stElementContainer"]:has(> div > div > button[title="Stop recording"]) audio {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 WeNext AI Bot")


# ================= SESSION STATE =================

if "chat" not in st.session_state:
    st.session_state.chat = [{
        "role": "assistant",
        "content": (
            "Hi 👋 I'm your WeNext assistant. "
            "Ask me anything about WeNext in English, Hindi, Telugu, "
            "Tenglish, Hinglish, or any Indian language! "
            "You can also use the 🎤 mic button below to speak."
        )
    }]

if "history"       not in st.session_state: st.session_state.history       = []
if "last_voice_id" not in st.session_state: st.session_state.last_voice_id = None
if "tts_audio"     not in st.session_state: st.session_state.tts_audio     = {}  # msg_index → wav bytes
if "tts_loading"   not in st.session_state: st.session_state.tts_loading   = None # index being fetched

if "db" not in st.session_state:
    try:
        db = VectorDB()
        chunks = load_files(DATA_FOLDER)
        if chunks:
            db.load(chunks)
            st.success(f"✅ Loaded {len(chunks)} chunks from documents")
        else:
            st.warning("⚠️ No files found in data folder")
        st.session_state.db = db
    except Exception as e:
        st.error(f"❌ DB init error: {e}. Try restarting the app.")
        st.stop()


# ================= CHAT HISTORY =================

for idx, m in enumerate(st.session_state.chat):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

        # 🔊 TTS button — only on assistant messages
        if m["role"] == "assistant":
            col1, col2 = st.columns([0.08, 0.92])
            with col1:
                btn_label = "⏳" if st.session_state.tts_loading == idx else "🔊"
                if st.button(btn_label, key=f"tts_btn_{idx}",
                             help="Listen to this response",
                             disabled=(st.session_state.tts_loading == idx)):
                    st.session_state.tts_loading = idx
                    # Retrieve language_info stored alongside the message (if any)
                    lang_info = m.get("language_info") or {"language_code": "en", "language_name": "English",
                                                            "is_romanized": False, "is_mixed": False}
                    with st.spinner("🔊 Generating audio..."):
                        wav = text_to_speech(m["content"], lang_info)
                    st.session_state.tts_audio[idx]  = wav
                    st.session_state.tts_loading      = None
                    st.rerun()

            # Play audio if already generated for this message
            if idx in st.session_state.tts_audio:
                wav = st.session_state.tts_audio[idx]
                if wav:
                    with col2:
                        st.audio(wav, format="audio/wav")
                else:
                    with col2:
                        st.caption("⚠️ Audio generation failed. Try again.")


# ================= INPUT ROW (chat input + mic — both in fixed bottom bar) =================

q = st.chat_input("Type your question or use the 🎤 mic...")

# mic_recorder renders inside the bottom container alongside chat_input
with st.container():
    audio_data = mic_recorder(
        start_prompt="🎤 Start",
        stop_prompt="🛑 Stop",
        key="voice_input",
        format="wav",          # wav is more reliably decoded by Sarvam than webm
    )


# ================= HANDLE TEXT INPUT =================

if q:
    language_info = detect_user_language_and_script(q)

    st.session_state.chat.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            ans = agent_router(q, st.session_state.db, st.session_state.history, language_info)
            st.markdown(ans)

    # Store message — note the index it will occupy
    new_idx = len(st.session_state.chat)
    st.session_state.chat.append({"role": "assistant", "content": ans, "language_info": language_info})
    st.session_state.history.append({"q": q, "a": ans})

    # Auto-generate TTS so audio is ready when the page rerenders
    with st.spinner("🔊 Generating voice..."):
        wav = text_to_speech(ans, language_info)
    st.session_state.tts_audio[new_idx] = wav

    st.rerun()


if "last_voice_id" not in st.session_state:
    st.session_state.last_voice_id = None

# ================= HANDLE VOICE INPUT =================

if audio_data:
    audio_id = audio_data.get("id")

    # Skip if already processed this recording
    if audio_id == st.session_state.last_voice_id:
        st.stop()

    st.session_state.last_voice_id = audio_id

    # mic_recorder returns 'format' as bare string e.g. "webm", "wav"
    fmt      = audio_data.get("format", "wav")
    fmt_to_mime = {"webm": "audio/webm", "wav": "audio/wav",
                   "ogg": "audio/ogg",   "mp4": "audio/mp4", "mp3": "audio/mpeg"}
    mime_type   = fmt_to_mime.get(fmt, f"audio/{fmt}")
    audio_bytes = audio_data["bytes"]

    # Reject recordings that are too short to contain real speech
    # A valid 1-second wav at 16kHz/16bit = ~32000 bytes minimum
    MIN_BYTES = 10000
    if len(audio_bytes) < MIN_BYTES:
        st.warning(f"⚠️ Recording too short ({len(audio_bytes)} bytes). "
                    "Hold the 🛑 Stop button for at least 1–2 seconds after speaking.")
        st.stop()

    with st.spinner("🔊 Recognizing speech..."):
        headers = {"api-subscription-key": SARVAM_API_KEY}
        payload = {"model": STT_MODEL, "language_code": "unknown"}
        files   = [("file", (f"voice.{fmt}", audio_bytes, mime_type))]

        try:
            res = requests.post(SARVAM_STT_URL, headers=headers,
                                data=payload, files=files, timeout=30)
        except requests.exceptions.ConnectionError:
            st.error("❌ Network error: Could not connect to Sarvam API. Check your internet and try again.")
            st.stop()
        except requests.exceptions.Timeout:
            st.error("❌ Request timed out. Try again.")
            st.stop()
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)[:200]}")
            st.stop()

    if res.status_code == 200:
        transcript = res.json().get("transcript", "").strip()
        if transcript:
            language_info = detect_user_language_and_script(transcript)

            st.session_state.chat.append({"role": "user", "content": f"🎤 {transcript}"})
            with st.chat_message("user"):
                st.markdown(f"🎤 {transcript}")

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    ans = route_request(transcript, language_info,
                                        st.session_state.db, st.session_state.history)
                    st.markdown(ans)

            # Store message — note the index it will occupy
            new_idx = len(st.session_state.chat)
            st.session_state.chat.append({"role": "assistant", "content": ans, "language_info": language_info})
            st.session_state.history.append({"q": transcript, "a": ans})

            # Auto-generate TTS so audio is ready when the page rerenders
            with st.spinner("🔊 Generating voice..."):
                wav = text_to_speech(ans, language_info)
            st.session_state.tts_audio[new_idx] = wav

            st.rerun()
        else:
            st.warning(f"⚠️ Could not recognize speech (empty transcript). "
                       f"Speak clearly and try again. [fmt={fmt}, size={len(audio_bytes)}B]")
    else:
        st.error(f"❌ STT failed ({res.status_code}): {res.text[:300]}")
