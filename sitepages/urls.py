from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("fragments/", views.fragments, name="fragments"),
    path("blog/", views.blog, name="blog"),
    path("blog/<int:pk>/", views.blog_post, name="blog_post"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("privacy/", views.privacy, name="privacy"),
    path("copyright/", views.copyright_notice, name="copyright"),
]
