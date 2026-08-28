"""The knowledge base.

One rule shapes this module: every claim about the candidate points at a
``Source``, and the FK is PROTECTed so a source cannot be deleted out from
under the claims that cite it. ``Gap`` and ``Extraction`` are the two
deliberate exceptions -- neither is a claim, so neither carries a source.
"""

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

DAYS_PER_YEAR = 365.25


class Visibility(models.TextChoices):
    PUBLIC = "public", "Public"
    RECRUITER = "recruiter", "Recruiter"
    PRIVATE = "private", "Private"


class SourceKind(models.TextChoices):
    RESUME = "resume", "Resume"
    INTAKE_TURN = "intake_turn", "Intake turn"
    DOCUMENT = "document", "Document"
    REPO = "repo", "Repository"
    MANUAL = "manual", "Entered by hand"


class EmploymentType(models.TextChoices):
    FULL_TIME = "full_time", "Full time"
    CONTRACT = "contract", "Contract"
    CONSULTING = "consulting", "Consulting"
    OTHER = "other", "Other"


class SkillCategory(models.TextChoices):
    LANGUAGE = "language", "Language"
    FRAMEWORK = "framework", "Framework"
    PLATFORM = "platform", "Platform"
    PROTOCOL = "protocol", "Protocol"
    DOMAIN = "domain", "Domain"
    TOOL = "tool", "Tool"


class SkillDepth(models.TextChoices):
    FAMILIAR = "familiar", "Familiar"
    WORKING = "working", "Working"
    DEEP = "deep", "Deep"


class ConstraintKind(models.TextChoices):
    LOCATION = "location", "Location"
    REMOTE_POLICY = "remote_policy", "Remote policy"
    COMPENSATION = "compensation", "Compensation"
    ROLE_TYPE = "role_type", "Role type"
    INDUSTRY = "industry", "Industry"
    DEALBREAKER = "dealbreaker", "Dealbreaker"


class QuestionCategory(models.TextChoices):
    OPENER = "opener", "Opener"
    ROLE = "role", "Role"
    PROJECT = "project", "Project"
    STORY = "story", "Story"
    SKILL = "skill", "Skill"
    CONSTRAINT = "constraint", "Constraint"
    CLOSER = "closer", "Closer"


class ExtractionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class ExtractionTarget(models.TextChoices):
    """Which knowledge model an extraction is proposing a row for.

    Values are the model class names verbatim, so an approved extraction
    can be promoted with ``apps.get_model("kb", extraction.target_model)``.
    """

    ROLE = "Role", "Role"
    PROJECT = "Project", "Project"
    STORY = "Story", "Story"
    SKILL = "Skill", "Skill"
    CONSTRAINT = "Constraint", "Constraint"


class Source(models.Model):
    """The single citation target. Every claim points here and nowhere else."""

    kind = models.CharField(max_length=20, choices=SourceKind.choices)
    label = models.CharField(
        max_length=255, help_text="Human-readable description of origin."
    )
    captured_on = models.DateField()
    uri = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.label


class Question(models.Model):
    """One question in the intake bank.

    Carries no source: a question is not a claim about the candidate. The
    wording here is the current wording -- ``IntakeTurn.question_text``
    keeps the wording as actually asked at the time.
    """

    key = models.SlugField(
        help_text="Stable identifier, referenced by code and seeds. Unique "
        "within a question set, so a later set can reuse it."
    )
    text = models.TextField(help_text="The question as asked.")
    category = models.CharField(
        max_length=20, choices=QuestionCategory.choices
    )
    target_model = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=ExtractionTarget.choices,
        help_text="Which knowledge model this question primarily feeds. "
        "Null for openers and closers.",
    )
    priority = models.IntegerField(help_text="Lower sorts first.")
    active = models.BooleanField(default=True)
    question_set_version = models.CharField(max_length=50)

    class Meta:
        ordering = ["priority"]
        constraints = [
            models.UniqueConstraint(
                fields=["key", "question_set_version"],
                name="unique_question_key_per_version",
            )
        ]

    def __str__(self):
        return self.key


