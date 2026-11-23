from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Media(models.Model):
    title = models.CharField(max_length=255)
    alt_text = models.CharField(max_length=255)
    storage_path = models.CharField(max_length=512)
    public_url = models.URLField(max_length=500)
    content_type = models.CharField(max_length=100, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    bytes = models.PositiveIntegerField(null=True, blank=True)
    source = models.CharField(max_length=64, default="migrated-static")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Post(models.Model):
    """Canonical post model (formerly BlogPost). Table: sitepages_post."""

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    episode = models.CharField(max_length=32, blank=True)
    excerpt = models.TextField()
    content_html = models.TextField()
    # Legacy static filename until Phase 6 Supabase media cutover
    image = models.CharField(
        max_length=255,
        blank=True,
        help_text="Legacy static image filename under static/images/",
    )
    cover = models.ForeignKey(
        Media,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="posts",
    )
    categories = models.ManyToManyField(Category, blank=True, related_name="posts")
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    seo_keywords = models.CharField(max_length=512, blank=True)
    og_title = models.CharField(max_length=255, blank=True)
    og_description = models.TextField(blank=True)
    twitter_card = models.CharField(max_length=64, default="summary_large_image")
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)
    date_display = models.CharField(max_length=64, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-sort_order", "-id"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "post"
            candidate = base
            n = 2
            while Post.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{n}"
                n += 1
            self.slug = candidate
        super().save(*args, **kwargs)


class Fragment(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    alt_text = models.CharField(max_length=255)
    # Legacy static filename until Phase 6 media cutover
    image = models.CharField(
        max_length=255,
        help_text="Legacy static image filename under static/images/",
    )
    media = models.ForeignKey(
        Media,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fragments",
    )
    caption = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sort_order", "-id"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "fragment"
            candidate = base
            n = 2
            while Fragment.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{n}"
                n += 1
            self.slug = candidate
        super().save(*args, **kwargs)


class Page(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content_html = models.TextField(blank=True)
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    seo_keywords = models.CharField(max_length=512, blank=True)
    og_title = models.CharField(max_length=255, blank=True)
    og_description = models.TextField(blank=True)
    og_image = models.ForeignKey(
        Media,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pages",
    )
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.title


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ForeignKey(
        Media,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="profiles",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or self.user.get_username()


class Comment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_FLAGGED = "flagged"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_FLAGGED, "Flagged"),
    ]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    body = models.TextField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    is_flagged = models.BooleanField(default=False)
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="moderated_comments",
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment on {self.post_id} by {self.author_id}"


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
    sync_provider = models.CharField(max_length=64, blank=True)
    sync_external_id = models.CharField(max_length=255, blank=True)
    sync_payload = models.JSONField(default=dict, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


class ContentPipelineItem(models.Model):
    KIND_CHOICES = [
        ("post", "Post"),
        ("fragment", "Fragment"),
        ("page", "Page"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("idea", "Idea"),
        ("draft", "Draft"),
        ("review", "Review"),
        ("scheduled", "Scheduled"),
        ("published", "Published"),
    ]

    title = models.CharField(max_length=255)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="post")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="idea")
    linked_post = models.ForeignKey(
        Post,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pipeline_items",
    )
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class DeployEvent(models.Model):
    environment = models.CharField(max_length=32)
    action = models.CharField(max_length=32)
    git_sha = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=32)
    actor = models.CharField(max_length=120, blank=True)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.environment}:{self.action}:{self.status}"
