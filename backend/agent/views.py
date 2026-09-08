import hashlib
import uuid

from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from agent.claude import AgentUnavailable, ask
from agent.models import InterviewLog
from agent.serializers import InterviewRequestSerializer
from agent.throttling import InterviewRateThrottle


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

        InterviewLog.objects.create(
            session_id=session_id,
            question=data["question"],
            answer=answer,
            ip_hash=hash_ip(request),
        )

        return Response({"answer": answer, "session_id": str(session_id)})


def health(request):
    """Liveness probe for Render."""
    return JsonResponse({"status": "ok"})
