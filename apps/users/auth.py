from django.conf import settings
from django.core.cache import cache
from oauth2_provider.contrib.rest_framework import OAuth2Authentication


class CachedOAuth2Authentication(OAuth2Authentication):

    def authenticate(self, request):
        token_string = request.META.get("HTTP_AUTHORIZATION", "").split(" ")[-1]

        if not token_string:
            return None

        cache_key = f"oauth2_token:{token_string}"
        cached_user = cache.get(cache_key)

        if cached_user:
            return cached_user

        result = super().authenticate(request)

        if result:
            cache.set(cache_key, result, timeout=settings.TOKEN_CACHING_SECONDS)

        return result
