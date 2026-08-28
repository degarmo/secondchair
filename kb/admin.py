from django.contrib import admin

from .models import Claim, Entity, Source


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("label", "kind", "captured_at", "claim_count")
    list_filter = ("kind",)
    search_fields = ("label", "excerpt")

    @admin.display(description="claims")
    def claim_count(self, obj):
        return obj.claims.count()


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ("title", "org", "kind", "period")
    list_filter = ("kind",)
    search_fields = ("title", "org")


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ("text", "entity", "status", "visibility", "source")
    list_filter = ("status", "visibility", "entity__kind")
    search_fields = ("text",)
    list_select_related = ("entity", "source")
