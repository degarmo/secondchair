import json

from django.contrib import admin, messages
from django.utils.html import format_html

from .services.extraction import promote_extraction, reject_extraction

from .models import (
    ExtractionStatus,
    Constraint,
    Extraction,
    Gap,
    IntakeSession,
    IntakeTurn,
    Project,
    Question,
    Role,
    Skill,
    Source,
    Story,
)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("label", "kind", "captured_on", "uri")
    list_filter = ("kind", "captured_on")
    search_fields = ("label", "uri")
    date_hierarchy = "captured_on"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "priority", "key", "category", "target_model", "active",
        "question_set_version",
    )
    list_display_links = ("key",)
    list_editable = ("active",)
    list_filter = ("question_set_version", "category", "active", "target_model")
    search_fields = ("key", "text")
    ordering = ("question_set_version", "priority")


@admin.register(IntakeSession)
class IntakeSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "question_set_version", "started_at", "completed_at")
    list_filter = ("question_set_version", "started_at")
    search_fields = ("question_set_version",)


@admin.register(IntakeTurn)
class IntakeTurnAdmin(admin.ModelAdmin):
    list_display = (
        "id", "session", "question", "question_text", "answered_at", "source",
    )
    list_filter = ("session", "answered_at", "question__category")
    search_fields = ("question_text", "answer_text", "question__key")
    list_select_related = ("session", "question", "source")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        "title", "org", "start_date", "end_date", "employment_type",
        "visibility", "verified",
    )
    list_filter = ("employment_type", "visibility", "verified", "start_date")
    search_fields = ("title", "org", "summary")
    list_select_related = ("source",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "stack", "visibility", "verified")
    list_filter = ("visibility", "verified", "role")
    search_fields = ("name", "description", "outcome")
    list_select_related = ("role", "source")


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = (
        "title", "role", "project", "themes", "requires_context",
        "visibility", "verified",
    )
    list_filter = ("requires_context", "visibility", "verified", "role", "project")
    search_fields = ("title", "situation", "action", "result")
    list_select_related = ("role", "project", "source")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = (
        "name", "category", "depth", "first_used", "last_used",
        "duration_years", "visibility",
    )
    list_filter = ("category", "depth", "visibility", "verified")
    search_fields = ("name",)
    list_select_related = ("source",)

    @admin.display(description="Years")
    def duration_years(self, obj):
        return obj.duration_years


@admin.register(Constraint)
class ConstraintAdmin(admin.ModelAdmin):
    list_display = ("kind", "value", "visibility", "verified")
    list_filter = ("kind", "visibility", "verified")
    search_fields = ("value", "notes")
    list_select_related = ("source",)


@admin.register(Gap)
class GapAdmin(admin.ModelAdmin):
    list_display = ("question_text", "filled", "filled_by_turn", "asked_at")
    list_filter = ("filled", "asked_at")
    search_fields = ("question_text",)
    list_select_related = ("filled_by_turn",)


@admin.register(Extraction)
class ExtractionAdmin(admin.ModelAdmin):
    """The review queue.

    Nothing here promotes silently: every row's outcome is reported back,
    and a row that fails validation stays pending so it can be corrected in
    the detail view and retried.
    """

    list_display = (
        "target_model", "confidence", "status", "payload_preview",
        "quote_preview", "rejection_reason", "turn", "created_object_id",
    )
    list_display_links = ("target_model",)
    list_editable = ("status",)
    list_filter = ("status", "target_model")
    search_fields = ("payload", "supporting_quote", "rejection_reason")
    list_select_related = ("turn",)
    readonly_fields = ("created_object_id", "reviewed_at")
    actions = ("approve_and_promote", "reject_selected")

    @admin.display(description="Payload")
    def payload_preview(self, obj):
        text = json.dumps(obj.payload, ensure_ascii=False)
        return text if len(text) <= 90 else f"{text[:89]}\u2026"

    @admin.display(description="Supporting quote")
    def quote_preview(self, obj):
        quote = obj.supporting_quote or ""
        shown = quote if len(quote) <= 90 else f"{quote[:89]}\u2026"
        if quote.startswith("[UNVERIFIED] "):
            return format_html("<span style=\"color:#8e2a2a\">{}</span>", shown)
        return shown

    @admin.action(description="Approve and promote")
    def approve_and_promote(self, request, queryset):
        promoted, failures = [], []
        for extraction in queryset:
            obj, errors = promote_extraction(extraction)
            if obj is None:
                failures.append((extraction, errors))
            else:
                promoted.append((extraction, obj))

        if promoted:
            self.message_user(
                request,
                "Promoted {}: {}.".format(
                    len(promoted),
                    "; ".join(
                        f"{e.target_model} #{o.pk} (from extraction {e.pk})"
                        for e, o in promoted
                    ),
                ),
                messages.SUCCESS,
            )
        # Each failure is reported separately with its own reasons -- a
        # partial success reported as one vague warning is how bad records
        # get through.
        for extraction, errors in failures:
            # Report the row's real status: a validation failure leaves it
            # pending and retryable, but an already-reviewed row was never
            # pending to begin with.
            state = (
                "left pending"
                if extraction.status == ExtractionStatus.PENDING
                else f"status unchanged ({extraction.status})"
            )
            self.message_user(
                request,
                f"Extraction {extraction.pk} ({extraction.target_model}) "
                f"not promoted, {state}: {'; '.join(errors)}",
                messages.ERROR,
            )

    @admin.action(description="Reject")
    def reject_selected(self, request, queryset):
        rejected = [
            reject_extraction(e, reason="Rejected from the admin queue").pk
            for e in queryset
        ]
        self.message_user(
            request,
            f"Rejected {len(rejected)} extraction(s): "
            f"{', '.join(str(pk) for pk in rejected)}."
            if rejected
            else "No extractions selected.",
            messages.SUCCESS if rejected else messages.WARNING,
        )
