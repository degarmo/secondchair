from django.contrib import admin

from .models import (
    Constraint,
    Extraction,
    Gap,
    IntakeSession,
    IntakeTurn,
    Project,
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


@admin.register(IntakeSession)
class IntakeSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "question_set_version", "started_at", "completed_at")
    list_filter = ("question_set_version", "started_at")
    search_fields = ("question_set_version",)


@admin.register(IntakeTurn)
class IntakeTurnAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "question_text", "answered_at", "source")
    list_filter = ("session", "answered_at")
    search_fields = ("question_text", "answer_text")
    list_select_related = ("session", "source")


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
    """The review queue: status is editable straight from the changelist."""

    list_display = (
        "target_model", "turn", "confidence", "status", "reviewed_at",
        "created_object_id",
    )
    list_display_links = ("target_model",)
    list_editable = ("status",)
    list_filter = ("status", "target_model")
    search_fields = ("payload",)
    list_select_related = ("turn",)
