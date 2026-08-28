"""Extraction: turning one answered intake turn into proposed records.

Three rules hold this together.

* Extraction never writes to a knowledge model. It writes ``Extraction``
  rows and nothing else. Only ``promote_extraction`` creates a Role, a
  Story, or anything else a recruiter will read.
* The prompt's description of the target models is generated from the
  Django models themselves, so a field added later appears in the prompt
  without anyone remembering to update a string literal.
* A ``supporting_quote`` that does not appear in the answer is the exact
  failure this project exists to catch, so it is checked in code rather
  than trusted from the model.
"""

import json
import logging
import re

import anthropic
from django.apps import apps
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from kb.models import Extraction, ExtractionStatus, ExtractionTarget

logger = logging.getLogger(__name__)

MAX_TOKENS = 4096

# Set by the system, not proposed by the model: identity and timestamps are
# automatic, source and verified are set at promotion, and visibility is a
# privacy decision for the candidate rather than something to infer from an
# answer. Every other field -- including any added later -- is described to
# the model automatically.
SYSTEM_MANAGED_FIELDS = frozenset(
    {"id", "source", "verified", "visibility", "created_at", "updated_at"}
)

FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)

UNVERIFIED_PREFIX = "[UNVERIFIED] "
UNVERIFIED_PENALTY = 0.3


class ExtractionError(RuntimeError):
    """Raised when a response cannot be turned into extractions."""


# --------------------------------------------------------------------------
# Describing the target models to the model
# --------------------------------------------------------------------------


def target_models():
    """The five knowledge models an extraction may propose, in choice order."""
    return {
        value: apps.get_model("kb", value) for value, _ in ExtractionTarget.choices
    }


def proposable_fields(model):
    """Concrete, model-proposable fields on ``model``.

    Derived from ``_meta.get_fields()``, so this stays correct as the schema
    changes.
    """
    fields = []
    for field in model._meta.get_fields():
        if not getattr(field, "concrete", False) or field.auto_created:
            continue
        if field.name in SYSTEM_MANAGED_FIELDS:
            continue
        fields.append(field)
    return fields


def describe_field(field):
    """One line of schema, in the shape the prompt needs."""
    if isinstance(field, models.ForeignKey):
        kind = (
            f"integer id of an existing {field.related_model.__name__} "
            f"-- always omit, these are linked during review"
        )
    elif isinstance(field, ArrayField):
        kind = "array of strings"
    elif isinstance(field, models.DateField):
        kind = "string, ISO date YYYY-MM-DD"
    elif isinstance(field, models.BooleanField):
        kind = "boolean"
    elif isinstance(field, models.FloatField):
        kind = "number"
    elif isinstance(field, models.URLField):
        kind = "string, absolute URL"
    else:
        kind = "string"

    if getattr(field, "choices", None):
        allowed = ", ".join(repr(value) for value, _ in field.choices)
        kind = f"{kind}, one of: {allowed}"

    # A field with a default is optional to propose even though it is not
    # nullable -- omitting it is valid and the default applies.
    optional = field.blank or field.null or field.has_default()
    requirement = "optional" if optional else "required"
    return f"  - {field.name} ({kind}) [{requirement}]"


def describe_targets():
    lines = []
    for name, model in target_models().items():
        lines.append(f"{name}:")
        lines += [describe_field(f) for f in proposable_fields(model)]
        lines.append("")
    return "\n".join(lines).strip()


SYSTEM_TEMPLATE = """You extract structured records from one answer given \
by a job candidate during an intake interview. A human reviews everything \
you produce before any of it is used, so your job is to be accurate and \
complete, never generous.

You may propose records for exactly these models and these fields:

{schema}

Return JSON only. No prose, no explanation, no markdown fences. The whole \
response must be a single JSON array.

Each element is an object with exactly these keys:
  - "target_model": one of {targets}
  - "payload": an object mapping field names above to values. Use only \
field names listed for that model. Omit any field the answer does not \
support -- an absent field is always better than a guessed one.
  - "confidence": a number from 0.0 to 1.0, how certain you are that the \
answer supports this record as written.
  - "supporting_quote": the span of the answer that justifies this record, \
copied character for character from the answer. It must appear verbatim in \
the answer text.

Hard rules:

- Extract only what the answer actually states. Do not infer, do not \
embellish, and do not fill a gap with what is typical for someone with \
this background. "I led the rewrite" does not support "strong leadership \
skills". Two facts sitting next to each other are not evidence they are \
connected.
- If the answer supports no records at all -- it is a refusal, a \
pleasantry, a question back, or simply contains no facts -- return an \
empty array. That is a correct and expected outcome, not a failure.
- Dates use ISO format YYYY-MM-DD. When only a month and year are known, \
use the first of that month and set confidence to 0.6 or lower. When a \
date cannot be determined at all, omit the field entirely rather than \
guessing.
- Split compound statements into separate records. Do not merge.
- Never invent a field name that is not listed above."""

