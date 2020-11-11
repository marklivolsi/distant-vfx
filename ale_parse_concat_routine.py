#!/usr/bin/env python3

import os
import sys
import pandas as pd
from datetime import datetime

from distant_vfx import ALEHandler


def main():
    # Set the path of the output .xlsx file to the desktop.
    desktop = os.path.normpath(os.path.expanduser("~/Desktop"))
    output_name = datetime.now().strftime('%y%m%d_%H%M%S_ALE_PARSE') + '.xlsx'
    output_path = os.path.join(desktop, output_name)

    # Pass in the path to either a single ALE file or directory containing multiple ALE files.
    path = sys.argv[1]

    # Define allowable file extensions for ale files.
    ale_ext = ['.ale', '.txt']

    # If a single ALE file, parse that file and export a .xlsx doc.
    if os.path.isfile(path) and os.path.splitext(path)[1] in ale_ext:
        parser = ALEHandler(path)
        parser.parse_ale()
        parser.column_data.to_excel(output_path, index=False)

    # If a directory, scan for any ALE files (.ale or .txt file extension).
    elif os.path.isdir(path):
        file_paths = [f.path for f in os.scandir(path) if f.is_file() and os.path.splitext(f.path)[1] in ale_ext]

        # Parse data from each found ALE file.
        parsers = []
        for path in file_paths:
            parser = ALEHandler(path)
            parser.parse_ale()
            parsers.append(parser)

        # Concatenate the dataframes and export a .xlsx doc.
        data_frames = []
        for parser in parsers:
            data_frames.append(parser.column_data)
        result = pd.concat(data_frames)
        result.to_excel(output_path, index=False)


if __name__ == '__main__':
    main()
