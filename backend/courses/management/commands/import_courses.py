import csv
from django.core.management.base import BaseCommand
from courses.models import Course  # Adjust if your model has a different name

class Command(BaseCommand):
    help = 'Import courses from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Create a Course object and save it to the database
                Course.objects.create(
                    crn=row['crn'],
                    subject=row['subject'],
                    course=row['course'],
                    section=row['section'],
                    title=row['title'],
                    instructor=row['instructor'],
                    dates=row['dates'],
                    seats=row['seats'],
                    waitlist=row['waitlist']
                )
                self.stdout.write(self.style.SUCCESS(f"Successfully added {row['crn']}"))
