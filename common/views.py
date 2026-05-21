import cloudinary.uploader
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, permissions

from rest_framework.views import APIView

import json
from django.http import QueryDict
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.views.base import TokenView


@method_decorator(csrf_exempt, name="dispatch")
class CustomTokenView(TokenView):
    def post(self, request, *args, **kwargs):
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                q_data = QueryDict('', mutable=True)
                for key, value in data.items():
                    q_data[key] = value

                request.POST = q_data
            except json.JSONDecodeError:
                pass

        return super().post(request, *args, **kwargs)


class ImageUploadAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        file_obj = request.FILES.get('file')

        if not file_obj:
            return Response(
                {"error": "Vui lòng đính kèm file ảnh với key là 'file'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            upload_result = cloudinary.uploader.upload(file_obj)
            image_url = upload_result.get("secure_url")

            return Response({
                "message": "Upload thành công!",
                "image_url": image_url
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
