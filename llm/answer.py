"""Answering recruiter questions from the knowledge base.

The guarantee this module makes: an answer's citations always point at
claims the asker was actually cleared to see. That is enforced twice --
the context is built only from ``visible_to(audience)``, and every claim
id the model returns is checked back against that same set before the
answer leaves the server. The prompt is not trusted to do either job.
"""

from kb.models import Claim

SYSTEM = """You answer recruiter questions about one candidate, using ONLY \
the claims provided below. You are the candidate's representative, so be \
helpful and concrete -- but you are useless to them if you say anything the \
record does not support.

Rules, in priority order:

1. Every sentence of substance must be backed by at least one claim id from \
the CLAIMS block. Put the ids you used in `citations`.
2. If the claims do not answer the question, set `answered` to false and say \
plainly what is missing. Do not pad the answer with adjacent facts and do \
not hedge your way into an implication. "I don't have anything on that" is \
a correct and expected answer.
3. Never infer, estimate, generalise, or fill a gap with what is typical. If \
a claim says "three years of Python", you may not say "senior Python \
engineer". If two claims sit next to each other, you may not assume they \
are connected.
4. Do not repeat a claim's wording verbatim unless it is a quotable \
achievement -- summarise naturally, but do not drift from what it says.
5. Cite only ids that appear in the CLAIMS block. Never invent an id."""

SCHEMA = {
    "type": "object",
    "properties": {
        "answered": {
            "type": "boolean",
            "description": "False if the claims do not support an answer.",
        },
        "answer": {
            "type": "string",
            "description": "The reply, addressed to the recruiter. If "
            "answered is false, say what is missing.",
        },
        "citations": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "Claim ids supporting the answer.",
        },
    },
    "required": ["answered", "answer", "citations"],
    "additionalProperties": False,
}


def build_context(claims):
    """Render the visible claims as the CLAIMS block.

    Grouped by entity so the model gets chronology for free; ungrouped
    claims go last under their own heading.
    """
    by_entity, loose = {}, []
    for claim in claims:
        if claim.entity_id:
            by_entity.setdefault(claim.entity, []).append(claim)
        else:
            loose.append(claim)

    lines = []
    for entity, group in by_entity.items():
        header = f"## {entity}"
        if entity.period:
            header += f"  ({entity.period})"
        lines.append(f"{header}  [{entity.get_kind_display()}]")
        lines += [f"  [{c.id}] {c.text}" for c in group]
        lines.append("")

    if loose:
        lines.append("## Unattached")
        lines += [f"  [{c.id}] {c.text}" for c in loose]

    return "\n".join(lines).strip()


def answer_question(question, audience):
    """Answer ``question`` for ``audience``. Returns a dict ready to serialise.

    Citations are filtered against the visible set on the way out, so a
    hallucinated or out-of-scope id is dropped rather than returned.
    """
    claims = list(
        Claim.objects.visible_to(audience).select_related("entity", "source")
    )

    if not claims:
        return {
            "answered": False,
            "answer": "There is nothing in the knowledge base I can share "
            "with you yet.",
            "citations": [],
        }

    context = build_context(claims)
    result = complete(question, context)

    allowed = {c.id: c for c in claims}
    cited = [allowed[i] for i in dict.fromkeys(result["citations"]) if i in allowed]

    # An answer that claims to be answered but cites nothing is unsourced by
    # definition, so it does not go out.
    if result["answered"] and not cited:
        return {
            "answered": False,
            "answer": "I can't back that up from what I have on record.",
            "citations": [],
        }

    return {
        "answered": result["answered"],
        "answer": result["answer"],
        "citations": [
            {
                "claim_id": c.id,
                "claim_text": c.text,
                "source": {
                    "id": c.source_id,
                    "label": c.source.label,
                    "kind": c.source.kind,
                    "excerpt": c.source.excerpt,
                },
            }
            for c in cited
        ],
    }


def complete(question, context):
    from .client import complete_json

    return complete_json(
        system=SYSTEM,
        user=f"CLAIMS\n{context}\n\nRECRUITER QUESTION\n{question}",
        schema=SCHEMA,
    )
