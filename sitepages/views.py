from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .models import ContactMessage, Fragment, Post, Subscriber


def _published_posts():
    return Post.objects.filter(is_published=True)


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
    except Post.DoesNotExist as exc:
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


@require_http_methods(["GET", "POST"])
def contact(request):
    if request.method == "POST":
        form_type = request.POST.get("form_type", "contact")
        if form_type == "newsletter" and settings.FEATURE_NEWSLETTER:
            email = (request.POST.get("email") or "").strip().lower()
            if email:
                Subscriber.objects.get_or_create(
                    email=email,
                    defaults={"source": "web", "status": Subscriber.STATUS_ACTIVE},
                )
                messages.success(request, "Thanks for subscribing to Olife.")
            return redirect("contact")

        msg = ContactMessage.objects.create(
            first_name=(request.POST.get("first_name") or "").strip(),
            last_name=(request.POST.get("last_name") or "").strip(),
            email=(request.POST.get("email") or "").strip(),
            phone=(request.POST.get("phone") or "").strip(),
            subject=(request.POST.get("subject") or "").strip() or "Contact",
            body=(request.POST.get("message") or "").strip(),
        )
        if settings.CONTACT_NOTIFY_EMAIL:
            send_mail(
                subject=f"[Olife] {msg.subject}",
                message=(
                    f"From: {msg.first_name} {msg.last_name} <{msg.email}>\n"
                    f"Phone: {msg.phone}\n\n{msg.body}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_NOTIFY_EMAIL],
                fail_silently=True,
            )
        messages.success(request, "Message sent. Thank you.")
        return redirect("contact")

    return render(
        request,
        "sitepages/contact.html",
        {
            "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
        },
    )


@require_GET
def privacy(request):
    return render(request, "sitepages/privacy.html")


@require_GET
def copyright_notice(request):
    return render(request, "sitepages/copyright.html")
