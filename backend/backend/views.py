import os
from django.http import JsonResponse
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework import status

from django.http import FileResponse
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import StreamingHttpResponse


import subprocess
import json

# POST and GET User Input
class UserInputView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        global SAVED_INPUT
        SAVED_INPUT = request.data.get('query', '')
        return Response({"message": "User input saved successfully."})

    def get(self, request):
        return Response({"user_input": SAVED_INPUT})


# POST a File
class FileUploadView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file_obj = request.FILES.get('file')

        if not file_obj:
            return Response({"error": "No file uploaded"}, status=400)

        save_path = os.path.join("uploaded_files", file_obj.name)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        return Response({"message": f"File '{file_obj.name}' uploaded successfully."})


# GET a File
class FileDownloadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        filename = request.query_params.get('filename')
        if not filename:
            return Response({"error": "No filename provided"}, status=400)

        filepath = os.path.join("uploaded_files", filename)
        if not os.path.exists(filepath):
            return Response({"error": "File not found"}, status=404)

        return FileResponse(open(filepath, 'rb'), as_attachment=True, filename=filename)
    
# User Registration
class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({"error": "Username and password required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password)
        return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
    
BASE_DIR = settings.BASE_DIR
OUTPUTS_DIR = os.path.join(BASE_DIR, "scheduler-test", "outputs")
SCHEDULER_TEST_DIR = os.path.join(BASE_DIR, "scheduler-test")

@csrf_exempt
def handle_user_input(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)

    try:
        body = json.loads(request.body)
        user_query = body.get("query")
        if not user_query:
            return JsonResponse({'error': 'Missing query'}, status=400)

        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        input_path = os.path.join(OUTPUTS_DIR, 'user_input.json')
        with open(input_path, "w") as f:
            json.dump({"user_input": user_query}, f)

        # Clear old schedule if it exists
        final_schedule_path = os.path.join(OUTPUTS_DIR, "final_schedule.json")
        if os.path.exists(final_schedule_path):
            try:
                os.remove(final_schedule_path)
                print("🗑️ Old final_schedule.json deleted before processing")
            except Exception as e:
                print("⚠️ Could not delete old final_schedule.json:", e)

        # ✅ Run schedule generation inline (Render-safe)
        import sys
        if SCHEDULER_TEST_DIR not in sys.path:
            sys.path.append(SCHEDULER_TEST_DIR)
        import subset

        subset.main()

        return JsonResponse({"status": "processing complete"})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def download_file(request):
    filename = request.GET.get("filename")
    if not filename:
        return JsonResponse({"error": "No filename provided"}, status=400)

    file_path = os.path.join(OUTPUTS_DIR, filename)
    if not os.path.exists(file_path):
        return JsonResponse({"error": "File not found"}, status=404)

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        return JsonResponse({"error": f"Could not read file: {str(e)}"}, status=500)

    # ✅ Delete after reading
    try:
        os.remove(file_path)
        print(f"🗑️ Deleted {filename} after sending it")
    except Exception as e:
        print(f"⚠️ Could not delete {filename}: {e}")

    return JsonResponse(data, safe=False)