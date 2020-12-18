import os

from distant_quicktime.farm.jobs import distant_slate


class DistantColourQuicktimeFarmJob(distant_slate.DistantSlateFarmJob):
    NUKESCRIPT_PATH = os.path.join(os.path.dirname(__file__), "template.nk")
    DEFAULT_LUT = os.path.join(os.path.dirname(__file__), "noop.cube")

    def __init__(
        self,
        show_lut=None,
        shot_lut=None,
        **kwargs
    ):
        if "nukescript_path" not in kwargs:
            kwargs["nukescript_path"] = self.NUKESCRIPT_PATH

        super(DistantColourQuicktimeFarmJob, self).__init__(**kwargs)

        self.show_lut = show_lut
        self.shot_lut = shot_lut

        if self.shot_lut is None:
            from distant_quicktime.colour import get_shot_lut_from_path
            self.shot_lut = get_shot_lut_from_path(self.image_sequence) or self.DEFAULT_LUT
        if self.show_lut is None:
            from distant_quicktime.colour import get_show_lut_from_path
            self.show_lut = get_show_lut_from_path(self.image_sequence) or self.DEFAULT_LUT

    @classmethod
    def help(cls):
        message = super(DistantColourQuicktimeFarmJob, cls).help()

        return (
            message
            + """
  DistantColourQuicktimeFarmJob
==============================
A DistantColourQuicktimeFarmJob subclasses a NukeQuickTimeFarmJob with specific settings for Distant VFX.
It adds show_lut path and shot_lut path

:param str|None show_lut: Path to the ShowLUT that we want to use.
:param str|None shot_lut: Path to the ShotLUT that we want to use.

"""
        )

    def nuke_arguments(self):
        args = super(DistantColourQuicktimeFarmJob, self).nuke_arguments()
        args.append(self.show_lut)
        args.append(self.shot_lut)
        return args
