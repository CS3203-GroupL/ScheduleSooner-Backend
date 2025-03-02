from django.db import models

class Course(models.Model):
    num = models.IntegerField(null=True, blank=True)  # Optional integer field
    crn = models.CharField(max_length=10)  # CRN can be a string as it can start with zeros
    subject = models.CharField(max_length=10)
    course = models.CharField(max_length=10)
    section = models.CharField(max_length=10)
    title = models.CharField(max_length=255)
    instructor = models.CharField(max_length=255)
    dates = models.CharField(max_length=255)  # Could be a date range in the future
    seats = models.CharField(max_length=50)  # Storing as string for now (e.g., "9 out of 120")
    waitlist = models.CharField(max_length=50)  # "No Wait List" or "0 Waiting"
    
    def __str__(self):
        return f"{self.subject} {self.course} - {self.title}"

    # Optionally, add a method to parse 'seats' and 'waitlist' to numeric values for processing
    def get_seat_capacity(self):
        try:
            # Extract the number of seats available (before 'out of')
            return int(self.seats.split(' ')[0])
        except ValueError:
            return None

    def get_waitlist_count(self):
        try:
            # Extract the number of people on the waitlist (after 'Waiting' or 'out of')
            if 'Waiting' in self.waitlist:
                return int(self.waitlist.split(' ')[0])
            else:
                return 0
        except ValueError:
            return 0

