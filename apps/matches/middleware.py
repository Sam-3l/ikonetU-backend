from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from urllib.parse import parse_qs
from apps.accounts.models import User

@database_sync_to_async
def get_user_from_token(token_string):
    """
    Get user from cache-based token (matches your TokenAuthentication)
    """
    try:
        # Get user_id from cache using the same key format
        user_id = cache.get(f'auth_token:{token_string}')
        
        if not user_id:
            return AnonymousUser()
        
        # Get the user
        user = User.objects.get(id=user_id)
        return user
    except User.DoesNotExist:
        return AnonymousUser()

class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Get token from query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        # Authenticate user
        scope['user'] = await get_user_from_token(token) if token else AnonymousUser()
        
        return await super().__call__(scope, receive, send)