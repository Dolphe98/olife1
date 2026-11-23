import uuid

from django.db import models


class AgentJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    class CreatedBy(models.TextChoices):
        CLI = "cli", "CLI"
        TELEGRAM = "telegram", "Telegram"
        ADMIN = "admin", "Admin"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_name = models.CharField(max_length=64, db_index=True)
    command = models.TextField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    result = models.TextField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    created_by = models.CharField(
        max_length=16,
        choices=CreatedBy.choices,
        default=CreatedBy.CLI,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.agent_name} {self.status} ({self.id})"


class SiteAudit(models.Model):
    """Per-URL history row written by SiteAuditor (Phase 3B)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(max_length=500)
    status_per_check = models.JSONField(default=dict)
    response_times_ms = models.JSONField(default=dict)
    cert_days_remaining = models.IntegerField(null=True, blank=True)
    run_at = models.DateTimeField()
    job = models.ForeignKey(
        AgentJob,
        on_delete=models.CASCADE,
        related_name="site_audits",
    )

    class Meta:
        ordering = ["-run_at"]

    def __str__(self):
        return f"SiteAudit {self.url} @ {self.run_at}"
