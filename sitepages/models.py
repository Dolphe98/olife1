from django.db import models


class BlogPost(models.Model):
    title = models.CharField(max_length=255)
    episode = models.CharField(max_length=32, blank=True)
    excerpt = models.TextField()
    date_display = models.CharField(max_length=64)
    image = models.CharField(max_length=255, help_text="Static image filename under static/images/")
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    seo_keywords = models.CharField(max_length=512, blank=True)
    content_html = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sort_order", "-id"]

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    STATUS_NEW = "new"
    STATUS_READ = "read"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_READ, "Read"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=64, blank=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} — {self.email}"


class Subscriber(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_UNSUBSCRIBED = "unsubscribed"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_UNSUBSCRIBED, "Unsubscribed"),
    ]

    email = models.EmailField(unique=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )
    source = models.CharField(max_length=64, default="web")
    # Future Beehiiv/Mailchimp bolt-on without a schema migration
    sync_provider = models.CharField(max_length=64, blank=True)
    sync_external_id = models.CharField(max_length=255, blank=True)
    sync_payload = models.JSONField(default=dict, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


class Fragment(models.Model):
    title = models.CharField(max_length=255)
    alt_text = models.CharField(max_length=255)
    image = models.CharField(max_length=255, help_text="Static image filename under static/images/")
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["-sort_order", "-id"]

    def __str__(self):
        return self.title
