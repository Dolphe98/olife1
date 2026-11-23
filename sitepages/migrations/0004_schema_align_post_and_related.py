import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    Post = apps.get_model("sitepages", "Post")
    Fragment = apps.get_model("sitepages", "Fragment")

    def unique_slug(model, title, pk):
        base = slugify(title)[:200] or "item"
        candidate = base
        n = 2
        while model.objects.filter(slug=candidate).exclude(pk=pk).exists():
            candidate = f"{base}-{n}"
            n += 1
        return candidate

    for post in Post.objects.all():
        if not post.slug:
            post.slug = unique_slug(Post, post.title, post.pk)
            post.save(update_fields=["slug"])

    for frag in Fragment.objects.all():
        if not frag.slug:
            frag.slug = unique_slug(Fragment, frag.title, frag.pk)
            frag.save(update_fields=["slug"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("sitepages", "0003_drop_empty_ghost_tables"),
    ]

    operations = [
        migrations.CreateModel(
            name="Media",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("alt_text", models.CharField(max_length=255)),
                ("storage_path", models.CharField(max_length=512)),
                ("public_url", models.URLField(max_length=500)),
                ("content_type", models.CharField(blank=True, max_length=100)),
                ("width", models.PositiveIntegerField(blank=True, null=True)),
                ("height", models.PositiveIntegerField(blank=True, null=True)),
                ("bytes", models.PositiveIntegerField(blank=True, null=True)),
                ("source", models.CharField(default="migrated-static", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("description", models.TextField(blank=True)),
            ],
            options={"ordering": ["name"], "verbose_name_plural": "categories"},
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60, unique=True)),
                ("slug", models.SlugField(max_length=60, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.RenameModel(old_name="BlogPost", new_name="Post"),
        migrations.AddField(
            model_name="post",
            name="slug",
            field=models.CharField(blank=True, default="", max_length=255, db_index=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="post",
            name="cover",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="posts",
                to="sitepages.media",
            ),
        ),
        migrations.AddField(
            model_name="post",
            name="og_description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="post",
            name="og_title",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="post",
            name="published_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="post",
            name="twitter_card",
            field=models.CharField(default="summary_large_image", max_length=64),
        ),
        migrations.AddField(
            model_name="post",
            name="updated_at",
            field=models.DateTimeField(
                auto_now=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="post",
            name="date_display",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AlterField(
            model_name="post",
            name="image",
            field=models.CharField(
                blank=True,
                help_text="Legacy static image filename under static/images/",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="post",
            name="categories",
            field=models.ManyToManyField(blank=True, related_name="posts", to="sitepages.category"),
        ),
        migrations.AddField(
            model_name="post",
            name="tags",
            field=models.ManyToManyField(blank=True, related_name="posts", to="sitepages.tag"),
        ),
        migrations.AddField(
            model_name="fragment",
            name="slug",
            field=models.CharField(blank=True, default="", max_length=255, db_index=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="fragment",
            name="caption",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="fragment",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="fragment",
            name="media",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="fragments",
                to="sitepages.media",
            ),
        ),
        migrations.AlterField(
            model_name="fragment",
            name="image",
            field=models.CharField(
                help_text="Legacy static image filename under static/images/",
                max_length=255,
            ),
        ),
        migrations.RunPython(populate_slugs, noop_reverse),
        migrations.AlterField(
            model_name="post",
            name="slug",
            field=models.SlugField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name="fragment",
            name="slug",
            field=models.SlugField(max_length=255, unique=True),
        ),
        migrations.CreateModel(
            name="Page",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=255, unique=True)),
                ("content_html", models.TextField(blank=True)),
                ("seo_title", models.CharField(blank=True, max_length=255)),
                ("seo_description", models.TextField(blank=True)),
                ("seo_keywords", models.CharField(blank=True, max_length=512)),
                ("og_title", models.CharField(blank=True, max_length=255)),
                ("og_description", models.TextField(blank=True)),
                ("is_published", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "og_image",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="pages",
                        to="sitepages.media",
                    ),
                ),
            ],
            options={"ordering": ["slug"]},
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(blank=True, max_length=120)),
                ("bio", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "avatar",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="profiles",
                        to="sitepages.media",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Comment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                            ("flagged", "Flagged"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("is_flagged", models.BooleanField(default=False)),
                ("moderated_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "moderated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="moderated_comments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "post",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="sitepages.post",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ContentPipelineItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("post", "Post"),
                            ("fragment", "Fragment"),
                            ("page", "Page"),
                            ("other", "Other"),
                        ],
                        default="post",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("idea", "Idea"),
                            ("draft", "Draft"),
                            ("review", "Review"),
                            ("scheduled", "Scheduled"),
                            ("published", "Published"),
                        ],
                        default="idea",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "linked_post",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="pipeline_items",
                        to="sitepages.post",
                    ),
                ),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="DeployEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("environment", models.CharField(max_length=32)),
                ("action", models.CharField(max_length=32)),
                ("git_sha", models.CharField(blank=True, max_length=64)),
                ("status", models.CharField(max_length=32)),
                ("actor", models.CharField(blank=True, max_length=120)),
                ("meta", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
