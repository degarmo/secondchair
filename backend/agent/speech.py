"""Text to speech for the agent's answers, via ElevenLabs.

Only answers the agent has already produced are ever synthesized - see
``agent.views.AnswerSpeechView``. Nothing here accepts caller-supplied text,
because an endpoint that speaks arbitrary strings is a free TTS service
billed to Cory.

The call is made with urllib rather than a vendor SDK on purpose: it is one
POST, and adding an HTTP stack alongside the one the Anthropic SDK pins is a
deploy risk out of proportion to the convenience.
"""

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

API_ROOT = "https://api.elevenlabs.io/v1/text-to-speech"


class SpeechUnavailable(Exception):
    """Speech could not be produced: not configured, or the vendor failed."""


def speech_enabled() -> bool:
    """Whether the site can speak at all.

    The frontend asks this so it can hide the play button entirely rather
    than offer a control that always fails.
    """
    return bool(settings.ELEVENLABS_API_KEY and settings.ELEVENLABS_VOICE_ID)


def synthesize(text: str) -> bytes:
    """Return MP3 audio of ``text``, or raise SpeechUnavailable."""
    if not speech_enabled():
        raise SpeechUnavailable("ElevenLabs is not configured.")

    if len(text) > settings.SPEECH_MAX_CHARS:
        # Answers are capped at 600 model tokens, so this is a guard against
        # a future prompt change, not against visitors.
        raise SpeechUnavailable("Answer is too long to speak.")

    url = (
        f"{API_ROOT}/{settings.ELEVENLABS_VOICE_ID}"
        f"?output_format={settings.ELEVENLABS_OUTPUT_FORMAT}"
    )
    payload = json.dumps(
        {"text": text, "model_id": settings.ELEVENLABS_MODEL_ID}
    ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "xi-api-key": settings.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
    )

    try:
        with urllib.request.urlopen(
            request, timeout=settings.ELEVENLABS_TIMEOUT_SECONDS
        ) as response:
            audio = response.read()
    except urllib.error.HTTPError as exc:
        logger.warning("ElevenLabs returned %s: %s", exc.code, exc.reason)
        raise SpeechUnavailable("The voice service returned an error.") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("Could not reach ElevenLabs: %s", exc)
        raise SpeechUnavailable("The voice service could not be reached.") from exc

    if not audio:
        raise SpeechUnavailable("The voice service returned no audio.")

    return audio
