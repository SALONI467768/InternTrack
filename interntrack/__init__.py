"""
InternTrack AI Project Initialization
Loads celery application on startup.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
