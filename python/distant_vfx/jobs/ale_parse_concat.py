#!/usr/bin/env python

import logging.config
import os
import sys
import pandas as pd
from datetime import datetime

from ..parsers import ALEParser

# Configure logging.
from ..constants import LOG_SETTINGS
logging.config.dictConfig(LOG_SETTINGS)
LOG = logging.getLogger(__name__)


def scandir(path):
    for root, dirs, files in os.walk(path):
        for file_ in files:
            yield file_


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
        handler = ALEParser()
        handler.parse_ale(path)
        handler.column_data.to_excel(output_path, index=False)

    # If a directory, scan for any ALE files (.ale or .txt file extension).
    elif os.path.isdir(path):
        file_paths = [f for f in scandir(path) if os.path.isfile(f) and os.path.splitext(f)[1] in ale_ext]

        # Parse data from each found ALE file.
        handlers = []
        for path in file_paths:
            handler = ALEParser()
            handler.parse_ale(path)
            handlers.append(handler)

        # Concatenate the dataframes and export a .xlsx doc.
        data_frames = []
        for handler in handlers:
            data_frames.append(handler.column_data)
        result = pd.concat(data_frames)
        result.to_excel(output_path, index=False)


if __name__ == '__main__':
    main()
