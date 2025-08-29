from django.core.management import BaseCommand

from apps.common.utils import load_regions


class Command(BaseCommand):
    help = 'Cron testing'

    def handle(self, *args, **options):
        load_regions()
        self.stdout.write(self.style.SUCCESS("Successfully imported districts"))
