#!/usr/bin/env python3

import logging.config
import sys

from . import edl_lowercase_loc
from ..filemaker import FMCloudInstance

# Configure logging.
from ..constants import LOG_SETTINGS
logging.config.dictConfig(LOG_SETTINGS)
LOG = logging.getLogger(__name__)


def main(edl_path):

    # First make sure the edl loc lines are converted to lowercase
    edl_lowercase_loc.main(edl_path)

    # TODO: Parse EDL
    # TODO: Connect to FileMaker and inject scan data


if __name__ == '__main__':
    main(edl_path=sys.argv[1])
