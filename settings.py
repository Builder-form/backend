import os
import sys
import corsheaders
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '6dncg2qm)vv0%i4)a3yrvmbg3*$v)3i6^d0c32du93+4^ba#$i'

CSRF_TRUSTED_ORIGINS = ['https://*.gracey.ru','https://*.gracey.ru:4002' ]



# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']
CORS_ORIGIN_ALLOW_ALL = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'user',
    
    'grace',

    'sms_auth',
    'sms_auth.providers.megafon',

    'rest_framework',
    'rest_framework.authtoken',

    'sslserver',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',

]

ROOT_URLCONF = 'urls'

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

WSGI_APPLICATION = 'wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'demo', 'db.sqlite3'),
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'firesieht',
        'USER': 'firesieht',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'

REST_FRAMEWORK = {
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_METADATA_CLASS': 'rest_framework.metadata.SimpleMetadata',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),

    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',

    ),
    'PAGE_SIZE': 20,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DATETIME_FORMAT': '%s',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ]
}


AUTH_USER_MODEL = 'user.User'

SMS_AUTH_SETTINGS = {
    "SMS_CELERY_FILE_NAME": "run_celery",
    "SMS_AUTH_SUCCESS_KEY": "jwt_token",
    "SMS_AUTH_PROVIDER_FROM": "79587747394",
    "SMS_PROVIDER_URL":'http://api.exolve.ru/messaging/v1/SendSMS',
   
    "SMS_DEBUG": False,
    "SMS_USER_SERIALIZER": "api.serializers.DefaultUserSerializer",
    "SMS_USER_ALREADY_EXIST": "Пользователь с указаными номером уже существует"

}

BITRIX_URL = 'https://gracerussia.bitrix24.ru/rest/18/nxa54xtae7cw3bs8/'
BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = "Europe/Moscow"


CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRFToken']
CORS_ALLOW_CREDENTIALS = True

DELTATIME_TESTPERIOD = 1 #в днях - время оплаты тестового периода (раз в день и тд)
DELTATIME_ACTIVEPERIOD = 7 #в днях - время оплаты основго периода(раз в неделю и тд)
DELTATIME_PAYMENTNURSEPERIOD = 1 #в часах
DELTATIME_PAYMENT_CALLS= 1 # в часах - задержка между следующим платежом и выплатой сиделке

CLOUDPAYMENTS_PUBLIC_ID = 'pk_a2d44a7570fe7490cfe41bb85f660' # Прием платеежй
CLOUDPAYMENTS_PASSWORD = 'b3185a124e9a9a4d80183156216221f8'

CLOUDPAYMENTS_SALARY_PUBLIC_ID = 'pk_f3458b2cceee2b656a28cb5fbd49c' #ДЛЯ ВЫПЛАТЫ СИДЕЛКАМ
CLOUDPAYMENTS_SALARY_PASSWORD = 'd69ab4a9e872f527a818d8b0198b716f'

