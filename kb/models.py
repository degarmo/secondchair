"""The knowledge base: Sources, Entities, and the Claims that cite them.

Two invariants live here, and everything else in the project depends on them:

1. A Claim cannot exist without a Source. The FK is non-nullable and
   PROTECTed, so a Source can never be deleted out from under a claim
   that cites it.
2. Visibility is a query-time filter, not a prompt instruction. Nothing
   should ever hand a raw ``Claim.objects.all()`` to the answering
   pipeline -- use ``Claim.objects.visible_to(audience)``.
"""

from django.db import models


class Visibility(models.IntegerChoices):
    """Ordered least- to most-restricted. Comparison is `<=`, so an
    audience cleared for RECRUITER also sees PUBLIC."""

    PUBLIC = 10, "Public"
    RECRUITER = 20, "Recruiter"
    PRIVATE = 30, "Private"


class Audience(models.TextChoices):
    """Who is asking. Maps to the highest Visibility they may read."""

    PUBLIC = "public", "Public"
    RECRUITER = "recruiter", "Recruiter"
    OWNER = "owner", "Owner"


AUDIENCE_CLEARANCE = {
    Audience.PUBLIC: Visibility.PUBLIC,
    Audience.RECRUITER: Visibility.RECRUITER,
    Audience.OWNER: Visibility.PRIVATE,
}


class SourceKind(models.TextChoices):
    INTERVIEW = "interview", "Interview turn"
    RESUME = "resume", "Resume"
    DOCUMENT = "document", "Uploaded document"
    LINK = "link", "Link"
    MANUAL = "manual", "Entered by hand"


class Source(models.Model):
    """Where a claim came from. Every claim points at exactly one.

    ``excerpt`` is the verbatim span the claim was drawn from -- it is what
    gets shown when a recruiter clicks a citation, so it must be quotable
    on its own without the rest of the source.
    """

    kind = models.CharField(max_length=20, choices=SourceKind.choices)
    label = models.CharField(
        max_length=200,
        help_text="Human-readable citation, e.g. 'Interview, 12 Aug 2026' "
        "or 'resume-2026.pdf, p2'.",
    )
    excerpt = models.TextField(
        help_text="Verbatim span this source contributed. Shown to the "
        "recruiter when they open a citation."
    )
    uri = models.URLField(blank=True, help_text="Original location, if any.")
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-captured_at"]

    def __str__(self):
        return self.label


class EntityKind(models.TextChoices):
    ROLE = "role", "Role"
    PROJECT = "project", "Project"
    EDUCATION = "education", "Education"
    SKILL = "skill", "Skill"
    OTHER = "other", "Other"


class Entity(models.Model):
    """A thing claims hang off: a job, a project, a degree.

    Deliberately thin. It exists to give the answering model chronology and
    grouping ("at Acme, 2019-2022: ...") without a table per type. It holds
    no assertions of its own beyond identity -- anything arguable about an
    entity belongs in a Claim, where it can be sourced.
    """

    kind = models.CharField(max_length=20, choices=EntityKind.choices)
    title = models.CharField(max_length=200)
    org = models.CharField(max_length=200, blank=True)
    start = models.DateField(null=True, blank=True)
    end = models.DateField(null=True, blank=True, help_text="Null = current.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start", "-created_at"]
        verbose_name_plural = "entities"

    def __str__(self):
        return f"{self.title} @ {self.org}" if self.org else self.title

    @property
    def period(self):
        if not self.start:
            return ""
        end = self.end.strftime("%b %Y") if self.end else "present"
        return f"{self.start.strftime('%b %Y')} - {end}"


class ClaimStatus(models.TextChoices):
    """Extraction proposes; the human approves. Only APPROVED claims are
    ever eligible to be read back out."""

    PROPOSED = "proposed", "Proposed"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class ClaimQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(status=ClaimStatus.APPROVED)

    def visible_to(self, audience):
        """The only supported way to read claims for an answer.

        Applies both gates: approval and clearance. An unknown audience
        gets nothing rather than defaulting open.
        """
        try:
            clearance = AUDIENCE_CLEARANCE[Audience(audience)]
        except ValueError:
            return self.none()
        return self.approved().filter(visibility__lte=clearance)


class Claim(models.Model):
    """One atomic, attributable assertion about the candidate.

    Rule of thumb for granularity: a claim is one thing a recruiter could
    ask a follow-up about, and one thing the source actually supports.
    """

    entity = models.ForeignKey(
        Entity,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="claims",
        help_text="Optional grouping. Standalone claims are fine.",
    )
    text = models.TextField(help_text="The assertion, stated plainly.")
    source = models.ForeignKey(
        Source,
        on_delete=models.PROTECT,
        related_name="claims",
        help_text="Required. A claim without a source cannot exist.",
    )
    visibility = models.IntegerField(
        choices=Visibility.choices,
        default=Visibility.RECRUITER,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=ClaimStatus.choices,
        default=ClaimStatus.PROPOSED,
        db_index=True,
    )
    confidence = models.FloatField(
        default=1.0,
        help_text="Extractor's confidence that the source supports this.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    objects = ClaimQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.text[:80]
