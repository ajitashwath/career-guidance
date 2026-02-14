"""
Voice service using ElevenLabs for text-to-speech generation.
"""

from io import BytesIO
from typing import IO, Iterator

from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

from app.core.config import get_settings


def get_elevenlabs_client() -> ElevenLabs:
    """Get configured ElevenLabs client."""
    settings = get_settings()
    return ElevenLabs(api_key=settings.elevenlabs_api_key)


def generate_audio(text: str, voice_id: str = "JBFqnCBsd6RMkjVDRZzb") -> Iterator[bytes]:
    """
    Generate audio from text using ElevenLabs.
    
    Args:
        text: The text to convert to speech.
        voice_id: The voice ID to use (default: 'JBFqnCBsd6RMkjVDRZzb' - George).
        
    Returns:
        Iterator[bytes]: Stream of audio data.
    """
    client = get_elevenlabs_client()
    
    audio_stream = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_monolingual_v1"
    )
    
    return audio_stream
