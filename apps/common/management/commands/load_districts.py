from django.core.management import BaseCommand

from apps.common.utils import load_districts


class Command(BaseCommand):
    help = 'Cron testing'

    def handle(self, *args, **options):
        load_districts()
        self.stdout.write(self.style.SUCCESS("Successfully imported districts"))
