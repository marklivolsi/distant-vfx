#!/bin/env python3

import argparse
import time
import yaml

from python.distant_vfx.jobs import aspera_auto_download_new
from python.distant_vfx.constants import ASPERA_YML_PATH


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--catch-up',
        action='store_true',
        help='Optionally specify "catch-up" mode, which updates the latest package ID without downloading '
             'any packages.'
    )

    args = parser.parse_args()

    with open(ASPERA_YML_PATH, 'r') as file:
        faspex_data = yaml.safe_load(file)

    while True:
        for host, data in faspex_data.items():
            aspera_auto_download_new.main(
                host=host,
                data=data,
                catch_up_mode=args.catch_up
            )
        print('Package scan complete. Job will restart in 5 min.')
        if args.catch_up:
            break
        else:
            time.sleep(300)


if __name__ == '__main__':
    main()
