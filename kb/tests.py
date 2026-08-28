"""Tests for the three guarantees the project actually promises."""

from unittest.mock import patch

from django.test import TestCase

from kb.models import (
    Audience, Claim, ClaimStatus, Entity, EntityKind, Source, SourceKind,
    Visibility,
)


def make_claim(text, visibility, status=ClaimStatus.APPROVED, entity=None):
    source = Source.objects.create(
        kind=SourceKind.INTERVIEW, label="Interview, 12 Aug 2026",
        excerpt=text,
    )
    return Claim.objects.create(
        text=text, source=source, visibility=visibility, status=status,
        entity=entity,
    )


class VisibilityTests(TestCase):
    def setUp(self):
        self.public = make_claim("Worked at Acme.", Visibility.PUBLIC)
        self.recruiter = make_claim("Earned 140k.", Visibility.RECRUITER)
        self.private = make_claim("Left after a dispute.", Visibility.PRIVATE)

    def test_public_audience_sees_only_public(self):
        visible = Claim.objects.visible_to(Audience.PUBLIC)
        self.assertEqual(list(visible), [self.public])

    def test_recruiter_sees_public_and_recruiter_but_not_private(self):
        visible = set(Claim.objects.visible_to(Audience.RECRUITER))
        self.assertEqual(visible, {self.public, self.recruiter})

    def test_owner_sees_everything(self):
        visible = Claim.objects.visible_to(Audience.OWNER)
        self.assertEqual(visible.count(), 3)

    def test_unapproved_claims_are_never_visible(self):
        make_claim("Unreviewed.", Visibility.PUBLIC, ClaimStatus.PROPOSED)
        make_claim("Thrown out.", Visibility.PUBLIC, ClaimStatus.REJECTED)
        self.assertEqual(
            list(Claim.objects.visible_to(Audience.OWNER)),
            [self.private, self.recruiter, self.public],
        )

    def test_unknown_audience_gets_nothing(self):
        self.assertEqual(list(Claim.objects.visible_to("admin")), [])


class SourceIntegrityTests(TestCase):
    def test_source_cannot_be_deleted_while_cited(self):
        from django.db.models import ProtectedError

        claim = make_claim("Worked at Acme.", Visibility.PUBLIC)
        with self.assertRaises(ProtectedError):
            claim.source.delete()


class AnswerTests(TestCase):
    """The answering layer must not be able to cite past its clearance,
    however the model behaves."""

    def setUp(self):
        self.public = make_claim("Worked at Acme.", Visibility.PUBLIC)
        self.private = make_claim("Left after a dispute.", Visibility.PRIVATE)

    def _answer(self, model_output, audience=Audience.PUBLIC):
        from llm.answer import answer_question

        with patch("llm.answer.complete", return_value=model_output):
            return answer_question("Why did they leave?", audience)

    def test_citation_outside_clearance_is_dropped(self):
        result = self._answer({
            "answered": True,
            "answer": "They left after a dispute.",
            "citations": [self.private.id],
        })
        self.assertFalse(result["answered"])
        self.assertEqual(result["citations"], [])

    def test_hallucinated_citation_id_is_dropped(self):
        result = self._answer({
            "answered": True, "answer": "Sure.", "citations": [9999],
        })
        self.assertFalse(result["answered"])

    def test_valid_citation_survives_with_its_source(self):
        result = self._answer({
            "answered": True,
            "answer": "They worked at Acme.",
            "citations": [self.public.id],
        })
        self.assertTrue(result["answered"])
        self.assertEqual(len(result["citations"]), 1)
        self.assertEqual(
            result["citations"][0]["source"]["label"],
            "Interview, 12 Aug 2026",
        )

    def test_empty_kb_declines_without_calling_the_model(self):
        from llm.answer import answer_question

        Claim.objects.all().delete()
        with patch("llm.answer.complete") as complete:
            result = answer_question("Anything?", Audience.RECRUITER)
        complete.assert_not_called()
        self.assertFalse(result["answered"])

    def test_context_only_contains_visible_claims(self):
        from llm.answer import build_context

        context = build_context(Claim.objects.visible_to(Audience.PUBLIC))
        self.assertIn("Worked at Acme.", context)
        self.assertNotIn("dispute", context)


class ExtractionTests(TestCase):
    """Extraction proposes; it may not assert. Anything it cannot quote
    never reaches the review queue."""

    ANSWER = "I ran the billing rewrite at Acme. It took about six weeks."

    def _propose(self, claims):
        from llm.extract import propose

        with patch("llm.client.complete_json", return_value={"claims": claims}):
            return propose("Tell me about a project.", self.ANSWER)

    def _claim(self, text, excerpt, **kwargs):
        return {
            "text": text, "excerpt": excerpt,
            "visibility": kwargs.get("visibility", "public"),
            "confidence": kwargs.get("confidence", 0.9),
            "entity": kwargs.get("entity"),
        }

    def test_quoted_claim_is_proposed_not_approved(self):
        created, rejected = self._propose([
            self._claim("Ran the billing rewrite at Acme.",
                        "I ran the billing rewrite at Acme."),
        ])
        self.assertEqual(rejected, [])
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].status, ClaimStatus.PROPOSED)
        self.assertEqual(
            list(Claim.objects.visible_to(Audience.OWNER)), []
        )

    def test_unquotable_claim_is_rejected_before_review(self):
        created, rejected = self._propose([
            self._claim("Works well under deadline pressure.",
                        "I thrive under pressure."),
        ])
        self.assertEqual(created, [])
        self.assertEqual(len(rejected), 1)
        self.assertEqual(Claim.objects.count(), 0)

    def test_rewrapped_excerpt_still_matches(self):
        created, _ = self._propose([
            self._claim("The rewrite took six weeks.",
                        "It took\n  about six weeks."),
        ])
        self.assertEqual(len(created), 1)

    def test_every_proposed_claim_has_a_source(self):
        created, _ = self._propose([
            self._claim("Ran the billing rewrite at Acme.",
                        "I ran the billing rewrite at Acme."),
            self._claim("The rewrite took six weeks.",
                        "It took about six weeks."),
        ])
        self.assertTrue(all(c.source_id for c in created))
        self.assertEqual(Source.objects.count(), 2)

    def test_claims_sharing_an_excerpt_share_one_source(self):
        created, _ = self._propose([
            self._claim("Ran the billing rewrite.",
                        "I ran the billing rewrite at Acme."),
            self._claim("Worked at Acme.",
                        "I ran the billing rewrite at Acme."),
        ])
        self.assertEqual(Source.objects.count(), 1)
        self.assertEqual(len({c.source_id for c in created}), 1)

    def test_unrecognised_visibility_falls_back_to_private(self):
        created, _ = self._propose([
            self._claim("Ran the billing rewrite at Acme.",
                        "I ran the billing rewrite at Acme.",
                        visibility="everyone"),
        ])
        self.assertEqual(created[0].visibility, Visibility.PRIVATE)

    def test_entity_is_created_and_reused(self):
        spec = {"kind": "role", "title": "Engineer", "org": "Acme",
                "start": "2019-01-01", "end": None}
        created, _ = self._propose([
            self._claim("Ran the billing rewrite at Acme.",
                        "I ran the billing rewrite at Acme.", entity=spec),
            self._claim("The rewrite took six weeks.",
                        "It took about six weeks.", entity=spec),
        ])
        self.assertEqual(Entity.objects.count(), 1)
        entity = Entity.objects.get()
        self.assertEqual(entity.kind, EntityKind.ROLE)
        self.assertEqual({c.entity_id for c in created}, {entity.id})
