"""Load a demo record so the UI can be driven without an API key.

The candidate here is fictional. The data is shaped to exercise the parts
of the system that are easy to fake and hard to get right: claims at all
three visibility levels, an entity with missing dates (so the interviewer
has a real gap to chase), and a proposed batch still sitting in the queue.
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from kb.models import (
    Claim, ClaimStatus, Entity, EntityKind, Source, SourceKind, Visibility,
)

INTERVIEW = "Interview, 21 Aug 2026"
RESUME = "riley-okafor-cv.pdf, p1"

ENTITIES = {
    "meridian": dict(
        kind=EntityKind.ROLE, title="Staff Engineer", org="Meridian Health",
        start=date(2022, 3, 1), end=None,
    ),
    "kestrel": dict(
        kind=EntityKind.ROLE, title="Senior Engineer", org="Kestrel Logistics",
        start=date(2019, 1, 1), end=date(2022, 2, 1),
    ),
    "claims-rewrite": dict(
        kind=EntityKind.PROJECT, title="Claims pipeline rewrite",
        org="Meridian Health", start=date(2023, 6, 1), end=date(2024, 2, 1),
    ),
    "degree": dict(
        kind=EntityKind.EDUCATION, title="BSc Computer Science",
        org="University of Leeds", start=None, end=date(2018, 7, 1),
    ),
}

# (entity key, claim text, verbatim excerpt, visibility, status)
RECORD = [
    ("meridian",
     "Has been a Staff Engineer at Meridian Health since March 2022.",
     "I've been at Meridian Health since March 2022, staff engineer.",
     Visibility.PUBLIC, ClaimStatus.APPROVED),
    ("meridian",
     "Leads a team of six engineers across two squads.",
     "I lead six engineers, split across two squads.",
     Visibility.PUBLIC, ClaimStatus.APPROVED),
    ("meridian",
     "Owns the platform's on-call rotation and incident review process.",
     "I own our on-call rotation and I run the incident reviews.",
     Visibility.RECRUITER, ClaimStatus.APPROVED),
    ("claims-rewrite",
     "Rewrote the claims processing pipeline over eight months, moving it "
     "from a nightly batch to streaming.",
     "The claims pipeline rewrite took eight months. We moved off a nightly "
     "batch onto streaming.",
     Visibility.PUBLIC, ClaimStatus.APPROVED),
    ("claims-rewrite",
     "Reduced claims settlement time from four days to under six hours.",
     "Settlement went from four days to under six hours.",
     Visibility.PUBLIC, ClaimStatus.APPROVED),
    ("claims-rewrite",
     "The rewrite was delivered two months later than originally planned.",
     "We were honestly about two months late on it.",
     Visibility.RECRUITER, ClaimStatus.APPROVED),
    ("kestrel",
     "Worked at Kestrel Logistics as a Senior Engineer from January 2019 to "
     "February 2022.",
     "Before that I was at Kestrel Logistics, senior engineer, 2019 to early "
     "2022.",
     Visibility.PUBLIC, ClaimStatus.APPROVED),
    ("kestrel",
     "Built the routing service that Kestrel still runs today.",
     "I built their routing service. As far as I know it's still running.",
     Visibility.PUBLIC, ClaimStatus.APPROVED),
    ("kestrel",
     "Left Kestrel after the engineering organisation was restructured and "
     "the platform team was dissolved.",
     "I left because they restructured and dissolved the platform team.",
     Visibility.PRIVATE, ClaimStatus.APPROVED),
    ("degree",
     "Holds a BSc in Computer Science from the University of Leeds, "
     "completed in 2018.",
     "BSc Computer Science, Leeds, finished 2018.",
     Visibility.PUBLIC, ClaimStatus.APPROVED),
    (None,
     "Works primarily in Python and Go, with production Kafka experience.",
     "Mostly Python and Go. A fair amount of Kafka in production.",
     Visibility.PUBLIC, ClaimStatus.APPROVED),
    (None,
     "Is looking for a role with more architectural ownership and less "
     "incident load.",
     "I want more architecture ownership and honestly less time on call.",
     Visibility.RECRUITER, ClaimStatus.APPROVED),
    (None,
     "Current base salary is £95,000.",
     "I'm on ninety-five thousand base at the moment.",
     Visibility.PRIVATE, ClaimStatus.APPROVED),
    # Still in the queue, so the review station has something to show.
    ("meridian",
     "Introduced a weekly architecture review that the platform group "
     "still runs.",
     "I started a weekly architecture review. They still do it.",
     Visibility.PUBLIC, ClaimStatus.PROPOSED),
    ("meridian",
     "Mentored two engineers who were promoted to senior during 2025.",
     "Two of the people I mentored made senior last year.",
     Visibility.RECRUITER, ClaimStatus.PROPOSED),
]


class Command(BaseCommand):
    help = "Load the demo record. Wipes the existing knowledge base first."

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep", action="store_true",
            help="Add to the existing record instead of replacing it.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["keep"]:
            Claim.objects.all().delete()
            Source.objects.all().delete()
            Entity.objects.all().delete()

        entities = {
            key: Entity.objects.create(**spec)
            for key, spec in ENTITIES.items()
        }

        for key, text, excerpt, visibility, status in RECORD:
            source = Source.objects.create(
                kind=SourceKind.RESUME if key == "degree"
                else SourceKind.INTERVIEW,
                label=RESUME if key == "degree" else INTERVIEW,
                excerpt=excerpt,
            )
            Claim.objects.create(
                entity=entities.get(key) if key else None,
                text=text,
                source=source,
                visibility=visibility,
                status=status,
                confidence=0.95,
            )

        approved = Claim.objects.filter(status=ClaimStatus.APPROVED).count()
        proposed = Claim.objects.filter(status=ClaimStatus.PROPOSED).count()
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {approved} claims on record, {proposed} awaiting review, "
            f"across {len(entities)} entities."
        ))
