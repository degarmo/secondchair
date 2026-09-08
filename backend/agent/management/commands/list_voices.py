"""Print the ElevenLabs voices available on the configured account.

Pick one and set ELEVENLABS_VOICE_ID to its id. Without that, the site
never offers to speak an answer.
"""

import json
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

VOICES_URL = "https://api.elevenlabs.io/v1/voices"


class Command(BaseCommand):
    help = "List ElevenLabs voices, so you can choose ELEVENLABS_VOICE_ID."

    def handle(self, *args, **options):
        if not settings.ELEVENLABS_API_KEY:
            raise CommandError("ELEVENLABS_API_KEY is not set.")

        request = urllib.request.Request(
            VOICES_URL, headers={"xi-api-key": settings.ELEVENLABS_API_KEY}
        )

        try:
            with urllib.request.urlopen(
                request, timeout=settings.ELEVENLABS_TIMEOUT_SECONDS
            ) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            raise CommandError(f"ElevenLabs returned {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise CommandError(f"Could not reach ElevenLabs: {exc.reason}") from exc

        voices = payload.get("voices", [])
        if not voices:
            self.stdout.write("No voices on this account.")
            return

        current = settings.ELEVENLABS_VOICE_ID
        for voice in voices:
            marker = " <- current" if voice.get("voice_id") == current else ""
            labels = voice.get("labels") or {}
            described = ", ".join(f"{k}: {v}" for k, v in sorted(labels.items()))
            self.stdout.write(
                f"{voice.get('voice_id')}  {voice.get('name')}"
                f"{f'  ({described})' if described else ''}{marker}"
            )
