import cloudinary.uploader
from django.conf import settings
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, permissions

from rest_framework.views import APIView

import json
from django.http import QueryDict, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.views.base import TokenView


@method_decorator(csrf_exempt, name="dispatch")
class CustomTokenView(TokenView):
    def post(self, request, *args, **kwargs):
        if request.content_type == "application/json":
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "invalid_json"}, status=400)
        else:
            data = request.POST.copy()

        data["client_id"] = settings.CLIENT_ID
        data["client_secret"] = settings.CLIENT_SECRET

        q_data = QueryDict("", mutable=True)
        q_data.update(data)
        request.POST = q_data

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
