import sys
import subprocess

from ..filesystem import Chunker
from . import new_package


# Chunk out files in the provided paths to roughly equal sized new vendor delivery packages
def main(dest_dir, paths):

    # The target size for each new package (will get as close as possible without breaking up subfolders)
    chunk_size = 16106127360  # 15 GB

    # Split into relatively constant volume bins (list of lists)
    chunker = Chunker()
    chunks = chunker.chunk(paths, chunk_size=chunk_size)

    # Create a new package for each chunk and copy the files.
    for chunk in chunks:
        if chunk:
            new_package_path = new_package.main(dest_dir)
            print(f'Copying chunk: {chunk}')
            for item in chunk:
                cmd = ['cp', '-r', item, new_package_path]
                result = subprocess.run(cmd,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        universal_newlines=True,
                                        shell=False)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
