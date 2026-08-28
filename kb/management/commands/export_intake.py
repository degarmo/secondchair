"""Write the question set out as a markdown file to fill in offline.

Forty long-form answers typed into a terminal prompt loop is the wrong
ergonomics. This lets the candidate use a real editor and work in sittings,
importing as often as they like.
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from kb.models import Question

DEFAULT_VERSION = "v1"
DEFAULT_OUTPUT = "intake.md"

# `question-set-version` is machine-read on import: keys are only unique
# within a set, so the file has to say which set it belongs to.
HEADER = """<!--
secondchair intake file
question-set-version: {version}

HOW TO FILL THIS IN

  Write your answer after the ">" on the answer line:

      > I have been at Meridian Health since March 2022.

  For a longer answer, start every line with ">":

      > We moved the pipeline off a nightly batch.
      > It took about eight months.

  Leave a ">" line blank to skip that question. You can come back to it
  later and import again -- nothing is lost, and re-importing updates your
  earlier answers rather than duplicating them.

DO NOT EDIT the [bracketed] keys in the headings. They are how each answer
is matched back to its question on import. Changing one will stop the
import with an error rather than risk filing your answer under the wrong
question.
-->

# Intake -- question set {version}

{count} questions. Answer what you can; blanks are fine.
"""

BLOCK = """
## [{key}] {category}

{text}

> 

---
"""


class Command(BaseCommand):
    help = "Export a question set as a markdown file to fill in offline."

    def create_parser(self, prog_name, subcommand, **kwargs):
        # BaseCommand already defines --version (it prints the Django
        # version). Here --version names the question set, so let the later
        # definition win rather than renaming the documented flag.
        kwargs["conflict_handler"] = "resolve"
        return super().create_parser(prog_name, subcommand, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            "--version",
            default=DEFAULT_VERSION,
            help="Question set version to export.",
        )
        parser.add_argument(
            "--output",
            default=DEFAULT_OUTPUT,
            help="Path to write. Refuses to overwrite an existing file.",
        )

    def handle(self, *args, **options):
        version = options["version"]
        path = Path(options["output"])

        # Answers represent real work, so an existing file is never
        # overwritten.
        if path.exists():
            raise CommandError(
                f"{path} already exists. Refusing to overwrite it -- move or "
                f"rename it first, or pass --output with a different path."
            )

        questions = list(
            Question.objects.filter(active=True, question_set_version=version)
            .order_by("priority", "pk")
        )
        if not questions:
            raise CommandError(
                f"No active questions in set '{version}'. Run seed_questions "
                f"first, or pass --version."
            )

        body = HEADER.format(version=version, count=len(questions))
        body += "".join(
            BLOCK.format(key=q.key, category=q.category, text=q.text)
            for q in questions
        )
        path.write_text(body, encoding="utf-8")

        self.stdout.write(
            self.style.SUCCESS(
                f"Wrote {len(questions)} question(s) from set '{version}' to "
                f"{path.resolve()}"
            )
        )
