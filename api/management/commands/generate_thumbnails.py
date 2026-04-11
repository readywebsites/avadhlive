from django.core.management.base import BaseCommand
from api.models import Project, Insight
from django.db.models import Q

class Command(BaseCommand):
    help = 'Generates missing card_image and mini_image thumbnails for existing projects and insights'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Force regeneration of thumbnails even if they already exist.',
        )

    def handle(self, *args, **kwargs):
        overwrite = kwargs['overwrite']

        self.stdout.write('Checking Projects...')
        if overwrite:
            self.stdout.write(self.style.WARNING('OVERWRITE flag set. Regenerating all thumbnails.'))
            projects = Project.objects.exclude(Q(main_image='') | Q(main_image__isnull=True))
        else:
            projects = Project.objects.exclude(Q(main_image='') | Q(main_image__isnull=True)).filter(Q(card_image='') | Q(card_image__isnull=True))
        
        if projects.exists():
            for project in projects:
                self.stdout.write(f'Processing Project: {project.title} ...', ending=' ')
                try:
                    project.make_thumbnails()
                    project.save(update_fields=['card_image', 'mini_image'])
                    self.stdout.write(self.style.SUCCESS('OK'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'FAILED - {str(e)}'))
        else:
            self.stdout.write(self.style.SUCCESS('No Projects require thumbnail generation!'))

        self.stdout.write('\nChecking Insights (Blog/Media)...')
        if overwrite:
            insights = Insight.objects.exclude(Q(image='') | Q(image__isnull=True))
        else:
            insights = Insight.objects.exclude(Q(image='') | Q(image__isnull=True)).filter(Q(card_image='') | Q(card_image__isnull=True))
        
        if insights.exists():
            for insight in insights:
                self.stdout.write(f'Processing Insight: {insight.title} ...', ending=' ')
                try:
                    insight.make_thumbnails()
                    insight.save(update_fields=['card_image', 'mini_image'])
                    self.stdout.write(self.style.SUCCESS('OK'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'FAILED - {str(e)}'))
        else:
            self.stdout.write(self.style.SUCCESS('No Insights require thumbnail generation!'))
