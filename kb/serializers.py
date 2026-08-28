"""Serializers for the intake API."""

from rest_framework import serializers

from .models import IntakeSession, IntakeTurn, Question


class IntakeSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntakeSession
        fields = [
            "id", "started_at", "completed_at", "question_set_version",
        ]
        read_only_fields = fields


class IntakeTurnSerializer(serializers.ModelSerializer):
    """A turn as read back. ``question_key`` comes from the FK; the
    ``question_text`` beside it is the snapshot taken when it was asked, so
    the two can legitimately differ once a question is reworded."""

    question_key = serializers.SlugField(
        source="question.key", read_only=True, default=None
    )
    source_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = IntakeTurn
        fields = [
            "id", "session", "question_key", "question_text", "answer_text",
            "asked_at", "answered_at", "source_id",
        ]
        read_only_fields = fields


class TurnCreateSerializer(serializers.Serializer):
    """Input for POST /api/intake/turns/.

    Resolves ``question_key`` against the session's own question set, so a
    key from a different set is rejected rather than silently accepted.
    """

    session = serializers.PrimaryKeyRelatedField(
        queryset=IntakeSession.objects.all()
    )
    question_key = serializers.SlugField()
    # trim_whitespace=False so a whitespace-only body reaches the validator
    # below and gets that message, rather than DRF's generic blank error.
    answer_text = serializers.CharField(trim_whitespace=False)

    def validate_answer_text(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "An answer is required; whitespace alone is not an answer."
            )
        return value

    def validate(self, attrs):
        session = attrs["session"]
        if session.completed_at is not None:
            raise serializers.ValidationError(
                {"session": "This session is already completed."}
            )

        try:
            attrs["question"] = Question.objects.get(
                key=attrs["question_key"],
                question_set_version=session.question_set_version,
                active=True,
            )
        except Question.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "question_key": (
                        f"'{attrs['question_key']}' is not an active question "
                        f"in set '{session.question_set_version}'."
                    )
                }
            )
        return attrs
