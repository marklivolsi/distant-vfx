from os import environ

LEGAL_FRAME_EXTENSIONS = ['.exr', '.png', '.jpg', '.jpeg']
LEGAL_THUMB_EXTENSIONS = ['.jpg', '.jpeg', '.png']
LEGAL_THUMB_SRC_EXTENSIONS = ['.mov', '.mp4']
SHOW_CODE = 'dst'
PACKAGE_REGEX = r'[A-Za-z]{2,3}_[A-Za-z]{2,3}_\d{6,8}(_[A-Za-z]{1,2})?'

# Environment variables

# FMP credentials
FMP_URL = environ.get('FMP_URL')
FMP_USERNAME = environ.get('FMP_USERNAME')
FMP_PASSWORD = environ.get('FMP_PASSWORD')

# FMP databases
FMP_VFX_DB = environ.get('FMP_VFX_DB')
FMP_ADMIN_DB = environ.get('FMP_ADMIN_DB')
FMP_EDIT_DB = environ.get('FMP_EDIT_DB')
FMP_IMAGE_DB = environ.get('FMP_IMAGE_DB')

# FMP layouts
FMP_VERSIONS_LAYOUT = environ.get('FMP_VERSIONS_LAYOUT')
FMP_TRANSFER_DATA_LAYOUT = environ.get('FMP_TRANSFER_DATA_LAYOUT')
FMP_TRANSFER_LOG_LAYOUT = environ.get('FMP_TRANSFER_LOG_LAYOUT')
FMP_SCANS_LAYOUT = environ.get('FMP_SCANS_LAYOUT')
FMP_CUTHISTORY_LAYOUT = environ.get('FMP_CUTHISTORY_LAYOUT')
FMP_CUTHISTORYSHOTS_LAYOUT = environ.get('FMP_CUTHISTORYSHOTS_LAYOUT')
FMP_IMAGES_LAYOUT = environ.get('FMP_IMAGES_LAYOUT')
FMP_NOTES_LAYOUT = environ.get('FMP_NOTES_LAYOUT')

# FMP scripts
FMP_PROCESS_IMAGE_SCRIPT = environ.get('FMP_PROCESS_IMAGE_SCRIPT')
FMP_PROCESS_TRANSFER_DATA_SCRIPT = environ.get('FMP_PROCESS_TRANSFER_DATA_SCRIPT')
FMP_UNFLAG_OMITS_SCRIPT = environ.get('FMP_UNFLAG_OMITS_SCRIPT')

# Filesystem path constants
SHOT_TREE_BASE_PATH = environ.get('SHOT_TREE_BASE_PATH')
THUMBS_BASE_PATH = environ.get('THUMBS_BASE_PATH')
RV_PATH = environ.get('RV_PATH')
TO_EDT_MAILBOX_PATH = environ.get('TO_EDT_MAILBOX_PATH')
MAILBOX_BASE_PATH = environ.get('MAILBOX_BASE_PATH')

# Email credentials
EMAIL_USERNAME = environ.get('EMAIL_USERNAME')
EMAIL_PASSWORD = environ.get('EMAIL_PASSWORD')
EMAIL_RECIPIENTS = environ.get('EMAIL_RECIPIENTS')

# Shotgun credentials
SG_INJECT_IH_NAME = environ.get('SG_INJECT_IH_NAME')
SG_INJECT_IH_KEY = environ.get('SG_INJECT_IH_KEY')
SG_INJECT_EXT_NAME = environ.get('SG_INJECT_EXT_NAME')
SG_INJECT_EXT_KEY = environ.get('SG_INJECT_EXT_KEY')
SG_EVENTS_NAME = environ.get('SG_EVENTS_NAME')
SG_EVENTS_KEY = environ.get('SG_EVENTS_KEY')

# Faspex credentials
FASPEX_BASE_URL = environ.get('FASPEX_BASE_URL')
FASPEX_USERNAME = environ.get('FASPEX_USERNAME')
FASPEX_PASSWORD = environ.get('FASPEX_PASSWORD')
FASPEX_RECIPIENTS = environ.get('FASPEX_RECIPIENTS')  # todo: add this
FASPEX_SUPE_USERNAME = environ.get('FASPEX_SUPE_USERNAME')
INTERNAL_FASPEX_BASE_URL = environ.get('INTERNAL_FASPEX_BASE_URL')
INTERNAL_FASPEX_USERNAME = environ.get('INTERNAL_FASPEX_USERNAME')
INTERNAL_FASPEX_PASSWORD = environ.get('INTERNAL_FASPEX_PASSWORD')
INTERNAL_FASPEX_RECIPIENTS = environ.get('INTERNAL_FASPEX_RECIPIENTS')  # todo: add this
INTERNAL_FASPEX_SUPE_USERNAME = environ.get('INTERNAL_FASPEX_SUPE_USERNAME')
INTERNAL_FASPEX_CONTENT_PROTECT_PASSWORD = environ.get('INTERNAL_FASPEX_CONTENT_PROTECT_PASSWORD')  # todo: add this
DEFAULT_DOWNLOAD_PATH = environ.get('DEFAULT_DOWNLOAD_PATH')
LAST_PROCESSED_PACKAGE_JSON_FILE_INTERNAL_ASPERA = environ.get('LAST_PROCESSED_PACKAGE_JSON_FILE_INTERNAL_ASPERA')
LAST_PROCESSED_PACKAGE_JSON_FILE_EXTERNAL_ASPERA = environ.get('LAST_PROCESSED_PACKAGE_JSON_FILE_EXTERNAL_ASPERA')

