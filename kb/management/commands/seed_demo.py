"""Load a demo knowledge base.

Idempotent: every row is looked up by a natural key before it is created,
so running the command twice leaves the row counts unchanged. The three
intake-turn Sources are never created here -- they come from
``IntakeTurn.save()``, which is the only thing allowed to mint them.
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from kb.models import (
    Constraint,
    ConstraintKind,
    EmploymentType,
    IntakeSession,
    IntakeTurn,
    Project,
    Role,
    Skill,
    SkillCategory,
    SkillDepth,
    Source,
    SourceKind,
    Story,
    Visibility,
)

QUESTION_SET_VERSION = "demo-v1"

TURNS = [
    (
        "Where are you working now, and what does the role involve?",
        "I'm a staff engineer at Meridian Health, and I've been there since "
        "March 2022. I lead six engineers across two squads and I own the "
        "on-call rotation.",
    ),
    (
        "Tell me about a project you're proud of.",
        "The claims pipeline rewrite. We moved it off a nightly batch onto "
        "streaming over about eight months, and settlement went from four "
        "days to under six hours.",
    ),
    (
        "Tell me about a time something went wrong.",
        "We shipped a migration that double-counted a week of claims. I "
        "caught it in reconciliation, we rolled back within the day, and I "
        "wrote the backfill myself.",
    ),
]

MANUAL_SOURCES = {
    "portfolio": "Personal portfolio site, reviewed with candidate",
    "skills": "Skills inventory, completed by candidate",
    "preferences": "Role preferences discussion, 24 Aug 2026",
}


class Command(BaseCommand):
    help = "Create a demo knowledge base. Safe to run more than once."

    @transaction.atomic
    def handle(self, *args, **options):
        session, _ = IntakeSession.objects.get_or_create(
            question_set_version=QUESTION_SET_VERSION
        )

        # Answered turns mint their own intake_turn Sources on first save.
        turns = []
        for question, answer in TURNS:
            turn, _ = IntakeTurn.objects.get_or_create(
                session=session,
                question_text=question,
                defaults={"answer_text": answer},
            )
            turns.append(turn)

        manual = {
            key: Source.objects.get_or_create(
                kind=SourceKind.MANUAL,
                label=label,
                defaults={"captured_on": date(2026, 8, 24)},
            )[0]
            for key, label in MANUAL_SOURCES.items()
        }

        meridian, _ = Role.objects.get_or_create(
            org="Meridian Health",
            title="Staff Engineer",
            defaults={
                "source": turns[0].source,
                "start_date": date(2022, 3, 1),
                "end_date": None,
                "employment_type": EmploymentType.FULL_TIME,
                "summary": "Leads six engineers across two squads and owns "
                "the platform on-call rotation.",
                "visibility": Visibility.PUBLIC,
                "verified": True,
            },
        )

        kestrel, _ = Role.objects.get_or_create(
            org="Kestrel Logistics",
            title="Senior Engineer",
            defaults={
                "source": turns[1].source,
                "start_date": date(2019, 1, 7),
                "end_date": date(2022, 2, 28),
                "employment_type": EmploymentType.FULL_TIME,
                "summary": "Built and ran the routing service behind "
                "next-day delivery scheduling.",
                "visibility": Visibility.PUBLIC,
                "verified": True,
            },
        )

        claims_pipeline, _ = Project.objects.get_or_create(
            name="Claims pipeline rewrite",
            defaults={
                "source": turns[1].source,
                "description": "Replaced a nightly batch claims processor "
                "with a streaming pipeline.",
                "stack": ["Python", "Kafka", "Postgres", "Terraform"],
                "outcome": "Settlement time fell from four days to under "
                "six hours.",
                "role": meridian,
                "url": None,
                "visibility": Visibility.PUBLIC,
                "verified": True,
            },
        )

        # Independent work: attaches to no employer.
        Project.objects.get_or_create(
            name="ledgerline",
            defaults={
                "source": manual["portfolio"],
                "description": "Open-source double-entry bookkeeping library "
                "for small Python services.",
                "stack": ["Python", "SQLite"],
                "outcome": "Used by three external projects; 400 stars.",
                "role": None,
                "url": "https://example.com/ledgerline",
                "visibility": Visibility.PUBLIC,
                "verified": False,
            },
        )

        Story.objects.get_or_create(
            title="Streaming migration under a hard audit deadline",
            defaults={
                "source": turns[1].source,
                "situation": "Claims settled on a nightly batch, and an "
                "audit commitment required same-day settlement.",
                "action": "Split the rewrite into shippable stages and ran "
                "the old and new pipelines side by side for six weeks.",
                "result": "Settlement dropped to under six hours with no "
                "reconciliation breaks at cutover.",
                "themes": ["scale", "ambiguity", "delivery"],
                "role": meridian,
                "project": claims_pipeline,
                "requires_context": False,
                "visibility": Visibility.PUBLIC,
                "verified": True,
            },
        )

        # Both FKs null: a story that attaches to nothing.
        Story.objects.get_or_create(
            title="Double-counted claims after a bad migration",
            defaults={
                "source": turns[2].source,
                "situation": "A migration double-counted roughly a week of "
                "claims before anyone noticed.",
                "action": "Caught it in reconciliation, rolled back the same "
                "day, and wrote the backfill personally.",
                "result": "Ledger fully corrected within 48 hours; "
                "reconciliation checks now run pre-merge.",
                "themes": ["failure", "ownership", "recovery"],
                "role": None,
                "project": None,
                "requires_context": True,
                "visibility": Visibility.RECRUITER,
                "verified": True,
            },
        )

        skills = [
            ("Python", SkillCategory.LANGUAGE, date(2014, 9, 1), None,
             SkillDepth.DEEP),
            ("Django", SkillCategory.FRAMEWORK, date(2016, 4, 1), None,
             SkillDepth.DEEP),
            ("Kafka", SkillCategory.PLATFORM, date(2020, 2, 1),
             date(2024, 11, 30), SkillDepth.WORKING),
            ("gRPC", SkillCategory.PROTOCOL, date(2021, 6, 1),
             date(2023, 5, 31), SkillDepth.FAMILIAR),
        ]
        for name, category, first_used, last_used, depth in skills:
            Skill.objects.get_or_create(
                name=name,
                defaults={
                    "source": manual["skills"],
                    "category": category,
                    "first_used": first_used,
                    "last_used": last_used,
                    "depth": depth,
                    "visibility": Visibility.PUBLIC,
                    "verified": True,
                },
            )

        constraints = [
            (ConstraintKind.REMOTE_POLICY, "Remote, up to one office week "
             "per quarter", "Will not relocate."),
            (ConstraintKind.COMPENSATION, "£115,000 base minimum",
             "Flexible on equity split."),
        ]
        for kind, value, notes in constraints:
            Constraint.objects.get_or_create(
                kind=kind,
                value=value,
                defaults={
                    "source": manual["preferences"],
                    "notes": notes,
                    "visibility": Visibility.RECRUITER,
                    "verified": True,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded: {IntakeSession.objects.count()} session, "
                f"{IntakeTurn.objects.count()} turns, "
                f"{Source.objects.count()} sources, "
                f"{Role.objects.count()} roles, "
                f"{Project.objects.count()} projects, "
                f"{Story.objects.count()} stories, "
                f"{Skill.objects.count()} skills, "
                f"{Constraint.objects.count()} constraints."
            )
        )
