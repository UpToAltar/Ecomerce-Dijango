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
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'OPTIONS': {'context_processors': ['django.template.context_processors.debug', 'django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages'], 'loaders': ['django.template.loaders.app_directories.Loader']}}]
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'cart_db', 'USER': os.environ.get('DB_USER', 'admin'), 'PASSWORD': os.environ.get('DB_PASSWORD', 'changeme'), 'HOST': os.environ.get('DB_HOST', 'localhost'), 'PORT': os.environ.get('DB_PORT', '5432')}}
REST_FRAMEWORK = {'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',), 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination', 'PAGE_SIZE': 20}
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
CORS_ALLOW_ALL_ORIGINS = True
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
