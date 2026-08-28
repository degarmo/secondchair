"""Review and browse endpoints for the knowledge base."""

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Claim, ClaimStatus, Entity, Source
from .serializers import ClaimSerializer, EntitySerializer, SourceSerializer


class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer


class EntityViewSet(viewsets.ModelViewSet):
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer


class ClaimViewSet(viewsets.ModelViewSet):
    """The review queue. Default listing is everything; filter with
    ``?status=proposed`` to get the queue itself."""

    serializer_class = ClaimSerializer

    def get_queryset(self):
        queryset = Claim.objects.select_related("entity", "source")
        if state := self.request.query_params.get("status"):
            queryset = queryset.filter(status=state)
        return queryset

    def _set_status(self, request, pk, new_status):
        claim = self.get_object()
        claim.status = new_status
        claim.reviewed_at = timezone.now()
        claim.save(update_fields=["status", "reviewed_at"])
        return Response(self.get_serializer(claim).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._set_status(request, pk, ClaimStatus.APPROVED)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._set_status(request, pk, ClaimStatus.REJECTED)

    @action(detail=False, methods=["post"])
    def approve_all(self, request):
        """Approve a batch of proposals in one click -- the common case
        after reviewing a single interview turn."""
        ids = request.data.get("ids", [])
        if not isinstance(ids, list) or not ids:
            return Response(
                {"detail": "Provide a non-empty 'ids' list."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated = Claim.objects.filter(
            id__in=ids, status=ClaimStatus.PROPOSED
        ).update(status=ClaimStatus.APPROVED, reviewed_at=timezone.now())
        return Response({"approved": updated})
