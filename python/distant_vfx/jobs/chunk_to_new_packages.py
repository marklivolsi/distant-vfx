import sys
import subprocess

from ..filesystem import Chunker
from . import new_package


# Chunk out files in the provided paths to roughly equal sized new vendor delivery packages
def main(dest_dir, paths, should_move=False):

    # The target size for each new package (will get as close as possible without breaking up subfolders)
    chunk_size = 16106127360  # 15 GB
    print('Target chunk size is {} bytes.'.format(chunk_size))

    # Split into relatively constant volume bins (list of lists)
    chunker = Chunker()
    chunks = chunker.chunk(paths, chunk_size=chunk_size)

    # Create a new package for each chunk and copy the files.
    for index, chunk in enumerate(chunks):
        if chunk:
            new_package_path = new_package.main(dest_dir)
            print('Copying chunk {} of {} to path {} (chunk {})'.format(index + 1, len(chunks), new_package_path, chunk))
            for item in chunk:
                if not should_move:
                    cmd = ['cp', '-r', item, new_package_path]
                else:
                    cmd = ['mv', item, new_package_path]
                process = subprocess.Popen(cmd,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        universal_newlines=True,
                                        shell=False)
                _, _ = process.communicate()
