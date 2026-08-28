"""Turning an interview answer into proposed claims.

Nothing here writes an approved claim. Everything lands as PROPOSED and
waits for the human. Two checks run server-side before a proposal is even
offered for review:

* every claim must come with a verbatim excerpt, and
* that excerpt must actually occur in what the candidate said.

The second check is the one that matters -- it is what stops a plausible
embellishment from entering the review queue wearing a citation.
"""

import re
from datetime import date

from django.db import transaction

from kb.models import (
    Claim, ClaimStatus, Entity, EntityKind, Source, SourceKind, Visibility,
)

SYSTEM = """You extract atomic, checkable claims from one turn of an \
interview with a job candidate. A human reviews everything you produce, so \
your job is to be accurate and complete, never to be generous.

What a claim is:
- One assertion a recruiter could ask a follow-up question about.
- Stated plainly, in the third person ("Led the billing rewrite", not "I \
led the billing rewrite").
- Supported word-for-word by something the candidate actually said.

Hard rules:
- `excerpt` must be copied character-for-character from the candidate's \
answer. Do not paraphrase it, tidy its grammar, or stitch together spans \
that are not adjacent. If you cannot quote it, do not claim it.
- Extract only what was said. "We shipped it in six weeks" does not \
support "works well under deadline pressure".
- Split compound statements into separate claims. Merge nothing.
- If the answer contains no factual content (pleasantries, "let me think", \
a question back), return an empty list. That is a fine outcome.
- `confidence` is how certain you are that the excerpt supports the claim \
as worded -- not how impressive the claim is.

Visibility, your best guess (the human will correct it):
- `public`: safe on a public profile. Employers, titles, tech, education.
- `recruiter`: fine for a recruiter under consideration. Specific metrics, \
project details, reasons for leaving, general compensation range.
- `private`: do not share by default. Health, family, conflict with named \
people, unflattering detail, anything the candidate hedged about.
When in doubt, choose the more restricted level.

Entity: if the claim belongs to a job, project, or degree the candidate \
named, fill in `entity`. Use the organisation's real name as given. Omit \
`entity` for general claims. Dates must be YYYY-MM-DD; use the first of \
the month when only a month is known, and omit what was not said."""

SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "excerpt": {
                        "type": "string",
                        "description": "Verbatim span from the answer.",
                    },
                    "visibility": {
                        "type": "string",
                        "enum": ["public", "recruiter", "private"],
                    },
                    "confidence": {
                        "type": "number", "minimum": 0, "maximum": 1,
                    },
                    "entity": {
                        "type": ["object", "null"],
                        "properties": {
                            "kind": {
                                "type": "string",
                                "enum": [
                                    "role", "project", "education",
                                    "skill", "other",
                                ],
                            },
                            "title": {"type": "string"},
                            "org": {"type": "string"},
                            "start": {"type": ["string", "null"]},
                            "end": {"type": ["string", "null"]},
                        },
                        "required": ["kind", "title", "org", "start", "end"],
                        "additionalProperties": False,
                    },
                },
                "required": [
                    "text", "excerpt", "visibility", "confidence", "entity",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["claims"],
    "additionalProperties": False,
}

VISIBILITY_BY_NAME = {
    "public": Visibility.PUBLIC,
    "recruiter": Visibility.RECRUITER,
    "private": Visibility.PRIVATE,
}


def _normalise(text):
    """Collapse whitespace so an excerpt still matches if the model
    re-wrapped a line. Anything beyond that counts as not a quote."""
    return re.sub(r"\s+", " ", text).strip().lower()


def propose(question, answer, asked_on=None):
    """Extract proposed claims from one interview turn.

    Returns ``(claims, rejected)`` -- ``rejected`` holds proposals whose
    excerpt could not be found in ``answer``, so the caller can show that
    the filter did something rather than hiding it.
    """
    from .client import complete_json

    result = complete_json(
        system=SYSTEM,
        user=f"INTERVIEWER ASKED\n{question}\n\nCANDIDATE ANSWERED\n{answer}",
        schema=SCHEMA,
    )

    haystack = _normalise(answer)
    verified, rejected = [], []
    for proposal in result["claims"]:
        if _normalise(proposal["excerpt"]) in haystack:
            verified.append(proposal)
        else:
            rejected.append(proposal)

    return _persist(verified, asked_on or date.today()), rejected


@transaction.atomic
def _persist(proposals, asked_on):
    """Write proposals as PROPOSED claims, one Source per distinct excerpt."""
    label = f"Interview, {asked_on.strftime('%d %b %Y')}"
    sources, entities, claims = {}, {}, []

    for proposal in proposals:
        excerpt = proposal["excerpt"]
        if excerpt not in sources:
            sources[excerpt] = Source.objects.create(
                kind=SourceKind.INTERVIEW, label=label, excerpt=excerpt
            )

        entity = None
        if spec := proposal["entity"]:
            key = (spec["kind"], spec["title"], spec["org"])
            if key not in entities:
                entities[key], _ = Entity.objects.get_or_create(
                    kind=spec["kind"] if spec["kind"] in EntityKind.values
                    else EntityKind.OTHER,
                    title=spec["title"],
                    org=spec["org"],
                    defaults={
                        "start": spec.get("start") or None,
                        "end": spec.get("end") or None,
                    },
                )
            entity = entities[key]

        claims.append(
            Claim(
                text=proposal["text"],
                source=sources[excerpt],
                entity=entity,
                visibility=VISIBILITY_BY_NAME.get(
                    proposal["visibility"], Visibility.PRIVATE
                ),
                confidence=proposal["confidence"],
                status=ClaimStatus.PROPOSED,
            )
        )

    return Claim.objects.bulk_create(claims)