USER_TEMPLATE = """<question>
{question}
</question>

<answer>
{answer}
</answer>"""


def build_system_prompt():
    return SYSTEM_TEMPLATE.format(
        schema=describe_targets(),
        targets=", ".join(repr(v) for v, _ in ExtractionTarget.choices),
    )


# --------------------------------------------------------------------------
# The API call
# --------------------------------------------------------------------------


def get_client():
    """Build the Anthropic client, failing loudly on missing configuration."""
    if not settings.ANTHROPIC_API_KEY:
        raise ExtractionError(
            "ANTHROPIC_API_KEY is not set. Extraction cannot run without it."
        )
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def get_model_id():
    """The configured model id.

    Deliberately has no default: guessing a model identifier would be a
    silent, wrong answer, so a missing setting is an error naming the
    variable.
    """
    model = settings.ANTHROPIC_MODEL
    if not model:
        raise ExtractionError(
            "ANTHROPIC_MODEL is not set. Set it to the model identifier to "
            "use, for example in .env. There is no default."
        )
    return model


def call_model(question, answer):
    """One API call. Returns the raw response text."""
    client = get_client()
    response = client.messages.create(
        model=get_model_id(),
        max_tokens=MAX_TOKENS,
        system=build_system_prompt(),
        messages=[
            {
                "role": "user",
                "content": USER_TEMPLATE.format(question=question, answer=answer),
            }
        ],
    )
    if response.stop_reason == "refusal":
        raise ExtractionError("The model declined to process this answer.")
    return "".join(
        block.text for block in response.content if block.type == "text"
    )


# --------------------------------------------------------------------------
# Response handling
# --------------------------------------------------------------------------


def parse_response(raw, turn_id=None):
    """Parse the model's response into a list of proposal dicts.

    Fences are stripped if present, but that is logged: the prompt asks for
    bare JSON, so needing to strip means the prompt wants tightening.
    """
    text = raw.strip()
    fenced = FENCE.match(text)
    if fenced:
        logger.warning(
            "Turn %s: response was wrapped in markdown fences despite the "
            "prompt forbidding them; stripping. Tighten the prompt.",
            turn_id,
        )
        text = fenced.group(1)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error(
            "Turn %s: could not parse response as JSON (%s). Raw response: %r",
            turn_id,
            exc,
            raw,
        )
        raise ExtractionError(
            f"Model response was not valid JSON for turn {turn_id}."
        ) from exc

    if not isinstance(parsed, list):
        logger.error(
            "Turn %s: expected a JSON array, got %s. Raw response: %r",
            turn_id,
            type(parsed).__name__,
            raw,
        )
        raise ExtractionError(
            f"Model response was not a JSON array for turn {turn_id}."
        )
    return parsed


def clean_payload(model, payload, turn_id=None):
    """Drop keys that are not real, proposable fields on ``model``.

    A model inventing a field name must not reach the database.
    """
    allowed = {field.name for field in proposable_fields(model)}
    kept = {k: v for k, v in payload.items() if k in allowed}
    dropped = sorted(set(payload) - allowed)
    if dropped:
        logger.warning(
            "Turn %s: dropped unknown %s field(s) from payload: %s",
            turn_id,
            model.__name__,
            ", ".join(dropped),
        )
    return kept, dropped


def verify_quote(quote, answer_text):
    """Check the quote against the answer.

    Returns ``(quote, penalty)``. An unverifiable quote is kept and marked
    rather than discarded, so a human reviewer sees that it failed instead
    of the record silently disappearing.
    """
    if quote and quote.strip() and quote.strip() in answer_text:
        return quote, 0.0
    return f"{UNVERIFIED_PREFIX}{quote}", UNVERIFIED_PENALTY


