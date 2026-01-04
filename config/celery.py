"""
Celery Configuration for MatchFlix
==================================
Redis varsa Redis kullanır, yoksa filesystem broker kullanır.
"""

import os
from celery import Celery
from django.conf import settings

# Django settings modülünü ayarla
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Celery app oluştur
app = Celery('matchflix')

# Django settings'ten ayarları yükle
app.config_from_object('django.conf:settings', namespace='CELERY')

# Tüm registered apps içindeki tasks.py dosyalarını otomatik bul
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug için test task"""
    print(f'Request: {self.request!r}')

