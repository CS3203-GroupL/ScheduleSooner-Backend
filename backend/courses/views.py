from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Course
from .serializers import CourseSerializer
from .filters import CourseTimeFilter

# Handles GET requests for listing and filtering courses
class CourseListView(generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CourseTimeFilter
    renderer_classes = [JSONRenderer]
    
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('meeting_days', openapi.IN_QUERY, description="Filter by meeting days (e.g., MWF)", type=openapi.TYPE_STRING),
        openapi.Parameter('start_time', openapi.IN_QUERY, description="Start time in format HH:MM (24-Hour Clock)", type=openapi.TYPE_STRING),
        openapi.Parameter('end_time', openapi.IN_QUERY, description="End time in format HH:MM (24-Hour Clock)", type=openapi.TYPE_STRING),
        openapi.Parameter('instructor', openapi.IN_QUERY, description="Filter by instructor name (e.g. Sridhar)", type=openapi.TYPE_STRING),
        openapi.Parameter('course', openapi.IN_QUERY, description="Filter by course number (e.g. 2413)", type=openapi.TYPE_STRING),
    ])
    
    def get(self, request, *args, **kwargs):
        if request.accepted_renderer.format == 'html':
            # If HTML is requested, serve as JSON to avoid missing template
            request.accepted_renderer = JSONRenderer()
        return super().get(request, *args, **kwargs)
    
# Handles GET requests for a single course
class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer