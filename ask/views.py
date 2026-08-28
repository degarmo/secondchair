"""The recruiter-facing endpoint."""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from kb.models import Audience
from llm.answer import answer_question
from llm.client import LLMUnavailable


@api_view(["POST"])
def ask(request):
    """Answer a question about the candidate at the caller's clearance.

    ``audience`` is a request parameter here because the demo has no auth.
    In anything real it would come from the session -- the point being
    tested is that the filter is applied in the query, not the prompt.
    """
    question = (request.data.get("question") or "").strip()
    if not question:
        return Response(
            {"detail": "A question is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    audience = request.data.get("audience", Audience.RECRUITER)
    if audience not in Audience.values:
        return Response(
            {"detail": f"Unknown audience '{audience}'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        return Response(answer_question(question, audience))
    except LLMUnavailable as exc:
        return Response(
            {"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
