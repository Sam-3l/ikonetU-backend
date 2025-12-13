# This script creates all the __init__.py files for Django apps

import os
from pathlib import Path

apps = [
    'profiles',
    'videos', 
    'signals',
    'matches',
    'legal',
    'reports'
]

BASE_PATH = Path(__file__).resolve().parent.parent / "apps"

base_path = BASE_PATH

for app in apps:
    init_file = os.path.join(base_path, app, '__init__.py')
    os.makedirs(os.path.dirname(init_file), exist_ok=True)
    with open(init_file, 'w') as f:
        f.write(f"default_app_config = 'apps.{app}.apps.{app.capitalize()}Config'\n")
    print(f"Created {init_file}")