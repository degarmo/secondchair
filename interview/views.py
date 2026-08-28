"""The candidate-facing interview loop."""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from kb.serializers import ClaimSerializer
from llm.client import LLMUnavailable
from llm.extract import propose
from llm.interviewer import next_question


@api_view(["POST"])
def next_prompt(request):
    """Ask the candidate the next question.

    ``recent`` is the session's turns so far, as [{question, answer}, ...].
    The client holds it -- interview sessions are not persisted, only the
    claims they produce are.
    """
    recent = [
        (turn.get("question", ""), turn.get("answer", ""))
        for turn in request.data.get("recent", [])
    ]
    try:
        return Response(next_question(recent))
    except LLMUnavailable as exc:
        return Response(
            {"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(["POST"])
def submit_answer(request):
    """Extract proposed claims from one answer, for review.

    ``rejected`` in the response holds proposals whose excerpt did not
    appear in the answer. They are surfaced, not silently dropped, so the
    filter's work is visible.
    """
    question = (request.data.get("question") or "").strip()
    answer = (request.data.get("answer") or "").strip()
    if not question or not answer:
        return Response(
            {"detail": "Both 'question' and 'answer' are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        claims, rejected = propose(question, answer)
    except LLMUnavailable as exc:
        return Response(
            {"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    return Response(
        {
            "proposed": ClaimSerializer(claims, many=True).data,
            "rejected": [
                {"text": r["text"], "excerpt": r["excerpt"],
                 "reason": "Excerpt not found in the answer."}
                for r in rejected
            ],
        }
    )
