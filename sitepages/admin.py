from django.contrib import admin

from .models import BlogPost, ContactMessage, Fragment, Subscriber


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "episode", "date_display", "sort_order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "excerpt", "seo_keywords")


@admin.register(Fragment)
class FragmentAdmin(admin.ModelAdmin):
    list_display = ("title", "sort_order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "alt_text")


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
