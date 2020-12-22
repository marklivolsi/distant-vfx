from distant_vfx.jobs.fmp_injectors import SgEventsInHouseInjector
from distant_vfx.constants import SG_INJECT_IH_NAME, SG_INJECT_IH_KEY


def registerCallbacks(reg):
    matchEvents = {
        'Shotgun_Version_Change': ['*'],  # look for any version change event
    }
    reg.registerCallback(SG_INJECT_IH_NAME,
                         SG_INJECT_IH_KEY,
                         inject,
                         matchEvents,
                         None)


def inject(sg, logger, event, args):
    injector = SgEventsInHouseInjector(sg, logger, event, args)
    injector.inject()
