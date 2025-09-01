from django.core.management.base import BaseCommand
from apps.bot.models import PointScore


class Command(BaseCommand):
    help = 'Set up default data for referral system'

    def handle(self, *args, **options):
        # Create default point score threshold
        point_score, created = PointScore.objects.get_or_create(
            defaults={'points': 5}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created default point score threshold: {point_score.points}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Point score threshold already exists: {point_score.points}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Referral system setup completed successfully!')
        )
