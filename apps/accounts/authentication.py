from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()

class TokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.replace('Bearer ', '')
        
        # Get user_id from cache (token storage)
        user_id = cache.get(f'auth_token:{token}')
        
        if not user_id:
            raise exceptions.AuthenticationFailed('Invalid or expired token')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')
        
        return (user, token)
    
    def authenticate_header(self, request):
        return 'Bearer'