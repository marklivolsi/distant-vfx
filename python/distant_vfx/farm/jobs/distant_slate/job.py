import os

from arch.farm.jobs import nuke_quicktime_render


class DistantSlateFarmJob(nuke_quicktime_render.NukeQuickTimeRenderFarmJob):
    SLATE_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "slate.png")

    def __init__(
        self,
        slate_image=None,
        slate_left_text="",
        slate_right_text="",
        slate_bottom_text="",
        **kwargs
    ):
        if "nukescript_path" not in kwargs:
            kwargs["nukescript_path"] = self.NUKESCRIPT_PATH

        super(DistantSlateFarmJob, self).__init__(**kwargs)

        if slate_image is None:
            self.slate_image = self.SLATE_IMAGE_PATH
        else:
            if not os.path.exists(slate_image):
                raise ValueError(
                    "Path to nukescript does not exist: {}".format(slate_image)
                )
            self.slate_image = slate_image

        if slate_left_text and slate_left_text[0].isdigit():
            # Can't start with a digit otherwise Nuke thinks it is a frame range
            slate_left_text = " " + slate_left_text
        if slate_right_text and slate_right_text[0].isdigit():
            # Can't start with a digit otherwise Nuke thinks it is a frame range
            slate_right_text = " " + slate_right_text
        if slate_bottom_text and slate_bottom_text[0].isdigit():
            # Can't start with a digit otherwise Nuke thinks it is a frame range
            slate_bottom_text = " " + slate_bottom_text

        self.slate_left_text = slate_left_text
        self.slate_right_text = slate_right_text
        self.slate_bottom_text = slate_bottom_text

    @classmethod
    def help(cls):
        message = super(DistantSlateFarmJob, cls).help()

        return (
            message
            + """
  DistantSlateFarmJob
==============================
A DistantSlateFarmJob subclasses a NukeQuickTimeFarmJob with specific settings for Distant VFX.
It adds a custom slate

:param str|None slate_image: Path to the slate image we want to use.
:param str|None slate_left_text: Text for the top left side of the slate.
:param str|None slate_right_text: Text for the bottom right side of the slate.
:param str|None slate_bottom_text: Text for the bottom right of the slate.

"""
        )

    def nuke_arguments(self):
        args = super(DistantSlateFarmJob, self).nuke_arguments()
        args.append(self.slate_image)
        args.append(self.slate_left_text)
        args.append(self.slate_right_text)
        args.append(self.slate_bottom_text)
        return args
