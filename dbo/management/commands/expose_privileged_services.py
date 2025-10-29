from django.core.management.base import BaseCommand
from django.db import transaction

from dbo.models import Service


class Command(BaseCommand):
    help = (
        "Sets all privileged services (is_privileged=True) to public (is_public=True) "
        "so they become visible to non-admin users."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without modifying data",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        qs = Service.objects.filter(is_privileged=True, is_public=False, is_active=True)
        total = qs.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No privileged non-public active services found."))
            return

        self.stdout.write(f"Found {total} privileged non-public active services.")

        if dry_run:
            preview = list(qs.values_list("id", "name"))[:20]
            for sid, name in preview:
                self.stdout.write(f"Would set is_public=True: [{sid}] {name}")
            if total > 20:
                self.stdout.write(f"... and {total - 20} more")
            self.stdout.write(self.style.SUCCESS("Dry run completed. No changes made."))
            return

        with transaction.atomic():
            updated = qs.update(is_public=True)

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} services: set is_public=True"))


