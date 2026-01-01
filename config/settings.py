import os
from pathlib import Path
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# Parse ALLOWED_HOSTS from comma-separated string
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',') if config('ALLOWED_HOSTS', default='') else []

# Application definition
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'corsheaders',
    'channels',
    'django_filters',
    'storages',
    
    # Local apps
    'apps.accounts',
    'apps.profiles',
    'apps.videos',
    'apps.signals',
    'apps.matches',
    'apps.legal',
    'apps.reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.accounts.middleware.RateLimitMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database
DATABASES = {
    'default': config(
        'DATABASE_URL',
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        cast=dj_database_url.parse
    )
}

# Set connection pooling and SSL for production databases
if not DEBUG and DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3':
    DATABASES['default']['CONN_MAX_AGE'] = 600
    DATABASES['default']['OPTIONS'] = {'sslmode': 'require'}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
]

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# IMPORTANT: Tell WhiteNoise to NOT serve media files
WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_USE_FINDERS = DEBUG

# Media files configuration
if DEBUG:
    # Local storage in development
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
else:
    # Cloudflare R2 / S3 in production
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    # R2 credentials from environment
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL')
    AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN')
    
    # Media URL (public access)
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
    
    # S3/R2 Configuration
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_QUERYSTRING_AUTH = False  # Don't add auth query params to URLs
    AWS_DEFAULT_ACL = 'public-read'  # Make uploads public by default
    AWS_S3_FILE_OVERWRITE = False  # Don't overwrite files with same name
    AWS_S3_REGION_NAME = None  # R2 doesn't use regions like S3

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.accounts.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'EXCEPTION_HANDLER': 'config.exceptions.custom_exception_handler',
}

# Add browsable API in development
if DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )

# CORS settings
# Parse CORS_ALLOWED_ORIGINS from comma-separated string
cors_origins_string = config('CORS_ALLOWED_ORIGINS', default='')
if cors_origins_string:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins_string.split(',') if origin.strip()]
else:
    # Safe defaults for development
    CORS_ALLOWED_ORIGINS = ['http://localhost:5173', 'http://localhost:5000', 'http://localhost:8088/']

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'range',  # Critical for video streaming
]

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 604800  # 1 week
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=not DEBUG, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = config('SESSION_COOKIE_SAMESITE', default='Lax')
SESSION_COOKIE_NAME = 'sessionid'

# CSRF settings
CSRF_COOKIE_SAMESITE = config('SESSION_COOKIE_SAMESITE', default='Lax')  # Use same as session
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=not DEBUG, cast=bool)
CSRF_COOKIE_HTTPONLY = False

# Parse CSRF_TRUSTED_ORIGINS from comma-separated string
csrf_origins_string = config('CSRF_TRUSTED_ORIGINS', default='')
if csrf_origins_string:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins_string.split(',') if origin.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []

# Channels (WebSocket support)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',  # Development
        # 'BACKEND': 'channels_redis.core.RedisChannelLayer',
        # 'CONFIG': {
        #     "hosts": [config('REDIS_URL', default='redis://localhost:6379/0')],
        # },
    },
}

# Rate limiting
RATE_LIMIT_ENABLE = config('RATE_LIMIT_ENABLE', default=True, cast=bool)
RATE_LIMIT_WINDOW = config('RATE_LIMIT_WINDOW', default=60, cast=int)
RATE_LIMIT_MAX_REQUESTS = config('RATE_LIMIT_MAX_REQUESTS', default=5, cast=int)

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'