import os

from distant_quicktime.farm.jobs import distant_colour


class DistantH264FarmJob(distant_colour.DistantColourQuicktimeFarmJob):
    NUKESCRIPT_PATH = os.path.join(os.path.dirname(__file__), "template.nk")

    @classmethod
    def help(cls):
        message = super(DistantH264FarmJob, cls).help()

        return (
            message
            + """
  DistantH264FarmJob
==============================
A DistantH264FarmJob subclasses a DistantColourQuicktimeFarmJob with specific settings for H264

:param str|None slate_image: Path to the slate image we want to use.
:param str|None slate_left_text: Text for the top left side of the slate.
:param str|None slate_right_text: Text for the bottom right side of the slate.
:param str|None slate_bottom_text: Text for the bottom right of the slate.

"""
        )
