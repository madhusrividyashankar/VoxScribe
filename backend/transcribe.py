# VoiceNote UK - Audio transcription using faster-whisper
# Uses the base model on CPU with int8 quantisation for speed.
# The model is loaded once at module level and reused across requests.

from faster_whisper import WhisperModel

# Global model instance — loaded lazily on first request
_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    """Load (or return cached) the faster-whisper base model."""
    global _model
    if _model is None:
        # "base" gives a good accuracy/speed balance and handles all accents well
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe an audio file and return the full text transcript.

    Args:
        audio_path: Absolute path to the audio file (mp3, wav, m4a, flac, ogg).

    Returns:
        The raw transcript as a single plain-text string.
    """
    model = _get_model()

    # beam_size=5 gives better accuracy than the default (beam_size=1)
    segments, _info = model.transcribe(audio_path, beam_size=5)

    # Concatenate all segment texts into one string
    transcript = " ".join(segment.text.strip() for segment in segments)
    return transcript.strip()
