from django.core.management.base import BaseCommand
from api.models import Project, Insight

class Command(BaseCommand):
    help = 'Generates missing card_image and mini_image thumbnails for existing projects and insights'

    def handle(self, *args, **kwargs):
        self.stdout.write('Checking Projects...')
        projects = Project.objects.exclude(main_image='').filter(card_image='')
        
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
        insights = Insight.objects.exclude(image='').filter(card_image='')
        
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
