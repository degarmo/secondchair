"""Answering recruiter questions from the knowledge base.

The guarantee this module makes: an answer's citations always point at
records the asker was cleared to see, and at records that actually exist.
That is enforced twice -- the context is built only from
``visible_to(audience)``, and every id the model returns is checked back
against that same set before the answer leaves the server. The prompt is
never trusted to do either job.

Declining is a correct outcome here, not a failure. A recruiter who is told
"that isn't in the record" has learned something true; one who is told a
plausible invention has not.
"""

import json
import logging

import anthropic
from django.conf import settings

from kb.models import Audience, Constraint, Project, Role, Skill, Story
from kb.services.extraction import ExtractionError, get_client, get_model_id

logger = logging.getLogger(__name__)

MAX_TOKENS = 2048

# Order shapes the context: employment history first, then what was built,
# then the narratives, then capabilities and terms.
ANSWERABLE_MODELS = (Role, Project, Story, Skill, Constraint)

SYSTEM = """You answer questions about one job candidate on their behalf, \
using ONLY the records provided below. You are working for the candidate, \
so be concrete and useful -- but you are worse than useless to them if you \
say anything the record does not support.

Rules, in priority order:

1. Every claim you make must be backed by at least one record id from the \
RECORDS block. List the ids you used in "citations".
2. If the records do not answer the question, set "answered" to false and \
say plainly what you do not have. Do not pad the answer with adjacent \
facts, and do not hedge your way toward an implication. "I don't have \
anything on that" is a correct and expected answer.
3. Never infer, estimate, generalise, or fill a gap with what is typical. \
Three years of Python does not make someone "highly experienced". Two \
records sitting near each other are not evidence they are connected.
4. Summarise naturally in your own words -- do not read records aloud \
verbatim -- but never drift beyond what they state.
5. Cite only ids that appear in the RECORDS block. Never invent an id.
6. Your answer will be read aloud, so write it to be spoken: plain \
sentences, no markdown, no bullet points, no id numbers in the prose \
itself. Two or three sentences unless the question needs more."""

SCHEMA = {
    "type": "object",
    "properties": {
        "answered": {
            "type": "boolean",
            "description": "False when the records do not support an answer.",
        },
        "answer": {
            "type": "string",
            "description": "The spoken reply. If answered is false, say "
            "what is missing.",
        },
        "citations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Record ids, exactly as given, e.g. 'Role#3'.",
        },
    },
    "required": ["answered", "answer", "citations"],
    "additionalProperties": False,
}


def record_id(obj):
    return f"{obj.__class__.__name__}#{obj.pk}"


def describe(obj):
    """One line of context for a record, in its own shape."""
    if isinstance(obj, Role):
        period = f"{obj.start_date} to {obj.end_date or 'present'}"
        return (f"{obj.title} at {obj.org} ({period}, "
                f"{obj.get_employment_type_display()}). {obj.summary}")
    if isinstance(obj, Project):
        stack = f" Built with: {', '.join(obj.stack)}." if obj.stack else ""
        outcome = f" Outcome: {obj.outcome}" if obj.outcome else ""
        where = f" At {obj.role.org}." if obj.role else " Independent project."
        return f"{obj.name}. {obj.description}{stack}{outcome}{where}"
    if isinstance(obj, Story):
        themes = f" Themes: {', '.join(obj.themes)}." if obj.themes else ""
        context = (" Needs framing to land well; use only if the question "
                   "invites it." if obj.requires_context else "")
        return (f"{obj.title}. Situation: {obj.situation} Action: "
                f"{obj.action} Result: {obj.result}{themes}{context}")
    if isinstance(obj, Skill):
        depth = obj.get_depth_display() if obj.depth else "depth not stated"
        used = f"since {obj.first_used}" if obj.last_used is None else (
            f"{obj.first_used} to {obj.last_used}")
        return (f"{obj.name} ({obj.get_category_display()}), {depth}, "
                f"used {used} -- about {obj.duration_years} years.")
    if isinstance(obj, Constraint):
        notes = f" ({obj.notes})" if obj.notes else ""
        return f"{obj.get_kind_display()}: {obj.value}{notes}"
    return str(obj)


def gather(audience):
    """Every record this audience may read, keyed by citation id."""
    records = {}
    for model in ANSWERABLE_MODELS:
        queryset = model.objects.visible_to(audience).select_related("source")
        if model is Project:
            queryset = queryset.select_related("role")
        for obj in queryset:
            records[record_id(obj)] = obj
    return records


def build_context(records):
    lines, current = [], None
    for key, obj in records.items():
        kind = obj.__class__.__name__
        if kind != current:
            lines.append(f"\n## {kind}")
            current = kind
        lines.append(f"[{key}] {describe(obj)}")
    return "\n".join(lines).strip()


def provenance(obj):
    """Where a record came from, as a recruiter would want to see it."""
    source = obj.source
    entry = {
        "record_id": record_id(obj),
        "record": describe(obj),
        "source_id": source.pk,
        "source_kind": source.kind,
        "source_label": source.label,
        "captured_on": source.captured_on.isoformat(),
        "quote": None,
    }
    # An intake source can show the candidate's own words behind the record.
    turn = getattr(source, "intake_turn", None)
    if turn is not None:
        entry["quote"] = turn.answer_text
        entry["question"] = turn.question_text
    return entry


def ask_model(question, context):
    """One API call, returning schema-conforming JSON."""
    client = get_client()
    try:
        response = client.messages.create(
            model=get_model_id(),
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            messages=[{
                "role": "user",
                "content": f"RECORDS\n{context}\n\nQUESTION\n{question}",
            }],
            output_config={
                "format": {"type": "json_schema", "schema": SCHEMA}
            },
        )
    except anthropic.APIStatusError as exc:
        raise ExtractionError(f"Claude API error {exc.status_code}") from exc
    except anthropic.APIConnectionError as exc:
        raise ExtractionError("Could not reach the Claude API.") from exc

    if response.stop_reason == "refusal":
        raise ExtractionError("The model declined to answer this question.")

    text = "".join(b.text for b in response.content if b.type == "text")
    return json.loads(text), response.usage


def answer_question(question, audience=Audience.RECRUITER):
    """Answer ``question`` for ``audience``, with citations.

    Returns a dict ready to serialise. Citations are filtered against the
    visible set on the way out, so an id that was hallucinated or belongs
    to a record above the asker's clearance is dropped rather than served.
    """
    records = gather(audience)

    if not records:
        return {
            "answered": False,
            "answer": "There is nothing on record I can share with you yet.",
            "citations": [],
            "usage": None,
        }

    result, usage = ask_model(question, build_context(records))

    seen, cited = set(), []
    for key in result.get("citations") or []:
        if key in records and key not in seen:
            seen.add(key)
            cited.append(records[key])
        elif key not in records:
            logger.warning(
                "Dropped citation %r: not a record visible to %s.",
                key, audience,
            )

    # An answer that claims to be answered but cites nothing is unsourced by
    # definition, so it does not go out.
    if result["answered"] and not cited:
        return {
            "answered": False,
            "answer": "I can't back that up from what I have on record.",
            "citations": [],
            "usage": {"input_tokens": usage.input_tokens,
                      "output_tokens": usage.output_tokens},
        }

    return {
        "answered": result["answered"],
        "answer": result["answer"],
        "citations": [provenance(obj) for obj in cited],
        "usage": {"input_tokens": usage.input_tokens,
                  "output_tokens": usage.output_tokens},
    }
