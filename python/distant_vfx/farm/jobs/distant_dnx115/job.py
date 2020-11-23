import os

from distant_vfx.farm.jobs import distant_slate


class DistantDNxHDFarmJob(distant_slate.DistantSlateFarmJob):
    NUKESCRIPT_PATH = os.path.join(os.path.dirname(__file__), "template.nk")

    @classmethod
    def help(cls):
        message = super(DistantDNxHDFarmJob, cls).help()

        return (
            message
            + """
  DistantDNxHDFarmJob
==============================
A DistantDNxHDFarmJob subclasses a DistantSlateFarmJob with specific settings for DNxHD115

:param str|None slate_image: Path to the slate image we want to use.
:param str|None slate_left_text: Text for the top left side of the slate.
:param str|None slate_right_text: Text for the bottom right side of the slate.
:param str|None slate_bottom_text: Text for the bottom right of the slate.

"""
        )
