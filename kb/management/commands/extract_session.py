"""Run extraction across every answered turn in a session.

Idempotent: a turn that already has extractions is left alone, so a re-run
after a partial failure picks up only what is missing.
"""

from django.core.management.base import BaseCommand, CommandError

from kb.models import IntakeSession
from kb.services.extraction import ExtractionError, extract_from_turn


class Command(BaseCommand):
    help = "Extract proposed records from every answered turn in a session."

    def add_arguments(self, parser):
        parser.add_argument("session_id", type=int)

    def handle(self, *args, **options):
        session_id = options["session_id"]
        try:
            session = IntakeSession.objects.get(pk=session_id)
        except IntakeSession.DoesNotExist:
            raise CommandError(f"No intake session with id {session_id}.")

        turns = (
            session.turns.exclude(answer_text__isnull=True)
            .exclude(answer_text="")
            .filter(extractions__isnull=True)
            .order_by("pk")
        )

        total = 0
        processed = 0
        for turn in turns:
            try:
                created = extract_from_turn(turn)
            except ExtractionError as exc:
                raise CommandError(f"Turn {turn.pk}: {exc}") from exc
            processed += 1
            total += len(created)
            self.stdout.write(
                f"  turn {turn.pk}: {len(created)} extraction(s) "
                f"[{', '.join(e.target_model for e in created) or 'none'}]"
            )

        if not processed:
            self.stdout.write(
                "No answered turns without extractions; nothing to do."
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Session {session_id}: {total} extraction(s) created across "
                f"{processed} turn(s)."
            )
        )
