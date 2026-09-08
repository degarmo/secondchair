from django.contrib import admin

from agent.models import InterviewLog


@admin.register(InterviewLog)
class InterviewLogAdmin(admin.ModelAdmin):
    list_display = ["question", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["question"]
    date_hierarchy = "created_at"
    readonly_fields = ["session_id", "question", "answer", "ip_hash", "created_at"]

    def has_add_permission(self, request):
        # Rows come from the endpoint, never from a person typing them in.
        return False

    def has_change_permission(self, request, obj=None):
        return False
