from django.conf import settings
from rest_framework import serializers


class HistoryTurnSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["user", "assistant"])
    content = serializers.CharField(max_length=4000, allow_blank=False)


class InterviewRequestSerializer(serializers.Serializer):
    question = serializers.CharField(
        max_length=settings.INTERVIEW_QUESTION_MAX_LENGTH,
        allow_blank=False,
        trim_whitespace=True,
    )
    history = HistoryTurnSerializer(many=True, required=False, default=list)
    # Optional: sent back by the client so a visitor's follow-up questions
    # group under one session in the log.
    session_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_history(self, value):
        """Keep the last N turns, and make the list valid for the API.

        The Messages API requires the first message to be from the user, so
        any leading assistant turns are dropped after trimming.
        """
        turns = value[-settings.INTERVIEW_HISTORY_LIMIT :]
        while turns and turns[0]["role"] != "user":
            turns = turns[1:]
        return turns


class InterviewResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()
    session_id = serializers.UUIDField()
