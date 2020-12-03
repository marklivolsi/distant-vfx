# import time
#
# from ..filemaker import FMCloudInstance
#
# # TODO: Get from env variable
# SCRIPT_NAME = ''
# SCRIPT_KEY = ''
#
#
# def registerCallbacks(reg):
#     matchEvents = {
#         'Shotgun_Version_Change': ['*'],
#     }
#     reg.registerCallback(SCRIPT_NAME,
#                          SCRIPT_KEY,
#                          inject_vendor_versions_to_filemaker,
#                          matchEvents,
#                          None)
#
#
# def inject_vendor_versions_to_filemaker(sg, logger, event, args):
#
#     # Wait for entity to be fully created
#     time.sleep(1)
#
#     # Get entity data
#     entity_id = event.get('meta').get('entity_id')
#     entity_type = event.get('meta').get('entity_type')
#
#     match_phrase = 'to "{status}" on Version'  # TODO: Change status to something for MrX only
#
#
