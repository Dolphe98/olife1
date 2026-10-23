from django.contrib import admin

from .models import BlogPost, Fragment


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
