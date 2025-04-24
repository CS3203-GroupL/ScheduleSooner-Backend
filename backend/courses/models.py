from django.db import models

class Course(models.Model):
    # num = models.IntegerField(null=True, blank=True)
    crn = models.CharField(max_length=20)
    subject = models.CharField(max_length=20)
    course = models.CharField(max_length=20)
    section = models.CharField(max_length=30)
    title = models.CharField(max_length=255)
    instructor = models.CharField(max_length=255)
    
    meeting_dates = models.CharField(max_length=255, null=True, blank=True)
    meeting_time = models.CharField(max_length=50, null=True, blank=True)
    meeting_days = models.CharField(max_length=20, null=True, blank=True)
    meeting_location = models.CharField(max_length=255, null=True, blank=True)
    
    final_days = models.CharField(max_length=10, null=True, blank=True)
    final_time = models.CharField(max_length=50, null=True, blank=True)
    final_date = models.CharField(max_length=50, null=True, blank=True)
    final_location = models.CharField(max_length=255, null=True, blank=True)
    
    seats = models.CharField(max_length=50)
    waitlist = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.subject} {self.course} - {self.title}"

    def get_seat_capacity(self):
        try:
            return int(self.seats.split(' ')[0])
        except ValueError:
            return None

    def get_waitlist_count(self):
        try:
            if 'Waiting' in self.waitlist:
                return int(self.waitlist.split(' ')[0])
            else:
                return 0
        except ValueError:
            return 0
