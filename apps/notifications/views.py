from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import GotifyApplication


class GotifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        g_app = GotifyApplication.objects.filter(user=request.user).first()

        if not g_app:
            return Response(
                {"error": "Không tìm thấy cấu hình Gotify cho người dùng này."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {"basic_token": g_app.basic_token},
            status=status.HTTP_200_OK
        )
