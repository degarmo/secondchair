"""Deciding what to ask the candidate next.

The interviewer sees only what is already in the KB, so it naturally
chases gaps rather than re-asking. It has no write access -- it proposes a
question, the candidate answers, and extraction takes over from there.
"""

from kb.models import Claim, Entity

SYSTEM = """You are interviewing a job candidate to build out their \
professional record. You are working for them, not screening them.

Ask exactly one question at a time. Good questions here are specific and \
answerable from memory -- "What was the team size on the billing rewrite?" \
beats "Tell me about your leadership style."

Priorities, highest first:
1. A gap that would stop a recruiter question from being answerable: a role \
with no dates, an achievement with no outcome, a named project with nothing \
attached to it.
2. Depth on something already recorded but thin -- ask for the number, the \
scope, the result.
3. A period of their history not covered at all.

Do not ask about anything already fully covered by the record below. Do not \
ask two things in one sentence. Do not preface the question with praise."""

SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string"},
        "rationale": {
            "type": "string",
            "description": "One line: which gap this fills. Shown to the "
            "candidate so they know why they are being asked.",
        },
        "targets": {
            "type": "string",
            "enum": ["gap", "depth", "coverage"],
        },
    },
    "required": ["question", "rationale", "targets"],
    "additionalProperties": False,
}

OPENING = {
    "question": "Let's start with where you work now, or where you worked "
    "most recently. What's the role, and what does the job actually "
    "involve day to day?",
    "rationale": "The record is empty, so we start with your current role.",
    "targets": "coverage",
}


def next_question(recent_turns=()):
    """Pick the next interview question given the KB's current state.

    ``recent_turns`` is an iterable of (question, answer) pairs from this
    session, so the interviewer does not repeat itself within a sitting.
    """
    from .client import complete_json

    claims = Claim.objects.approved().select_related("entity")
    if not claims.exists() and not recent_turns:
        return OPENING

    lines = []
    for entity in Entity.objects.prefetch_related("claims"):
        approved = [c for c in entity.claims.all() if c.status == "approved"]
        if not approved:
            continue
        lines.append(f"## {entity} ({entity.period or 'no dates recorded'})")
        lines += [f"  - {c.text}" for c in approved]

    loose = [c.text for c in claims if not c.entity_id]
    if loose:
        lines.append("## Unattached")
        lines += [f"  - {t}" for t in loose]

    record = "\n".join(lines) or "(nothing recorded yet)"
    session = "\n\n".join(
        f"Q: {q}\nA: {a}" for q, a in recent_turns
    ) or "(this is the first question of the session)"

    return complete_json(
        system=SYSTEM,
        user=f"RECORD SO FAR\n{record}\n\nTHIS SESSION\n{session}",
        schema=SCHEMA,
        effort="medium",
    )
