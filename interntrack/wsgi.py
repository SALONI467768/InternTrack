"""
WSGI config for InternTrack AI project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interntrack.settings')
application = get_wsgi_application()