class KnowledgeItem(models.Model):
    """Abstract base for everything that asserts something about the candidate.

    PROTECT on ``source`` is deliberate: deleting a source must not silently
    orphan the claims that cite it.
    """

    source = models.ForeignKey(
        Source, on_delete=models.PROTECT, related_name="%(class)s_items"
    )
    verified = models.BooleanField(default=False)
    visibility = models.CharField(
        max_length=20, choices=Visibility.choices, default=Visibility.RECRUITER
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class IntakeSession(models.Model):
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    question_set_version = models.CharField(max_length=50)

    def __str__(self):
        return f"Intake session {self.pk} ({self.question_set_version})"


class IntakeTurn(models.Model):
    """One question and its answer.

    A turn does not *become* a Source -- it *gets* one, on the save where an
    answer first appears. That is what makes the answer citable.
    """

    session = models.ForeignKey(
        IntakeSession, on_delete=models.CASCADE, related_name="turns"
    )
    question = models.ForeignKey(
        Question,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="turns",
    )
    question_text = models.TextField(
        help_text="Denormalised snapshot of the wording as asked at the time."
    )
    answer_text = models.TextField(null=True, blank=True)
    asked_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    source = models.OneToOneField(
        Source,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="intake_turn",
    )

    class Meta:
        constraints = [
            # Postgres treats NULLs as distinct, so this pins one turn per
            # question while still allowing any number of follow-up turns
            # that reference no question.
            models.UniqueConstraint(
                fields=["session", "question"],
                name="unique_turn_per_question_in_session",
            )
        ]

    def __str__(self):
        return f"Turn {self.pk} of session {self.session_id}"

    def _source_label(self):
        """Label this turn by its ordinal position within its session.

        Positions come from primary-key order, which matches creation order
        under BigAutoField, so an existing turn keeps the same number when it
        is answered later.
        """
        turns = self.session.turns
        preceding = turns.filter(pk__lt=self.pk).count() if self.pk else turns.count()
        return f"Intake session {self.session_id}, turn {preceding + 1}"

    def save(self, *args, **kwargs):
        if self.answer_text and self.answer_text.strip():
            if self.answered_at is None:
                self.answered_at = timezone.now()
            if self.source is None:
                self.source = Source.objects.create(
                    kind=SourceKind.INTAKE_TURN,
                    label=self._source_label(),
                    captured_on=timezone.localdate(),
                )
        super().save(*args, **kwargs)


class Role(KnowledgeItem):
    org = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(
        null=True, blank=True, help_text="Null means current."
    )
    employment_type = models.CharField(
        max_length=20, choices=EmploymentType.choices
    )
    summary = models.TextField()

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.title} at {self.org}"


class Project(KnowledgeItem):
    name = models.CharField(max_length=200)
    description = models.TextField()
    stack = ArrayField(
        models.CharField(max_length=100), help_text="Technologies used."
    )
    outcome = models.TextField(
        blank=True, help_text="What it produced or changed."
    )
    # Nullable by design: some projects are independent and attach to no
    # employer.
    role = models.ForeignKey(
        Role,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
    )
    url = models.URLField(
        null=True, blank=True, help_text="Public repo or live site."
    )

    def __str__(self):
        return self.name


class Story(KnowledgeItem):
    """The STAR unit. Carries every narrative answer."""

    title = models.CharField(max_length=200, help_text="Short internal handle.")
    situation = models.TextField()
    action = models.TextField()
    result = models.TextField()
    themes = ArrayField(
        models.CharField(max_length=50),
        help_text="e.g. conflict, failure, leadership, ambiguity, scale.",
    )
    # A story may attach to a role, a project, both, or neither.
    role = models.ForeignKey(
        Role,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stories",
    )
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stories",
    )
    requires_context = models.BooleanField(
        default=False,
        help_text="Fine to tell, but lands badly without framing. Not a "
        "visibility level: the answering layer includes these only when a "
        "question invites them, rather than in a general summary.",
    )

    def __str__(self):
        return self.title


class Skill(KnowledgeItem):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=SkillCategory.choices)
    first_used = models.DateField()
    last_used = models.DateField(
        null=True, blank=True, help_text="Null means currently in use."
    )
    depth = models.CharField(max_length=20, choices=SkillDepth.choices)

    def __str__(self):
        return self.name

    @property
    def duration_years(self):
        """Span from ``first_used`` to ``last_used``, or to today if null.

        Computed rather than stored: a stored duration goes stale, and a
        recruiter catching a stale number is worse than having no number.
        """
        end = self.last_used or timezone.localdate()
        return round((end - self.first_used).days / DAYS_PER_YEAR, 1)


class Constraint(KnowledgeItem):
    """What the candidate wants and will not accept."""

    kind = models.CharField(max_length=20, choices=ConstraintKind.choices)
    value = models.CharField(max_length=200)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_kind_display()}: {self.value}"


class Gap(models.Model):
    """A question the system could not answer.

    Carries no source: a gap is the absence of a claim, and inventing a
    source for it would be fabricated provenance.
    """

    question_text = models.TextField()
    asked_at = models.DateTimeField(auto_now_add=True)
    filled = models.BooleanField(default=False)
    filled_by_turn = models.ForeignKey(
        IntakeTurn,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="filled_gaps",
    )

    def __str__(self):
        return self.question_text[:80]


class Extraction(models.Model):
    """Staging table. Nothing reaches the knowledge models unreviewed."""

    turn = models.ForeignKey(
        IntakeTurn, on_delete=models.CASCADE, related_name="extractions"
    )
    target_model = models.CharField(
        max_length=20, choices=ExtractionTarget.choices
    )
    payload = models.JSONField(help_text="The proposed field values.")
    confidence = models.FloatField(help_text="Expected range 0.0-1.0.")
    supporting_quote = models.TextField(
        blank=True,
        help_text="Verbatim span of the answer that justifies this record. "
        "What makes the extraction auditable rather than merely plausible.",
    )
    status = models.CharField(
        max_length=20,
        choices=ExtractionStatus.choices,
        default=ExtractionStatus.PENDING,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_object_id = models.IntegerField(
        null=True, blank=True, help_text="Set when approved and promoted."
    )

    class Meta:
        ordering = ["-confidence"]

    def __str__(self):
        return f"{self.target_model} from turn {self.turn_id} ({self.status})"
