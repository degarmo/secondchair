"""Clear the knowledge base, keeping the question bank.

The seeded demo content is fictional. It has to go before a real intake,
or invented claims about a made-up candidate end up cited alongside real
ones.

Deletion order matters: knowledge records PROTECT their Source, so they go
first and Sources go last.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from kb.models import (
    Constraint,
    Extraction,
    IntakeSession,
    IntakeTurn,
    Project,
    Role,
    Skill,
    Source,
    Story,
)

# Knowledge records first (they PROTECT Source), then the intake graph,
# then the Sources nothing points at any more. Question is absent on
# purpose: the bank survives a reset.
DELETION_ORDER = (
    Role, Project, Story, Skill, Constraint,
    Extraction, IntakeTurn, IntakeSession, Source,
)


class Command(BaseCommand):
    help = (
        "Delete all intake and knowledge records. Questions are kept. "
        "Requires --confirm."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Actually delete. Without it, only report what would go.",
        )

    def handle(self, *args, **options):
        counts = {m.__name__: m.objects.count() for m in DELETION_ORDER}
        total = sum(counts.values())

        if not options["confirm"]:
            self.stdout.write("Dry run. Nothing has been deleted.")
            self.stdout.write("Would delete:")
            for name, count in counts.items():
                self.stdout.write(f"  {name:<14} {count}")
            self.stdout.write(f"  {'TOTAL':<14} {total}")
            self.stdout.write(
                self.style.WARNING(
                    "Re-run with --confirm to delete. Questions are never "
                    "touched by this command."
                )
            )
            return

        with transaction.atomic():
            deleted = {}
            for model in DELETION_ORDER:
                count, _ = model.objects.all().delete()
                deleted[model.__name__] = count

        self.stdout.write("Deleted:")
        for name, count in deleted.items():
            self.stdout.write(f"  {name:<14} {count}")
        self.stdout.write(
            self.style.SUCCESS(
                f"Knowledge base cleared. "
                f"{sum(deleted.values())} row(s) removed across "
                f"{len(deleted)} model(s); the question bank is untouched."
            )
        )
