import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User

email = "admin@ikonetu.com"
password = "pass123"

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        password=password,
        name="Admin",
    )
    print(f"✅ Superuser '{email}' created successfully.")
else:
    print(f"ℹ️ User '{email}' already exists, skipping.")
