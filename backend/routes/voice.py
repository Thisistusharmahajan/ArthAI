"""
Voice Route — /api/voice/*
Speech-to-Text: Whisper (OpenAI)
Text-to-Speech: gTTS (Google)
"""
import os
import uuid
import logging
import tempfile
from flask import Blueprint, request, jsonify, send_file, current_app

logger = logging.getLogger(__name__)
voice_bp = Blueprint("voice", __name__)


# ── Speech → Text ─────────────────────────────────────────────

@voice_bp.route("/api/voice/transcribe", methods=["POST"])
def transcribe():
    """
    Accept audio file (webm/mp3/wav/m4a), return transcribed text.
    Frontend records via MediaRecorder API and sends the blob here.
    """
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    lang = request.form.get("language", "en")   # "en" or "hi" for Hindi

    # Save to temp file
    ext = os.path.splitext(audio_file.filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        transcript = _transcribe_whisper(tmp_path, lang)
        return jsonify({"transcript": transcript, "language": lang})
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _transcribe_whisper(audio_path: str, language: str = "en") -> str:
    try:
        import whisper
    except ImportError:
        raise RuntimeError(
            "Whisper is not installed. Voice input requires PyTorch + Whisper.\n"
            "Install steps:\n"
            "  1. Visit https://pytorch.org/get-started/locally/ and install PyTorch for your OS\n"
            "  2. Run: pip install -r requirements-voice.txt\n"
            "In the meantime, please type your query instead."
        )
    try:
        model = _get_whisper_model()
        lang_code = "hi" if language == "hi" else "en"
        result = model.transcribe(audio_path, language=lang_code, fp16=False)
        return result.get("text", "").strip()
    except Exception as e:
        raise RuntimeError(f"Whisper transcription failed: {e}")


_whisper_model = None
def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        _whisper_model = whisper.load_model("base")   # Use "small" or "medium" for better accuracy
        logger.info("Whisper model loaded (base)")
    return _whisper_model


# ── Text → Speech ─────────────────────────────────────────────

@voice_bp.route("/api/voice/speak", methods=["POST"])
def speak():
    """
    Accept text, return MP3 audio file.
    Frontend plays it with HTML5 Audio API.
    """
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    lang = data.get("language", "en")   # "en" or "hi"

    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Truncate very long responses for TTS
    if len(text) > 1000:
        text = text[:1000] + "... Please read the full response on screen."

    try:
        audio_path = _text_to_speech(text, lang)
        return send_file(
            audio_path,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="response.mp3"
        )
    except Exception as e:
        logger.error(f"TTS error: {e}", exc_info=True)
        return jsonify({"error": f"Text-to-speech failed: {str(e)}"}), 500


def _text_to_speech(text: str, language: str = "en") -> str:
    from config import Config
    try:
        from gtts import gTTS
        lang_code = "hi" if language == "hi" else "en"
        tld = "co.in" if lang_code == "en" else "com"   # Indian English accent
        tts = gTTS(text=text, lang=lang_code, tld=tld, slow=False)
        out_path = os.path.join(Config.EXPORT_DIR, f"tts_{uuid.uuid4().hex}.mp3")
        tts.save(out_path)
        return out_path
    except ImportError:
        raise RuntimeError("gTTS not installed. Run: pip install gTTS")


# ── Language detection ────────────────────────────────────────

@voice_bp.route("/api/voice/detect-language", methods=["POST"])
def detect_language():
    """Simple language detection from text (Hindi vs English)."""
    data = request.get_json() or {}
    text = data.get("text", "")
    # Very basic check: count Devanagari characters
    devanagari_count = sum(1 for ch in text if '\u0900' <= ch <= '\u097F')
    lang = "hi" if devanagari_count > len(text) * 0.2 else "en"
    return jsonify({"language": lang, "devanagari_chars": devanagari_count})
