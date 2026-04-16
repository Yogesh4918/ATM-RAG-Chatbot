"""
Speech Engine — Speech-to-Text (STT) and Text-to-Speech (TTS) handlers.
STT: Uses SpeechRecognition with Google's API for Indian language support.
TTS: Uses gTTS for natural Indian voice output.
"""

import io
import speech_recognition as sr
from gtts import gTTS
import streamlit as st

from src.translations import LANGUAGES


def speech_to_text(audio_bytes: bytes, language: str = "English") -> dict:
    """
    Convert audio bytes to text using Google Speech Recognition.

    Args:
        audio_bytes: Raw audio data from st.audio_input
        language: Selected UI language key (e.g., "Hindi", "Gujarati")

    Returns: {
        "success": bool,
        "text": str,
        "error": str | None
    }
    """
    locale = LANGUAGES.get(language, LANGUAGES["English"])["stt_locale"]

    try:
        recognizer = sr.Recognizer()

        # Convert bytes to AudioData
        # st.audio_input returns WAV format by default
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)

        # Use Google STT (free, best for Indian languages)
        text = recognizer.recognize_google(audio_data, language=locale)

        return {
            "success": True,
            "text": text,
            "error": None,
        }

    except sr.UnknownValueError:
        return {
            "success": False,
            "text": "",
            "error": "Could not understand audio. Please speak clearly.",
        }
    except sr.RequestError as e:
        return {
            "success": False,
            "text": "",
            "error": f"Speech recognition service unavailable: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": f"Error processing audio: {str(e)}",
        }


def text_to_speech(text: str, language: str = "English") -> bytes | None:
    """
    Convert text to speech audio bytes using gTTS.

    Args:
        text: Text to convert to speech
        language: Selected UI language key

    Returns:
        Audio bytes (MP3 format) or None on failure
    """
    tts_code = LANGUAGES.get(language, LANGUAGES["English"])["tts_code"]

    try:
        tts = gTTS(text=text, lang=tts_code, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.read()

    except Exception as e:
        st.warning(f"TTS Error: {str(e)}")
        return None


def play_response(text: str, language: str = "English"):
    """
    Generate TTS audio and display it with autoplay in Streamlit.

    Args:
        text: Response text to speak
        language: Selected UI language key
    """
    audio_bytes = text_to_speech(text, language)
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
