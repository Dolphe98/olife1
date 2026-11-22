"""Optional boot tasks for Railway Procfile (seed when SEED_ON_BOOT=true)."""
import os
import sys


def main() -> int:
    if os.environ.get("SEED_ON_BOOT", "").lower() in ("1", "true", "yes"):
        from django.core.management import execute_from_command_line

        execute_from_command_line(["manage.py", "seed_content"])
    return 0


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    sys.exit(main())
