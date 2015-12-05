from oby.settings.common import *


# HOSTING + AUTHENTICATION
ADMINS = (
    ("JP", "halis@obystudio.com"),
)
MANAGERS = ADMINS
ALLOWED_HOSTS = [
    'www.obystudio.com',
    'obystudio.com',
    '*.obystudio.com',
    '127.0.0.1',
    '52.2.52.114',  # AWS Elastic IP
]
CORS_URLS_REGEX = r'^/hide/oby/api/.*$'
FULL_DOMAIN_NAME = 'www.obystudio.com'


# S S L  S E C U R I T Y
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_SECONDS = 0
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_HOST = None
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False


# S T R I P E
STRIPE_SECRET_KEY = 'sk_live_6OlOtvEapbxPwcf1CZATzOXA'


# E M A I L
EMAIL_HOST = 'smtp.gmail.com'  # 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'halis@obystudio.com'  # 'sendgrid_username'
EMAIL_HOST_PASSWORD = '. Hockey18 .'  # 'sendgrid_password'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None
EMAIL_TIMEOUT = None
'''
If using gmail, you will need to
unlock Captcha to enable Django
to  send for you:
https://accounts.google.com/displayunlockcaptcha
'''


INSTALLED_APPS += (
    'storages',
)


# D A T A B A S E
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'oby_db_initial',
        'USER': 'obystudio',
        'PASSWORD': '84e52ccc-de80-4bc1-ae4c-5dd0934d42a6',
        'HOST': 'oby-dbs-virginia.cmyml5gujc5c.us-east-1.rds.amazonaws.com',
        'PORT': '5432',
        # 'ATOMIC_REQUESTS': True,
    },
    'extra': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# T E M P L A T E S
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join('templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# C A C H E
CACHES = {
    'default': {
        'BACKEND': 'oby.memcached.ElastiCache',
        'LOCATION': [
            'oby-memcached.il3181.cfg.use1.cache.amazonaws.com:11211',
        ],
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 12
CACHE_MIDDLEWARE_KEY_PREFIX = ''


# S 3  B U C K E T
STATICFILES_DIRS = (
    os.path.join('oby', 'static', 'static_dirs'),
    # '/Users/jphalis/Desktop/oby/src/oby/static/static_dirs/'
)

AWS_ACCESS_KEY_ID = 'AKIAJS5O4GAHA4MJH4NA'
AWS_SECRET_ACCESS_KEY = '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'

AWS_STORAGE_BUCKET_NAME = 'oby'
# With cloudfront
AWS_CLOUDFRONT_DOMAIN = 'd2ragyhmhrkfg3.cloudfront.net'

STATICFILES_STORAGE = 'oby.s3utils.StaticRootS3BotoStorage'  # static files
STATIC_S3_PATH = 'media/'
DEFAULT_FILE_STORAGE = 'oby.s3utils.MediaRootS3BotoStorage'  # media uploads
DEFAULT_S3_PATH = 'static/'

S3_URL = '//{}.s3.amazonaws.com/'.format(AWS_STORAGE_BUCKET_NAME)
# Without cloudfront
# MEDIA_URL = S3_URL + STATIC_S3_PATH
# STATIC_URL = S3_URL + DEFAULT_S3_PATH
MEDIA_ROOT = '/home/ubuntu/obystudio.com/oby/static/media'
STATIC_ROOT = '/home/ubuntu/obystudio.com/oby/static/static'
# With cloudfront
MEDIA_URL = '//{}/{}'.format(AWS_CLOUDFRONT_DOMAIN, STATIC_S3_PATH)
STATIC_URL = '//{}/{}'.format(AWS_CLOUDFRONT_DOMAIN, DEFAULT_S3_PATH)
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

AWS_PRELOAD_METADATA = False
date_two_months_later = datetime.date.today() + datetime.timedelta(2 * 365 / 12)
expires = date_two_months_later.strftime('%A, %d %B %Y 20:00:00 EST')
AWS_HEADERS = {
    'Expires': expires,
    'Cache-Control': 'max-age=86400',
}


# L O G G I N G
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'oby.settings.handlers.ThrottledAdminEmailHandler'
        }
    },
    'loggers': {
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        },
    },
}
