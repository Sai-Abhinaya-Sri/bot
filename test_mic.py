"""
Quick mic test — run with: streamlit run test_mic.py
Records audio and plays it back so you can confirm the mic is working.
"""
import streamlit as st
from streamlit_mic_recorder import mic_recorder

st.title("🎤 Mic Test")
st.write("Click Start, speak for 3 seconds, click Stop. You should hear your voice played back.")

audio = mic_recorder(
    start_prompt="▶️ Start Recording",
    stop_prompt="⏹️ Stop Recording",
    format="wav",
    key="mic_test"
)

if audio:
    st.success(f"✅ Recorded! Size: {len(audio['bytes']):,} bytes | "
               f"Sample rate: {audio['sample_rate']} Hz | "
               f"Format: {audio['format']}")
    st.audio(audio["bytes"])
    
    if len(audio["bytes"]) < 5000:
        st.error("❌ Recording is too small — mic is not capturing audio. "
                 "Check browser and Windows mic permissions.")
    else:
        st.success("✅ Mic is working correctly!")
else:
    st.info("Waiting for recording...")