@transaction.atomic
def build_extractions(turn, raw, proposals=None):
    """Turn a raw model response into saved ``Extraction`` rows.

    Separated from the API call so the parsing, field validation, and quote
    checking can be exercised without a network round trip.
    """
    if proposals is None:
        proposals = parse_response(raw, turn_id=turn.pk)

    models_by_name = target_models()
    rows = []

    for proposal in proposals:
        target = proposal.get("target_model")
        if target not in models_by_name:
            logger.warning(
                "Turn %s: skipping proposal with unknown target_model %r.",
                turn.pk,
                target,
            )
            continue

        payload = proposal.get("payload")
        if not isinstance(payload, dict):
            logger.warning(
                "Turn %s: skipping %s proposal whose payload is %s, not an "
                "object.",
                turn.pk,
                target,
                type(payload).__name__,
            )
            continue

        payload, _ = clean_payload(models_by_name[target], payload, turn.pk)

        quote, penalty = verify_quote(
            proposal.get("supporting_quote") or "", turn.answer_text or ""
        )
        if penalty:
            logger.warning(
                "Turn %s: %s supporting_quote does not appear in the answer; "
                "marking unverified and reducing confidence by %s.",
                turn.pk,
                target,
                penalty,
            )

        try:
            confidence = float(proposal.get("confidence", 0.0))
        except (TypeError, ValueError):
            logger.warning(
                "Turn %s: %s confidence %r is not a number; treating as 0.0.",
                turn.pk,
                target,
                proposal.get("confidence"),
            )
            confidence = 0.0

        rows.append(
            Extraction(
                turn=turn,
                target_model=target,
                payload=payload,
                confidence=max(0.0, min(1.0, confidence - penalty)),
                supporting_quote=quote,
                status=ExtractionStatus.PENDING,
            )
        )

    return Extraction.objects.bulk_create(rows)


def extract_from_turn(turn):
    """Extract proposed records from one answered turn. One API call.

    Never writes to Role, Project, Story, Skill, or Constraint.
    """
    if not (turn.answer_text and turn.answer_text.strip()):
        raise ExtractionError(
            f"Turn {turn.pk} has no answer to extract from."
        )

    raw = call_model(turn.question_text, turn.answer_text)
    return build_extractions(turn, raw)


# --------------------------------------------------------------------------
# Promotion
# --------------------------------------------------------------------------


def promote_extraction(extraction):
    """Create the real record an extraction proposes.

    Returns ``(object_or_None, errors)`` and never raises on validation
    failure -- a reviewer needs the reasons, not a traceback. A failed
    promotion leaves the extraction ``pending`` so it can be corrected in
    the admin and retried.
    """
    if extraction.status != ExtractionStatus.PENDING:
        return None, ["already reviewed"]

    source = extraction.turn.source
    if source is None:
        return None, [
            "the turn this was extracted from has no source; promoting "
            "would create a record with no provenance"
        ]

    try:
        model = apps.get_model("kb", extraction.target_model)
    except LookupError:
        return None, [f"unknown target model {extraction.target_model!r}"]

    payload, dropped = clean_payload(
        model, extraction.payload or {}, extraction.turn_id
    )
    errors = [
        f"{field}: not a field on {model.__name__}" for field in dropped
    ]

    instance = model(**payload, source=source, verified=True)

    try:
        instance.full_clean()
    except ValidationError as exc:
        for field, messages in exc.message_dict.items():
            errors += [f"{field}: {message}" for message in messages]
        return None, errors

    if errors:
        return None, errors

    with transaction.atomic():
        instance.save()
        extraction.status = ExtractionStatus.APPROVED
        extraction.reviewed_at = timezone.now()
        extraction.created_object_id = instance.pk
        extraction.save(
            update_fields=["status", "reviewed_at", "created_object_id"]
        )

    return instance, []


def reject_extraction(extraction, reason=""):
    """Mark an extraction rejected. Never creates anything.

    ``reason`` is logged rather than stored -- there is no field for it on
    ``Extraction``.
    """
    extraction.status = ExtractionStatus.REJECTED
    extraction.reviewed_at = timezone.now()
    extraction.save(update_fields=["status", "reviewed_at"])
    logger.info(
        "Rejected extraction %s (%s)%s",
        extraction.pk,
        extraction.target_model,
        f": {reason}" if reason else "",
    )
    return extraction
