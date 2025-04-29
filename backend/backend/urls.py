"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from courses.views import CourseListView

from backend.views import UserInputView, FileUploadView, FileDownloadView
from backend.views import RegisterView
#from backend.views import csrf  # import CSRF view

schema_view = get_schema_view(
    openapi.Info(
        title="Schedule Sooner API",
        default_version='v1',
        description="Private API docs. You must authenticate via JWT to use them.",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # template 
    path('admin/', admin.site.urls),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # endpoint for courses API
    path('cs/', include('courses.urls')), 
    
    # NEW user input and file APIs
    path('api/user-input/', UserInputView.as_view(), name='user-input'),
    path('api/upload-file/', FileUploadView.as_view(), name='upload-file'),
    path('api/download-file/', FileDownloadView.as_view(), name='download-file'),
    
    # swagger ui & redoc shit
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # user registration API
    path('api/register/', RegisterView.as_view(), name='register'),
    
     # default endpoint for API
    path('', lambda request: JsonResponse({"message": "Welcome to the Schedule Sooner API!"})),
]

