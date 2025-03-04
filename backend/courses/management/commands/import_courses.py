import csv
from django.core.management.base import BaseCommand
from courses.models import Course  # Import the Course model

class Command(BaseCommand):
    help = 'Import courses from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help="Path to the CSV file")

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)

            # Skip the first row (header)
            next(reader)

            for row in reader:
                # Ensure the row has the correct number of columns
                if len(row) < 10:
                    self.stdout.write(self.style.ERROR(f"Skipping invalid row: {row}"))
                    continue

                # Extract values from the row
                num = int(row[0]) if row[0].isdigit() else None
                crn = row[1]
                subject = row[2]
                course = row[3]
                section = row[4]
                title = row[5]
                instructor = row[6]
                dates = row[7]
                seats = row[8]
                waitlist = row[9]

                # Create and save the Course object
                Course.objects.create(
                    num=num,
                    crn=crn,
                    subject=subject,
                    course=course,
                    section=section,
                    title=title,
                    instructor=instructor,
                    dates=dates,
                    seats=seats,
                    waitlist=waitlist
                )

                self.stdout.write(self.style.SUCCESS(f"Added course: {subject} {course} - {title}"))

        self.stdout.write(self.style.SUCCESS("CSV data successfully imported!"))
