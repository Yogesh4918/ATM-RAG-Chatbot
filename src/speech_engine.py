"""
Speech Engine — Text-to-Speech (TTS) handler.
STT is handled client-side via Web Speech API.
TTS uses gTTS (Google Text-to-Speech) for natural multilingual output.
Framework-agnostic: returns bytes, no UI dependencies.
"""

import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def text_to_speech(text: str, tts_code: str = "en") -> Optional[bytes]:
    """
    Convert text to speech audio bytes using gTTS (Google Text-to-Speech).

    Args:
        text: Text to convert to speech
        tts_code: Language code for gTTS (e.g., "hi", "gu", "ta")

    Returns:
        Audio bytes (MP3 format) or None on failure
    """
    if not text or not text.strip():
        return None

    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=tts_code, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.read()
    except Exception as e:
        logger.warning("TTS error (lang=%s): %s", tts_code, e)
        return None
