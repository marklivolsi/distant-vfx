import sys
from python.distant_vfx.filesystem import Chunker
import subprocess
from . import new_package


def main(dest_dir, *paths):
    chunk_size = 104857600
    chunker = Chunker()
    chunks = chunker.chunk(*paths, chunk_size=chunk_size)

    for chunk in chunks:
        print(chunk)
        new_package_path = new_package.main(dest_dir)
        print(new_package_path)
        for item in chunk:
            cmd = ['cp', '-r', item, new_package_path]
            subprocess.call(cmd, shell=False)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
