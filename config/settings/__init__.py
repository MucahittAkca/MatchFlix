import os


# Hangi ayar dosyası kullanılacak.
ENV = os.getenv('DJANGO_ENV', 'development')


if ENV == 'production':
    from .production import *
elif ENV == 'development':
    from .development import *
else:
    from .base import *


