from django.contrib import admin

from .models import (
    Category,
    Comment,
    ContactMessage,
    ContentPipelineItem,
    DeployEvent,
    Fragment,
    Media,
    Page,
    Post,
    Profile,
    Subscriber,
    Tag,
)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "episode", "date_display", "sort_order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "excerpt", "seo_keywords", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Fragment)
class FragmentAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "sort_order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "alt_text", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("email", "subject", "body", "first_name", "last_name")


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "status", "source", "sync_provider", "created_at")
    list_filter = ("status", "source")
    search_fields = ("email",)


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "content_type", "created_at")
    search_fields = ("title", "alt_text", "storage_path")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "updated_at")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "updated_at")
    search_fields = ("display_name", "user__username", "user__email")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "status", "is_flagged", "created_at")
    list_filter = ("status", "is_flagged")
    search_fields = ("body", "author__username")


@admin.register(ContentPipelineItem)
class ContentPipelineItemAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "status", "updated_at")
    list_filter = ("kind", "status")


@admin.register(DeployEvent)
class DeployEventAdmin(admin.ModelAdmin):
    list_display = ("environment", "action", "status", "git_sha", "created_at")
    list_filter = ("environment", "action", "status")
