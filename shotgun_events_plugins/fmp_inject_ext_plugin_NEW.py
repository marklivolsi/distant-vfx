from distant_vfx.jobs.fmp_injectors import SgEventsExtVendorInjector
from distant_vfx.constants import SG_INJECT_EXT_NAME, SG_INJECT_EXT_KEY


def registerCallbacks(reg):
    matchEvents = {
        'Shotgun_PublishedFile_Change': ['*'],  # look for any published file change event
    }
    reg.registerCallback(SG_INJECT_EXT_NAME,
                         SG_INJECT_EXT_KEY,
                         inject,
                         matchEvents,
                         None)


def inject(sg, logger, event, args):
    injector = SgEventsExtVendorInjector(sg, logger, event, args)
    injector.inject()
