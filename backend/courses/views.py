from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Course
from .serializers import CourseSerializer
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from .filters import CourseTimeFilter

# Create your views here.

# Handles GET requests for listing and filtering courses
class CourseListView(generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CourseTimeFilter