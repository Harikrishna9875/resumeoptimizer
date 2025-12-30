import os
import django
from django.conf import settings
from django.http import HttpResponse
from django.urls import path
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')

# Setup Django
django.setup()

application = get_wsgi_application()

def main(request):
    return HttpResponse("Resume Optimizer Live!", status=200)

# Serve static files
def serve_static(request):
    if request.path.startswith('/static/'):
        return HttpResponse("Static files not served in serverless", status=404)
    return main(request)

# All routes to Django
def app(environ, start_response):
    return application(environ, start_response)
