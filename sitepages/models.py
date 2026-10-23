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
