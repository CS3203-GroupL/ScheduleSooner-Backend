import django_filters
from .models import Course
from datetime import datetime

# this class is used to filter the courses based on the meeting days and times
class CourseTimeFilter(django_filters.FilterSet):
    start_time = django_filters.TimeFilter(method='filter_by_start')
    end_time = django_filters.TimeFilter(method='filter_by_end')
    meeting_days = django_filters.CharFilter(method='filter_meeting_days')
    instructor = django_filters.CharFilter(method='filter_by_instructor')
    course = django_filters.CharFilter(lookup_expr='icontains')

    
    class Meta:
        model = Course
        fields = ['meeting_days']

    def extract_start(self, time_range):
        try:
            return datetime.strptime(time_range.split('-')[0].strip(), '%I:%M %p').time()
        except:
            return None

    def extract_end(self, time_range):
        try:
            return datetime.strptime(time_range.split('-')[1].strip(), '%I:%M %p').time()
        except:
            return None

    def filter_by_start(self, queryset, name, value):
        return queryset.filter(
            meeting_time__isnull=False
        ).filter(
            meeting_time__regex=r'^\s*([0-9]+:[0-9]+ [ap]m)\s*-\s*([0-9]+:[0-9]+ [ap]m)'
        ).filter(
            meeting_time__iregex=fr'^{value.strftime("%-I:%M %p")}'
        )

    def filter_by_end(self, queryset, name, value):
        return queryset.filter(
            meeting_time__icontains=value.strftime("%-I:%M %p")
        )
        
    def filter_meeting_days(self, queryset, name, value):
        return queryset.filter(meeting_days__iexact=value)
    
    def filter_by_instructor(self, queryset, name, value):
        return queryset.filter(instructor__icontains=value.strip())

