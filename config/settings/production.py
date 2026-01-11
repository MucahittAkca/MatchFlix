from .base import *
import os

DEBUG = False

# WhiteNoise - Static files (must be after SecurityMiddleware)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Security - Azure App Service handles SSL at the load balancer level
# So we disable SECURE_SSL_REDIRECT when behind Azure's reverse proxy
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF Trusted Origins for Azure
CSRF_TRUSTED_ORIGINS = [
    'https://*.azurewebsites.net',
    config('SITE_URL', default='https://matchflix-app.azurewebsites.net'),
]

# Azure Blob Storage (optional - for ML model and media)
AZURE_STORAGE_CONNECTION_STRING = config('AZURE_STORAGE_CONNECTION_STRING', default='')
AZURE_CONTAINER_NAME = config('AZURE_CONTAINER_NAME', default='matchflix')

if AZURE_STORAGE_CONNECTION_STRING:
    # ML Model will be downloaded from Azure Blob on startup
    ML_MODEL_AZURE_PATH = 'models/ncf_model.pkl'
    ML_MODEL_MAPPINGS_AZURE_PATH = 'models/ncf_model_mappings.pkl'
    ML_MODEL_ML_MAPPING_AZURE_PATH = 'models/ncf_model_ml_mapping.pkl'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
