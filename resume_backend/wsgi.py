import os
import sys
from pathlib import Path

# Add project directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')

# Collect static files on first import
try:
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput', '--clear'])
    execute_from_command_line(['manage.py', 'migrate', '--noinput'])
except Exception as e:
    print(f"Setup warning: {e}")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Vercel handler
app = application
