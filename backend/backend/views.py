from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
from django.http import FileResponse
import os


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