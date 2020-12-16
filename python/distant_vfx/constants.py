from os import environ

# Environment variables

# FMP credentials
FMP_URL = environ['FMP_URL']
FMP_USERNAME = environ['FMP_USERNAME']
FMP_PASSWORD = environ['FMP_PASSWORD']

# FMP databases
FMP_ADMIN_DB = environ['FMP_ADMIN_DB']
FMP_EDIT_DB = environ['FMP_EDIT_DB']

# FMP layouts
FMP_TRANSFER_DATA_LAYOUT = environ['FMP_TRANSFER_DATA_LAYOUT']
FMP_SCANS_LAYOUT = environ['FMP_SCANS_LAYOUT']
FMP_CUTHISTORY_LAYOUT = environ['FMP_CUTHISTORY_LAYOUT']
FMP_CUTHISTORYSHOTS_LAYOUT = environ['FMP_CUTHISTORYSHOTS_LAYOUT']

# Filesystem path constants
SHOT_TREE_BASE_PATH = environ['SHOT_TREE_BASE_PATH']
CONFIG_PATH = './config.yml'

# Template constants
TC_PATTERN = r'\d{2}:\d{2}:\d{2}:\d{2}'

# Media-related constants
FPS = 24

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
