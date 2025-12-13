"""
Bootstrap script to create all Django app files with proper structure
Run this after setup to generate all necessary model, serializer, view files
"""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent

# App configurations
APP_CONFIGS = {
    'profiles': 'ProfilesConfig',
    'videos': 'VideosConfig',
    'signals': 'SignalsConfig',
    'matches': 'MatchesConfig',
    'legal': 'LegalConfig',
    'reports': 'ReportsConfig',
}

def create_apps_py(app_name, config_name):
    content = f'''from django.apps import AppConfig


class {config_name}(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.{app_name}'
'''
    path = os.path.join(BACKEND_DIR, 'apps', app_name, 'apps.py')
    with open(path, 'w') as f:
        f.write(content)
    print(f'Created {path}')


def create_admin_py(app_name):
    content = '''from django.contrib import admin

# Register your models here.
'''
    path = os.path.join(BACKEND_DIR, 'apps', app_name, 'admin.py')
    with open(path, 'w') as f:
        f.write(content)
    print(f'Created {path}')


def create_models_py(app_name):
    content = '''from django.db import models

# Create your models here.
'''
    path = os.path.join(BACKEND_DIR, 'apps', app_name, 'models.py')
    with open(path, 'w') as f:
        f.write(content)
    print(f'Created {path}')


def create_serializers_py(app_name):
    content = '''from rest_framework import serializers

# Create your serializers here.
'''
    path = os.path.join(BACKEND_DIR, 'apps', app_name, 'serializers.py')
    with open(path, 'w') as f:
        f.write(content)
    print(f'Created {path}')


def create_views_py(app_name):
    content = '''from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# Create your views here.
'''
    path = os.path.join(BACKEND_DIR, 'apps', app_name, 'views.py')
    with open(path, 'w') as f:
        f.write(content)
    print(f'Created {path}')


def create_urls_py(app_name):
    content = '''from django.urls import path
from . import views

urlpatterns = [
    # Add your URL patterns here
]
'''
    path = os.path.join(BACKEND_DIR, 'apps', app_name, 'urls.py')
    with open(path, 'w') as f:
        f.write(content)
    print(f'Created {path}')


def main():
    print("Bootstrapping Django apps...")
    print("=" * 50)
    
    for app_name, config_name in APP_CONFIGS.items():
        print(f"\nCreating files for {app_name}...")
        create_apps_py(app_name, config_name)
        create_admin_py(app_name)
        create_models_py(app_name)
        create_serializers_py(app_name)
        create_views_py(app_name)
        create_urls_py(app_name)
    
    print("\n" + "=" * 50)
    print("Bootstrap complete!")
    print("\nNext steps:")
    print("1. Implement models in each app's models.py")
    print("2. Create serializers in serializers.py")
    print("3. Implement views in views.py")
    print("4. Configure URLs in urls.py")
    print("5. Run: python manage.py makemigrations")
    print("6. Run: python manage.py migrate")


if __name__ == '__main__':
    main()