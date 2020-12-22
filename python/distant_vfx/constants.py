from os import environ

LEGAL_THUMB_SRC_EXTENSIONS = ['.mov', '.mp4', '.jpg']
FRAME_RANGE_EXTS_NO_DOT = ['exr', 'png', 'jpg', 'jpeg']

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

# FMP scripts
FMP_PROCESS_IMAGE_SCRIPT = environ.get('FMP_PROCESS_IMAGE_SCRIPT')

# Filesystem path constants
SHOT_TREE_BASE_PATH = environ.get('SHOT_TREE_BASE_PATH')
THUMBS_BASE_PATH = environ.get('THUMBS_BASE_PATH')
RV_PATH = environ.get('RV_PATH')
CONFIG_PATH = './config.yml'
SG_EVENTS_CONFIG_PATH = '/mnt/Plugins/python3.6/config/shotgun_events_config.yml'
TO_EDT_MAILBOX_PATH = '/mnt/Projects/dst/mailbox/edt/to_edt'

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
