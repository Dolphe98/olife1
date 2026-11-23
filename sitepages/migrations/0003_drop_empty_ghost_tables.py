"""Drop empty DATA_MODEL ghost tables that collide with RenameModel BlogPost→Post.

Verified empty on staging before apply. Safe for 0-row tables only.
"""

from django.db import migrations


TABLES = [
    "sitepages_post_categories",
    "sitepages_post_tags",
    "sitepages_post",
    "sitepages_page",
    "sitepages_media",
    "sitepages_category",
    "sitepages_tag",
]


def drop_ghosts(apps, schema_editor):
    existing = set(schema_editor.connection.introspection.table_names())
    quote = schema_editor.quote_name
    with schema_editor.connection.cursor() as cursor:
        for table in TABLES:
            if table not in existing:
                continue
            if schema_editor.connection.vendor == "postgresql":
                cursor.execute(f"DROP TABLE IF EXISTS {quote(table)} CASCADE")
            else:
                cursor.execute(f"DROP TABLE IF EXISTS {quote(table)}")


def noop_reverse(apps, schema_editor):
    # Ghosts intentionally not recreated; forward migration is the source of truth.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("sitepages", "0002_contactmessage_subscriber"),
    ]

    operations = [
        migrations.RunPython(drop_ghosts, noop_reverse),
    ]
