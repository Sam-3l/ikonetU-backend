from rest_framework.authentication import SessionAuthentication as DRFSessionAuthentication


class SessionAuthentication(DRFSessionAuthentication):
    """
    Custom session authentication that doesn't enforce CSRF for API calls
    since we're using session-based auth with CORS
    """
    def enforce_csrf(self, request):
        return  # Don't enforce CSRF for API requests