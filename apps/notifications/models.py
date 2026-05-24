from django.db import models

from common.models import BaseModel


class GotifyApplication(BaseModel):
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name="gotify_app")
    app_id = models.IntegerField(null=True)
    app_token = models.CharField(max_length=255, unique=True)
    basic_token = models.CharField(max_length=255, null=True)

    class Meta:
        ordering = ["-pk"]

    def __str__(self):
        return f"GotifyApp({self.user})"
