from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts.views import serve_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/founder/', include('apps.profiles.urls.founder')),
    path('api/investor/', include('apps.profiles.urls.investor')),
    path('api/videos/', include('apps.videos.urls')),
    path('api/signals/', include('apps.signals.urls')),
    path('api/matches/', include('apps.matches.urls')),
    path('api/legal/', include('apps.legal.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/admin/', include('apps.videos.admin_urls')),
    path('api/admin/', include('apps.reports.admin_urls')),
    path('api/dashboard/', include('apps.accounts.dashboard_urls')),
    path('api/user/', include('apps.accounts.user_urls')),
]