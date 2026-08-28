"""Read a filled-in intake file back into an IntakeSession.

Resumable by design: import a partly-filled file, write more answers, and
import again. Re-importing updates the turn that already exists rather than
creating a second one, which is what keeps a correction from minting a
second Source and leaving the first citable but stale.

A key that matches no question stops the whole import before anything is
written. Silently skipping it would mean a typo quietly costs the candidate
an answer.
"""

import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from kb.models import IntakeSession, IntakeTurn, Question, Source

VERSION_RE = re.compile(r"^\s*question-set-version:\s*(\S+)\s*$", re.MULTILINE)
HEADING_RE = re.compile(r"^##\s*\[([^\]]+)\]")
ANSWER_RE = re.compile(r"^>\s?(.*)$")


def parse_version(text):
    match = VERSION_RE.search(text)
    if not match:
        raise CommandError(
            "The file has no 'question-set-version:' line in its header. It "
            "may not be a secondchair intake file, or the header was "
            "removed. Re-export with export_intake."
        )
    return match.group(1)


def parse_blocks(text):
    """Yield ``(key, answer)`` for every block, answered or not.

    An answer is the run of ``>``-prefixed lines in a block. Consecutive
    lines are joined with newlines so paragraph breaks survive the round
    trip.
    """
    blocks, key, lines = [], None, []
    for line in text.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            if key is not None:
                blocks.append((key, "\n".join(lines).strip()))
            key, lines = heading.group(1).strip(), []
            continue
        if key is None:
            continue
        answer = ANSWER_RE.match(line)
        if answer:
            lines.append(answer.group(1).rstrip())
    if key is not None:
        blocks.append((key, "\n".join(lines).strip()))
    return blocks


class Command(BaseCommand):
    help = "Import a filled-in intake markdown file into an IntakeSession."

    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument(
            "--session",
            type=int,
            default=None,
            help="Add to an existing session instead of creating one.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"No such file: {path}")

        text = path.read_text(encoding="utf-8")
        version = parse_version(text)
        blocks = parse_blocks(text)
        if not blocks:
            raise CommandError(
                f"{path} contains no question blocks. Expected headings of "
                f"the form '## [question-key] category'."
            )

        questions = {
            q.key: q
            for q in Question.objects.filter(question_set_version=version)
        }

        # Every key is checked before anything is written, so a typo costs
        # an error message rather than an answer.
        unknown = [key for key, _ in blocks if key not in questions]
        if unknown:
            raise CommandError(
                "These bracketed keys match no question in set "
                f"'{version}': {', '.join(repr(k) for k in unknown)}. "
                "Nothing was imported. Fix the keys (they must match the "
                "exported file exactly) and run the import again."
            )

        if options["session"] is None:
            session = IntakeSession.objects.create(question_set_version=version)
            self.stdout.write(f"Created intake session {session.pk}.")
        else:
            try:
                session = IntakeSession.objects.get(pk=options["session"])
            except IntakeSession.DoesNotExist:
                raise CommandError(
                    f"No intake session with id {options['session']}."
                )
            if session.question_set_version != version:
                raise CommandError(
                    f"Session {session.pk} uses question set "
                    f"'{session.question_set_version}', but this file is for "
                    f"'{version}'. Nothing was imported."
                )

        sources_before = Source.objects.count()
        created = updated = skipped = 0

        for key, answer in blocks:
            if not answer:
                skipped += 1
                continue
            question = questions[key]
            turn = IntakeTurn.objects.filter(
                session=session, question=question
            ).first()
            if turn is None:
                IntakeTurn.objects.create(
                    session=session,
                    question=question,
                    question_text=question.text,
                    answer_text=answer,
                )
                created += 1
            else:
                # save() mints a Source only when there is not one already,
                # so an update keeps the original.
                turn.answer_text = answer
                turn.save()
                updated += 1

        minted = Source.objects.count() - sources_before
        self.stdout.write(
            self.style.SUCCESS(
                f"Session {session.pk}: {created} turn(s) created, "
                f"{updated} updated, {skipped} blank block(s) skipped, "
                f"{minted} source(s) minted."
            )
        )
