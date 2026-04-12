import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1')
ALLOWED_HOSTS = ['*']
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'rest_framework', 'corsheaders', 'domain', 'application',
]
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', 'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'notification_db', 'USER': os.environ.get('DB_USER', 'admin'), 'PASSWORD': os.environ.get('DB_PASSWORD', 'changeme'), 'HOST': os.environ.get('DB_HOST', 'postgres-notification'), 'PORT': os.environ.get('DB_PORT', '5432')}}
CORS_ALLOW_ALL_ORIGINS = True
STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
