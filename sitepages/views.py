from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .models import BlogPost, Fragment


def _published_posts():
    return BlogPost.objects.filter(is_published=True)


def _published_fragments():
    return Fragment.objects.filter(is_published=True)


@require_GET
def home(request):
    return render(
        request,
        "sitepages/home.html",
        {
            "latest_fragments": _published_fragments()[:3],
            "latest_posts": _published_posts()[:3],
        },
    )


@require_GET
def fragments(request):
    return render(
        request,
        "sitepages/fragments.html",
        {"fragments": _published_fragments()[:10]},
    )


@require_GET
def blog(request):
    return render(
        request,
        "sitepages/blog.html",
        {"posts": _published_posts()},
    )


@require_GET
def blog_post(request, pk):
    try:
        post = _published_posts().get(pk=pk)
    except BlogPost.DoesNotExist as exc:
        raise Http404("Article not found.") from exc
    return render(
        request,
        "sitepages/blog_post.html",
        {
            "post": post,
            "page_title": post.seo_title or post.title,
            "meta_description": post.seo_description or post.excerpt,
            "meta_keywords": post.seo_keywords,
        },
    )


@require_GET
def about(request):
    return render(request, "sitepages/about.html")


@require_GET
def contact(request):
    return render(
        request,
        "sitepages/contact.html",
        {
            "formspree_endpoint": settings.FORMSPREE_ENDPOINT,
            "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
        },
    )


@require_GET
def privacy(request):
    return render(request, "sitepages/privacy.html")


@require_GET
def copyright_notice(request):
    return render(request, "sitepages/copyright.html")
