# Celery app'i Django ile birlikte yükle
from .celery import app as celery_app

__all__ = ('celery_app',)

