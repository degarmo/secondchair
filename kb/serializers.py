from rest_framework import serializers

from .models import Claim, Entity, Source


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ["id", "kind", "label", "excerpt", "uri", "captured_at"]
        read_only_fields = ["captured_at"]


class EntitySerializer(serializers.ModelSerializer):
    period = serializers.CharField(read_only=True)

    class Meta:
        model = Entity
        fields = ["id", "kind", "title", "org", "start", "end", "period"]


class ClaimSerializer(serializers.ModelSerializer):
    source = SourceSerializer(read_only=True)
    source_id = serializers.PrimaryKeyRelatedField(
        queryset=Source.objects.all(), source="source", write_only=True
    )
    entity = EntitySerializer(read_only=True)
    entity_id = serializers.PrimaryKeyRelatedField(
        queryset=Entity.objects.all(),
        source="entity",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Claim
        fields = [
            "id", "text", "entity", "entity_id", "source", "source_id",
            "visibility", "status", "confidence", "created_at", "reviewed_at",
        ]
        read_only_fields = ["created_at", "reviewed_at"]
