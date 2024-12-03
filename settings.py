import os
import sys
import corsheaders
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '6dncg2qm)vv0%i4)a3yrvmbg3*$v)3i6^d0c32du93+4^ba#$i'




# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*', 'https://a011-93-175-7-121.ngrok-free.app']
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
    'builder_form',

    'sms_auth',
    'sms_auth.providers.megafon',

    'rest_framework',
    'rest_framework.authtoken',

    'sslserver',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',

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
        'NAME': 'builder_forms_bd',
        'USER': 'builder_forms',
        # 'NAME': 'firesieht',
        # 'NAME': 'builder_form_database',
        # 'USER': 'firesieht',
    }
}


# DATABASES = {
#          'default': {
#              'ENGINE': 'django.db.backends.mysql',  
#              'NAME': 'combitco_forms',                  
#              'USER': 'forms_user',         
#              'PASSWORD': 'Combit1234!',    
#              'HOST': 'localhost',          
#              'PORT': '3306',               
#          }
#      }
    
 
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
   
    "SMS_DEBUG": True,
    "SMS_DEBUG_CODE":1111,
    "SMS_USER_SERIALIZER": "api.serializers.DefaultUserSerializer",
    "SMS_USER_ALREADY_EXIST": "Пользователь с указаными номером уже существует"

}

BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = "Europe/Moscow"



PAYPAL_CLIENT_ID = 'AWpyl4qJ8yFNqg8hCMBJZJMREMpMLuazo30-N5tOE99Xoxd7PxdynxovWjdIz0X_jOej8Ugy4hUQhwBw'
PAYPAL_SECRET = 'EMkOXp2pjbNq3WrIUpS87-s6DZ50SZBSSsqXqLoD_syJ2-IPlnLsAF7eaNFk8sPAuplHnbbPIPnGWOnN'
PAYPAL_API_URL = 'https://api-m.sandbox.paypal.com' 
PAYPAL_ACCESS_TOKEN = 'A21AALVHHJEkwOFU351jM42RLoDHMbx-TxiytxzxjpvIm9iKSuaPIfVJue4a2KNNBJnMvmPGHKEOCqHKwbCNSUAFNtVIUtKOA'


