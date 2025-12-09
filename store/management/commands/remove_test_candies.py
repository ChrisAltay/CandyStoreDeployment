from django.core.management.base import BaseCommand
from store.models import Candy


class Command(BaseCommand):
    help = "Removes test candies from the database"

    def handle(self, *args, **options):
        test_names = ["Debug Candy", "Order Flow Candy", "Test Candy"]

        for name in test_names:
            deleted_count, _ = Candy.objects.filter(name=name).delete()
            if deleted_count > 0:
                self.stdout.write(self.style.SUCCESS(f'Successfully deleted "{name}"'))
            else:
                self.stdout.write(self.style.WARNING(f'"{name}" not found'))
