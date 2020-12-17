from os import environ

# Environment variables

# FMP credentials
FMP_URL = environ['FMP_URL']
FMP_USERNAME = environ['FMP_USERNAME']
FMP_PASSWORD = environ['FMP_PASSWORD']

# FMP databases
FMP_VFX_DB = environ['FMP_VFX_DB']
FMP_ADMIN_DB = environ['FMP_ADMIN_DB']
FMP_EDIT_DB = environ['FMP_EDIT_DB']
FMP_IMAGE_DB = environ['FMP_IMAGE_DB']

# FMP layouts
FMP_VERSIONS_LAYOUT = environ['FMP_VERSIONS_LAYOUT']
FMP_TRANSFER_DATA_LAYOUT = environ['FMP_TRANSFER_DATA_LAYOUT']
FMP_TRANSFER_LOG_LAYOUT = environ['FMP_TRANSFER_LOG_LAYOUT']
FMP_SCANS_LAYOUT = environ['FMP_SCANS_LAYOUT']
FMP_CUTHISTORY_LAYOUT = environ['FMP_CUTHISTORY_LAYOUT']
FMP_CUTHISTORYSHOTS_LAYOUT = environ['FMP_CUTHISTORYSHOTS_LAYOUT']
FMP_IMAGES_LAYOUT = environ['FMP_IMAGES_LAYOUT']

# FMP scripts
FMP_PROCESS_IMAGE_SCRIPT = environ['FMP_PROCESS_IMAGE_SCRIPT']

# Filesystem path constants
SHOT_TREE_BASE_PATH = environ['SHOT_TREE_BASE_PATH']
THUMBS_BASE_PATH = environ['THUMBS_BASE_PATH']
CONFIG_PATH = './config.yml'
SG_EVENTS_CONFIG_PATH = '/mnt/Plugins/python3.6/config/shotgun_events_config.yml'

# Email credentials
EMAIL_USERNAME = environ['EMAIL_USERNAME']
EMAIL_PASSWORD = environ['EMAIL_PASSWORD']

# Shotgun credentials
SG_INJECT_IH_NAME = environ['SG_INJECT_IH_NAME']
SG_INJECT_IH_KEY = environ['SG_INJECT_IH_KEY']
SG_INJECT_EXT_NAME = environ['SG_INJECT_EXT_NAME']
SG_INJECT_EXT_KEY = environ['SG_INJECT_EXT_KEY']
SG_EVENTS_NAME = environ['SG_EVENTS_NAME']
SG_EVENTS_KEY = environ['SG_EVENTS_KEY']

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
