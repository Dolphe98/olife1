from django.contrib import admin

from .models import AgentJob


@admin.register(AgentJob)
class AgentJobAdmin(admin.ModelAdmin):
    list_display = ("id", "agent_name", "status", "created_by", "created_at", "duration_ms")
    list_filter = ("status", "agent_name", "created_by")
    search_fields = ("id", "agent_name", "command")
    readonly_fields = ("id", "created_at", "started_at", "finished_at", "duration_ms")
