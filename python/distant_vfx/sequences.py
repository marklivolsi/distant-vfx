

class ImageSequence:

    def __init__(self, frames):
        self.frames = frames
        self._split = frames[0].split('.')
        self._sorted = False

    def __repr__(self):
        return self.name

    @property
    def name(self):
        # frame_len = len(self._split[-2])
        return self.basename + '.[' + str(self.start) + '-' + str(self.end) + '].' + self.extension

    @property
    def basename(self):
        return self._split[0]

    @property
    def extension(self):
        return self._split[-1]

    @property
    def start(self):
        if not self._sorted:
            self._sort_frames()
        return self.frames[0]

    @property
    def end(self):
        if not self._sorted:
            self._sort_frames()
        return self.frames[-1]

    def _sort_frames(self):
        self.frames.sort(key=lambda x: int(x.split('.')[-2]))
        self._sorted = True
