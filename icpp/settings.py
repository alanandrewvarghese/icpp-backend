import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import timedelta

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = True

ALLOWED_HOSTS = ['*']

AUTH_USER_MODEL = 'accounts.User'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework',
    'corsheaders',

    # Custom apps
    'apps.common',
    'apps.accounts',
    'apps.lessons',
    'apps.sandbox',
    'apps.progress',
    'apps.badges',
    'apps.analytics',
    'apps.support',
    'apps.quiz',
    'apps.status',
]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('PY_INTERACT_EMAIL')
EMAIL_HOST_PASSWORD = os.getenv('PY_INTERACT_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

FRONTEND_URL = os.getenv('FRONTEND_URL')
BASE_URL = os.getenv('BASE_URL')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'icpp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'icpp.wsgi.application'


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "icpp-two",
        "USER": "postgres",
        "PASSWORD": "root",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=120),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": os.getenv("SIGNING_KEY"),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

LOG_DIR = f'{BASE_DIR}/logs'

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    'formatters': {
        'default': {
            'format': '{levelname} \nTime: {asctime} \nModule: {module} \nMessage: {message}',
            'style': '{',
        },
    },

    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR}/general.log",
            "formatter": "default"
        },
        "applogs": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR}/apps.log",
            "formatter": "default",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },

    "loggers": {
        "accounts": {
            "handlers": ["applogs", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "lessons": {
            "handlers": ["applogs", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "sandbox": {
            "handlers": ["applogs", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "progress": {
            "handlers": ["applogs", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "badges": {
            "handlers": ["applogs", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "analytics": {
            "handlers": ["applogs", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "support": {
            "handlers": ["applogs", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "quiz": {
            "handlers": ["applogs", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "status": {
            "handlers": ["applogs", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
