import edge_tts
import asyncio
import streamlit as st
import tempfile
import os
import re
from langdetect import detect


# Indian voices
VOICE_MAP = {
    "en": "en-IN-PrabhatNeural",
    "te": "te-IN-MohanNeural",
    "hi": "hi-IN-MadhurNeural",
    "ta": "ta-IN-ValluvarNeural",
    "kn": "kn-IN-GaganNeural",
    "mr": "mr-IN-ManoharNeural" # Added Marathi
}


# Detect language
def detect_lang(text):
    try:
        return detect(text)
    except:
        return "en"


# Remove symbols for speech
def clean_text(text):
    # Remove special symbols
    text = re.sub(r"[₹:;,_\-*/=+<>|{}\[\]()]", " ", text)
    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# Internal async TTS
async def _speak(text, lang):
    voice = VOICE_MAP.get(lang, VOICE_MAP["en"])
    communicate = edge_tts.Communicate(text, voice)
    
    # Create temp file
    # We use delete=False then remove manualy because windows can handle opened temp files differently
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        file_path = f.name

    await communicate.save(file_path)
    return file_path


# Main function (Single audio)
def speak_full(text, lang="en"):
    
    # We need a loop for async
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        try:
            clean = clean_text(text)
            file_path = await _speak(clean, lang)
            
            # Display audio player
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    st.audio(f.read(), format="audio/mp3")
                
                # Cleanup
                os.remove(file_path)

        except Exception as e:
            print("TTS Error:", e)

    loop.run_until_complete(run())
    loop.close()
