import time

from ..filemaker import FMCloudInstance

# TODO: Get from env variable
SCRIPT_NAME = ''
SCRIPT_KEY = ''


def registerCallbacks(reg):
    matchEvents = {
        'Shotgun_Version_New': ['*'],
    }
    reg.registerCallback(SCRIPT_NAME,
                         SCRIPT_KEY,
                         inject_new_versions_to_filemaker,
                         matchEvents,
                         None)


def inject_new_versions_to_filemaker(sg, logger, event, args):

    # Wait for entity to be fully created
    time.sleep(1)

