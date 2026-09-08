import hashlib
import uuid

from django.conf import settings
from django.core.cache import cache
from django.http import Http404, HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from agent.claude import AgentUnavailable, ask
from agent.models import InterviewLog
from agent.serializers import InterviewRequestSerializer
from agent.speech import SpeechUnavailable, speech_enabled, synthesize
from agent.throttling import InterviewRateThrottle, SpeechRateThrottle


def client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def hash_ip(request) -> str:
    """Salted hash of the caller's address, so logs hold no raw IPs."""
    ip = client_ip(request)
    if not ip:
        return ""
    return hashlib.sha256(f"{settings.SECRET_KEY}:{ip}".encode()).hexdigest()


class InterviewView(APIView):
    """POST a question about Cory, get an answer grounded in the knowledge base."""

    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes = [InterviewRateThrottle]

    def post(self, request):
        serializer = InterviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        session_id = data.get("session_id") or uuid.uuid4()

        try:
            answer = ask(data["question"], data["history"])
        except AgentUnavailable:
            return Response(
                {
                    "detail": (
                        "The agent is having trouble reaching the model right "
                        f"now. Email Cory at {settings.CONTACT_EMAIL} and he'll "
                        "answer himself."
                    ),
                    "code": "agent_unavailable",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        log = InterviewLog.objects.create(
            session_id=session_id,
            question=data["question"],
            answer=answer,
            ip_hash=hash_ip(request),
        )

        return Response(
            {
                "answer": answer,
                "session_id": str(session_id),
                # The id the client passes to the speech endpoint, and whether
                # offering a play button is worth it at all.
                "log_id": log.id,
                "speech_available": speech_enabled(),
            }
        )


class AnswerSpeechView(APIView):
    """GET audio of an answer the agent has already given.

    Addressed by log id rather than by text on purpose: this endpoint can
    only ever speak sentences the agent itself produced, so it cannot be
    turned into free text-to-speech billed to Cory.
    """

    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes = [SpeechRateThrottle]

    def get(self, request, log_id: int):
        if not speech_enabled():
            return Response(
                {
                    "detail": "Spoken answers are not available right now.",
                    "code": "speech_unavailable",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            log = InterviewLog.objects.only("id", "answer").get(pk=log_id)
        except InterviewLog.DoesNotExist:
            raise Http404("No such answer.")

        cache_key = f"speech:{settings.ELEVENLABS_VOICE_ID}:{log.id}"
        audio = cache.get(cache_key)

        if audio is None:
            try:
                audio = synthesize(log.answer)
            except SpeechUnavailable:
                return Response(
                    {
                        "detail": "That answer could not be spoken. Read it above.",
                        "code": "speech_unavailable",
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            cache.set(cache_key, audio, settings.SPEECH_CACHE_SECONDS)

        response = HttpResponse(audio, content_type="audio/mpeg")
        response["Content-Length"] = str(len(audio))
        response["Cache-Control"] = "private, max-age=3600"
        return response


def health(request):
    """Liveness probe for Render."""
    return JsonResponse({"status": "ok"})
