import subprocess


class VideoProcessor:

    def __init__(self):
        pass

    @staticmethod
    def generate_thumbnail(src, dest, num_thumbs=1):
        cmd = ['ffmpeg', '-i', src, '-vf', 'thumbnail', '-frames:v', num_thumbs, dest]
        process = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                universal_newlines=True,
                                shell=False)
        stdout, stderr = process.communicate()
        return stdout
