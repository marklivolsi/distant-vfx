#!/usr/bin/env python

import os
import sys

from distant_vfx import EDLHandler


def main():
    # Get path to either directory or file.
    path = sys.argv[1]

    # If path is a file and is an edl, rewrite all *LOC lines to lowercase.
    if os.path.isfile(path):
        if os.path.splitext(path)[1] == '.edl':
            handler = EDLHandler()
            handler.loc_to_lower(path)

    # If path is a directory, scan for edls and rewrite *LOC lines to lowercase for each.
    elif os.path.isdir(path):

        # If running Python 3.5+, os.scandir can be used.
        if sys.version_info[0] == 3 and sys.version_info[1] >= 5:
            edls = [item.path for item in os.scandir(path) if item.is_file() and os.path.splitext(item.path)[1] == '.edl']

        # For earlier Python installations, use os.listdir
        else:
            edls = []
            for item in os.listdir(path):
                filepath = os.path.join(path, item)
                extension = os.path.splitext(item)[1]
                if os.path.isfile(filepath) and extension == '.edl':
                    edls.append(filepath)

        # Rewrite each edl with lowercase *LOC lines.
        for edl in edls:
            handler = EDLHandler()
            handler.loc_to_lower(edl)


if __name__ == '__main__':
    main()
