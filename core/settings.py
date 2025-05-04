import os
from pathlib import Path
from typing import Optional

import oracledb
from decouple import config

from core.openapi_metadata import SETTINGS_METADATA as OPENAPI_SETTINGS

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Define the path to the logs folder
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Check if the logs folder exists, if not, create it
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default="putyourownkey")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=False, cast=bool)

WHITELIST_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="http://127.0.0.1:8000").split(
    " "
)

ALLOWED_HOSTS = WHITELIST_HOSTS if not DEBUG else ["*"]

AUTH_USER_MODEL = "auth_users.User"

CORS_ALLOW_ALL_ORIGINS = DEBUG

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://ossapi.waltonbd.com:8000",
    "https://ossapi.waltonbd.com:8000",
    "https://ossapi.waltonbd.com",
    "http://192.168.117.126:3000",
    "https://192.168.117.126:3000",
    "http://192.168.117.126",
    "https://192.168.117.126",
]

CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "PATCH",
    "POST",
    "PUT",
)

HRMS_API_ENDPOINT = config("EXT_HRMS_API_LINK")

# Application definition

INSTALLED_APPS = [
    # "daphne",
    # internals
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    # own apps
    "auth_users",
    "pms",
    "dropdown_repository",
    "recommendation_engine",
    "menu",
    "tms",
    # 3rd party apps,
    "oauth2_provider",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "django_extensions",
    "simple_history",
    "django_celery_results",
    "django_celery_beat",
    "django_filters",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.common.CommonMiddleware",
    # custom & third-party middlewares
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# ASGI_APPLICATION = "core.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.oracle",
        "NAME": config("DB_SID"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT"),
    },
}

# django restframework configs

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardResultSetPagination",
    "NON_FIELD_ERRORS_KEY": "error",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": (
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "djangorestframework_camel_case.parser.CamelCaseMultiPartParser",
        "djangorestframework_camel_case.parser.FormParser",
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
    ),
    "JSON_UNDERSCOREIZE": {
        "ignore_keys": (
            "other_1",
            "other_1_desc",
            "other_2",
            "other_2_desc",
            "other_3",
            "other_3_desc",
        ),
    },
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

# Oauth2 Settings
LOGIN_URL = "/admin/login/"
OAUTH_SCOPES = "read create update remove groups openid introspection"
PMS_NEXTJS_CLIENT_ID = config("CLIENT_ID")
PMS_NEXTJS_CLIENT_SECRET = SECRET_KEY
PMS_NEXTJS_APP_NAME = config("APP_NAME")
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10024

oauth_dir = BASE_DIR / "oauth/oidc.pem"

try:
    if not oauth_dir.exists():
        from .services.utils import generate_rsa_key, save_key

        oauth_dir.parent.mkdir(parents=True)

        pem = generate_rsa_key()
        save_key(pem, oauth_dir)
except Exception as exc:
    raise exc

try:
    with open(oauth_dir, mode="rb") as f:
        OIDC_RSA_PRIVATE_KEY = f.read().decode()
except FileNotFoundError as err:
    raise FileNotFoundError(
        "RSA Private Key is required for the OAuth2 setup."
    ) from err


def make_seconds(*, day: Optional[int] = None, minute: Optional[int] = None) -> int:
    """helper function for converting day and minute in seconds"""
    if day and minute and day >= 0 and minute >= 0:
        seconds = int(day * 24 * 60 * 60) + int(minute * 60)
    elif day and day > 0 and not minute:
        seconds = int(day * 24 * 60 * 60)
    elif minute and minute > 0 and not day:
        seconds = int(minute * 60)
    else:
        raise ValueError("Either day or minute must be a non-negative integer")
    return seconds


OAUTH2_PROVIDER = {
    "SCOPES": {
        "read": "Read scope",
        "create": "Create new scope",
        "update": "Update existing scope",
        "remove": "Remove existing scope",
        "groups": "Access to your groups",
        "openid": "Open ID Connect",
        "introspection": "Introspect token scope",
    },
    "OIDC_ENABLED": True,
    "OIDC_RSA_PRIVATE_KEY": OIDC_RSA_PRIVATE_KEY,
    "ALLOWED_SCHEMES": ["http"],
    "ALLOWED_REDIRECT_URI_SCHEMES": ["http"],
    "AUTHORIZATION_CODE_EXPIRE_SECONDS": make_seconds(minute=1),
    "ACCESS_TOKEN_EXPIRE_SECONDS": make_seconds(day=5),
    "REFRESH_TOKEN_EXPIRE_SECONDS": make_seconds(day=7),
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# localization configs
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_L10N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# statics configs

STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# EMAIL Configurations
MAIL_SENDER_ADDR = "support@waltondigitech.com"
SMTP_HOST = config("SMTP_HOST")
SMTP_PORT = config("SMTP_PORT", cast=int)
SMTP_USERNAME = config("SMTP_USERNAME")
SMTP_PASSWORD = config("SMTP_PASSWORD")

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    **OPENAPI_SETTINGS,
    # Oauth2 related settings. used for example by django-oauth2-toolkit.
    # https://spec.openapis.org/oas/v3.0.3#oauthFlowsObject
    # , "authorization_code"
    "OAUTH2_FLOWS": ["password"],
    "OAUTH2_AUTHORIZATION_URL": "/oauth2/authorize/",
    "OAUTH2_TOKEN_URL": "/oauth2/token/",
    "OAUTH2_REFRESH_URL": "/oauth2/token/",
    "OAUTH2_SCOPES": OAUTH_SCOPES.split(" "),
    "SWAGGER_UI_OAUTH2_CONFIG": {
        "clientId": PMS_NEXTJS_CLIENT_ID,
        "clientSecret": PMS_NEXTJS_CLIENT_SECRET,
        "appName": PMS_NEXTJS_APP_NAME,
        "scopeSeparator": " ",
        "scopes": OAUTH_SCOPES,
        "usePkceWithAuthorizationCodeGrant": "true",
    },
}

# celery Configurations
CELERY_BROKER_URL = config("CELERY_BROKER_URL")
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Dhaka"
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_EXTENDED = True

# logging configs
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
        "require_debug_true": {"()": "django.utils.log.RequireDebugTrue"},
    },
    "formatters": {
        "main_formatter": {
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s "
            "(%(filename)s:%(lineno)d)",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "main_formatter",
        },
        "production_file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/main.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 7,
            "formatter": "main_formatter",
            "filters": ["require_debug_false"],
        },
        "debug_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/debug.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 7,
            "formatter": "main_formatter",
            "filters": ["require_debug_true"],
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "production_file", "debug_file"],
            "level": "DEBUG",
        },
    },
}


# EBS Oracle Settings
try:
    oracledb.init_oracle_client(
        lib_dir=config("EBS_ORCL_INSTANT_CLIENT_PATH"),
    )
    EBS_CONN_PARAMS = oracledb.ConnectParams(
        user=config("EBS_USERNAME"),
        password=config("EBS_PASSWD"),
        host=config("EBS_HOST"),
        port=config("EBS_PORT"),
        service_name=config("EBS_SERVICE_NAME"),
    )
except Exception as exc:
    raise exc from exc

# For Menu Work
HEADER_AUTH_KEY = "Authorization"