# Faspex email recipients
MRX_EMAIL_RECIPIENTS = environ.get('MRX_EMAIL_RECIPIENTS')
EDT_EMAIL_RECIPIENTS = environ.get('EDT_EMAIL_RECIPIENTS')
SUP_EMAIL_RECIPIENTS = environ.get('SUP_EMAIL_RECIPIENTS')


ASPERA_VENDOR_MAP = {
    'mrx': {
        'user': FASPEX_USERNAME,
        'password': FASPEX_PASSWORD,
        'url': FASPEX_BASE_URL,
        'package_id_json_file': LAST_PROCESSED_PACKAGE_JSON_FILE_EXTERNAL_ASPERA,
        'url_prefix': 'aspera/faspex',
        'recipients': FASPEX_RECIPIENTS,
        'email_recipients': MRX_EMAIL_RECIPIENTS,
        'cc_on_upload': FASPEX_USERNAME,
        'cc_on_download': FASPEX_USERNAME
    },
    'edt': {
        'user': INTERNAL_FASPEX_USERNAME,
        'password': INTERNAL_FASPEX_PASSWORD,
        'url': INTERNAL_FASPEX_BASE_URL,
        'package_id_json_file': LAST_PROCESSED_PACKAGE_JSON_FILE_INTERNAL_ASPERA,
        'url_prefix': 'faspex',
        'recipients': INTERNAL_FASPEX_RECIPIENTS,
        'content_protect_password': INTERNAL_FASPEX_CONTENT_PROTECT_PASSWORD,
        'email_recipients': EDT_EMAIL_RECIPIENTS,
        'cc_on_upload': INTERNAL_FASPEX_USERNAME,
        'cc_on_download': INTERNAL_FASPEX_USERNAME
    },
    'ldq': {
        'user': FASPEX_USERNAME,
        'password': FASPEX_PASSWORD,
        'url': FASPEX_BASE_URL,
        'package_id_json_file': LAST_PROCESSED_PACKAGE_JSON_FILE_EXTERNAL_ASPERA,
        'url_prefix': 'aspera/faspex',
        'recipients': FASPEX_SUPE_USERNAME,
        'email_recipients': SUP_EMAIL_RECIPIENTS,
        'cc_on_upload': FASPEX_USERNAME,
        'cc_on_download': FASPEX_USERNAME
    },
    'tst': {
        'user': INTERNAL_FASPEX_USERNAME,
        'password': INTERNAL_FASPEX_PASSWORD,
        'url': INTERNAL_FASPEX_BASE_URL,
        'package_id_json_file': LAST_PROCESSED_PACKAGE_JSON_FILE_INTERNAL_ASPERA,
        'url_prefix': 'faspex',
        'recipients': 'mlivolsi',
        'content_protect_password': INTERNAL_FASPEX_CONTENT_PROTECT_PASSWORD,
        'email_recipients': 'mark.c.livolsi@gmail.com',
        'cc_on_upload': INTERNAL_FASPEX_USERNAME,
        'cc_on_download': INTERNAL_FASPEX_USERNAME
    }
}


# Faspex API pathways
FASPEX_API_PATHS = {
    'auth': '/auth/oauth2/token',
    'users': '/api/users/{user_id}',
    'packages': '/api/users/{user_id}/packages',
    'workgroups': '/api/workgroups',
    'transfer_specs': '/api/users/{user_id}/packages/{package_id}/transfer_specs'
}


# Logging configuration.
LOG_SETTINGS = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s :: %(levelname)s :: %(name)s :: %(filename)s, line %(lineno)s :: %(funcName)s :: '
                      '%(message)s'
        },
    },
    'handlers': {
        'default': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': 'log/debug.log',
            'encoding': 'utf-8',
            'interval': 1,
            'when': 'midnight',
            'backupCount': 5
        },
        'info': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': 'log/info.log',
            'encoding': 'utf-8',
            'interval': 1,
            'when': 'midnight',
            'backupCount': 5
        },
        'session': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': 'log/session.log',
            'mode': 'w',
            'encoding': 'utf-8',
        }
    },
    'loggers': {
        '': {
            'handlers': ['default', 'info', 'session'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}
