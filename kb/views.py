"""Intake API.

Deterministic throughout -- no model calls anywhere in this module. The
intake loop is plumbing, and keeping it free of LLM calls means a failure
in extraction or generated follow-ups later is unambiguously in the model
layer rather than here.

Authentication is deliberately deferred: this is a single-user demo, so
every endpoint below is open. Nothing here inspects a user, so adding auth
later is a matter of applying permission classes, not restructuring.
"""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Audience, IntakeSession, IntakeTurn, Question, Source
from .services.answering import answer_question
from .services.extraction import ExtractionError
from .serializers import (
    IntakeSessionSerializer,
    IntakeTurnSerializer,
    TurnCreateSerializer,
)

QUESTION_SET_VERSION = "v1"

# A turn counts as answered only when it carries a non-empty answer. A turn
# that was asked but not yet answered must stay in the queue.
ANSWERED = ~Q(answer_text__isnull=True) & ~Q(answer_text="")


def active_questions(version):
    return Question.objects.filter(active=True, question_set_version=version)


def answered_turns(session):
    return session.turns.filter(ANSWERED)


@api_view(["POST"])
def create_session(request):
    """POST /api/intake/sessions/ -- start an intake session."""
    session = IntakeSession.objects.create(
        question_set_version=QUESTION_SET_VERSION
    )
    return Response(
        IntakeSessionSerializer(session).data, status=status.HTTP_201_CREATED
    )


@api_view(["GET"])
def next_question(request, pk):
    """GET /api/intake/sessions/<id>/next/ -- the next unanswered question.

    Exhausting the set is a normal outcome, not a missing resource, so it
    returns 200 with ``done`` rather than a 404.
    """
    session = get_object_or_404(IntakeSession, pk=pk)
    questions = active_questions(session.question_set_version)

    answered = answered_turns(session)
    answered_ids = answered.filter(question__isnull=False).values_list(
        "question_id", flat=True
    )
    question = questions.exclude(pk__in=answered_ids).order_by(
        "priority", "pk"
    ).first()

    if question is None:
        return Response({"done": True})

    return Response(
        {
            "question_key": question.key,
            "text": question.text,
            "category": question.category,
            # 1-based index across the whole set: how many are done, plus
            # this one.
            "position": answered.count() + 1,
            "total": questions.count(),
        }
    )


@api_view(["POST"])
def create_turn(request):
    """POST /api/intake/turns/ -- record an answer.

    Re-answering a question updates the existing turn in place. That is what
    keeps a correction from minting a second Source and leaving the first
    one citable but stale.
    """
    serializer = TurnCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    session = data["session"]
    question = data["question"]

    turn, created = IntakeTurn.objects.get_or_create(
        session=session,
        question=question,
        defaults={
            "question_text": question.text,
            "answer_text": data["answer_text"],
        },
    )
    if not created:
        turn.answer_text = data["answer_text"]
        # save() mints a Source only when there isn't one, so an update
        # keeps the original.
        turn.save()

    return Response(
        IntakeTurnSerializer(turn).data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["POST"])
def complete_session(request, pk):
    """POST /api/intake/sessions/<id>/complete/ -- close the session."""
    session = get_object_or_404(IntakeSession, pk=pk)

    # Completing twice keeps the first timestamp; the summary is unchanged
    # either way.
    if session.completed_at is None:
        session.completed_at = timezone.now()
        session.save(update_fields=["completed_at"])

    answered = answered_turns(session)
    total = active_questions(session.question_set_version).count()
    sources = Source.objects.filter(intake_turn__session=session).count()

    return Response(
        {
            "session": session.pk,
            "completed_at": session.completed_at,
            "turns_answered": answered.count(),
            "questions_skipped": total - answered.count(),
            "sources_created": sources,
        }
    )


@api_view(["GET"])
def transcript(request, pk):
    """GET /api/intake/sessions/<id>/transcript/ -- the citable record.

    Ordered by ``asked_at``, which is the order the candidate met the
    questions in. This is what the answering layer will cite against.
    """
    session = get_object_or_404(IntakeSession, pk=pk)
    turns = session.turns.select_related("question", "source").order_by(
        "asked_at", "pk"
    )
    return Response(
        {
            "session": session.pk,
            "count": turns.count(),
            "turns": IntakeTurnSerializer(turns, many=True).data,
        }
    )


@api_view(["POST"])
def ask(request):
    """POST /api/ask/ -- answer a question about the candidate.

    ``audience`` is a request parameter because the demo has no auth. In
    anything real it would come from the session; what is being exercised
    here is that the filter runs in the query, not in the prompt.
    """
    question = (request.data.get("question") or "").strip()
    if not question:
        return Response(
            {"detail": "A question is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    audience = request.data.get("audience") or Audience.RECRUITER
    if audience not in Audience.values:
        return Response(
            {"detail": f"Unknown audience '{audience}'. Expected one of: "
                       f"{', '.join(Audience.values)}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        return Response(answer_question(question, audience))
    except ExtractionError as exc:
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class VoicePage(TemplateView):
    """The spoken interface. Speech recognition and synthesis both run in
    the browser, so no audio ever leaves the machine -- only the transcript
    is sent, and only to answer against the knowledge base."""

    template_name = "kb/ask.html"
