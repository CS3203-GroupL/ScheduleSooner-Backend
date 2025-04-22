import csv
from django.core.management.base import BaseCommand
from courses.models import Course

class Command(BaseCommand):
    help = 'Import courses from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            courses = []

            for row in reader:
                course = Course(
                    crn=row['crn'],
                    subject=row['subject'],
                    course=row['course'],
                    section=row['section'],
                    title=row['title'],
                    instructor=row['instructor'],
                    meeting_dates=row['meeting_dates'],
                    meeting_time=row['meeting_time'],
                    meeting_days=row['meeting_days'],
                    meeting_location=row['meeting_location'],
                    final_days=row['final_days'],
                    final_time=row['final_time'],
                    final_date=row['final_date'],
                    final_location=row['final_location'],
                    seats=row['seats'],
                    waitlist=row['waitlist'],
                )
                courses.append(course)

            Course.objects.bulk_create(courses)
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(courses)} courses'))
